"""Self-update from the project's own GitHub releases (specs/008-auto-atualizacao).

Ported from the previous plugin (decky-system-monitor, its spec 009); REQ ids are kept identical.
"""
import hashlib
import io
import json
import os
import re
import shutil
import ssl
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from typing import Any, Callable, Dict, Optional, Tuple

REPO = "paulorband/decky-system-monitor-v2"
TEST_TAG = "test-build"
# REQ-660: one request covers both the latest stable release and the rolling test build.
API_RELEASES = f"https://api.github.com/repos/{REPO}/releases?per_page=15"
DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"
ASSET_NAME = "steam-system-monitor.zip"
ZIP_ROOT = "steam-system-monitor"
PLUGIN_NAME = "System Monitor"
PAYLOAD = ("plugin.json", "package.json", "main.py", "LICENSE", "README.md", "build.json", "dist", "py_modules")
MAX_ZIP = 10 * 1024 * 1024
MAX_UNPACKED = 30 * 1024 * 1024
TIMEOUT = 10
CACHE_SECONDS = 6 * 3600

_SHA = re.compile(r"^[0-9a-f]{40}$")
_BODY_COMMIT = re.compile(r"^commit:\s*([0-9a-f]{40})\s*$", re.M)
_BODY_VERSION = re.compile(r"^version:\s*(\S+)\s*$", re.M)
_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


class UpdateError(Exception):
    pass


class RateLimited(UpdateError):
    """REQ-662: GitHub's unauthenticated API quota is used up."""

    def __init__(self, minutes: int):
        super().__init__(f"GitHub rate limit; retry in ~{minutes} min")
        self.minutes = minutes


# --- versions (REQ-601) ---
def parse_version(s: Any) -> Optional[Tuple[int, int, int, Optional[str]]]:
    m = _SEMVER.match(s.strip()) if isinstance(s, str) else None
    return (int(m[1]), int(m[2]), int(m[3]), m[4]) if m else None


def is_newer(latest: str, current: str) -> bool:
    a, b = parse_version(latest), parse_version(current)
    if not a or not b:
        return False
    if a[:3] != b[:3]:
        return a[:3] > b[:3]
    return a[3] is None and b[3] is not None  # 1.0.0 supersedes 1.0.0-rc1


def read_version(plugin_dir: str) -> str:
    try:
        with open(os.path.join(plugin_dir, "package.json")) as f:
            v = json.load(f).get("version")
        return v if parse_version(v) else "0.0.0"
    except (OSError, ValueError, AttributeError):
        return "0.0.0"


def is_older(a: str, b: str) -> bool:
    pa, pb = parse_version(a), parse_version(b)
    return bool(pa and pb and pa[:3] < pb[:3])


def read_build(plugin_dir: str) -> Dict[str, Any]:
    """REQ-652/663: build.json written by the CI (kind added by install()); absent in old installs."""
    try:
        with open(os.path.join(plugin_dir, "build.json")) as f:
            d = json.load(f)
        c = d.get("commit")
        k = d.get("kind")
        return {"version": d.get("version"), "commit": c if isinstance(c, str) and _SHA.match(c) else None,
                "kind": k if k in ("stable", "test") else None}
    except (OSError, ValueError, AttributeError):
        return {"version": None, "commit": None, "kind": None}


def build_info(plugin_dir: str) -> Dict[str, Any]:
    b = read_build(plugin_dir)
    return {"current_commit": b["commit"][:7] if b["commit"] else None, "current_kind": b["kind"]}


def _stamp_kind(plugin_dir: str, kind: str) -> None:
    """REQ-663: remember where the installed build came from."""
    path = os.path.join(plugin_dir, "build.json")
    try:
        with open(path) as f:
            d = json.load(f)
        if not isinstance(d, dict):
            d = {}
    except (OSError, ValueError):
        d = {}
    d["kind"] = kind
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f)
    os.replace(tmp, path)


# --- network ---
CA_BUNDLES = (
    "/etc/ssl/certs/ca-certificates.crt",  # Debian/Arch/SteamOS
    "/etc/pki/tls/certs/ca-bundle.crt",  # Fedora/Bazzite
    "/etc/ssl/ca-bundle.pem",
)


def _contexts():
    """Default first (honours SSL_CERT_FILE and the system store), then certifi/known bundles."""
    yield ssl.create_default_context()
    candidates = []
    try:
        import certifi  # type: ignore
        candidates.append(certifi.where())
    except Exception:
        pass
    candidates.extend(CA_BUNDLES)
    for cafile in candidates:
        if cafile and os.path.isfile(cafile):
            try:
                yield ssl.create_default_context(cafile=cafile)
            except (ssl.SSLError, OSError):
                continue


def _open(url: str, urlopen: Callable, accept: str, headers: Optional[Dict[str, str]] = None):
    """Retry with alternative CA bundles only on certificate errors."""
    req = urllib.request.Request(
        url, headers={"Accept": accept, "User-Agent": "steam-system-monitor-updater", **(headers or {})})
    last: Optional[Exception] = None
    for ctx in _contexts():
        try:
            return urlopen(req, timeout=TIMEOUT, context=ctx)
        except urllib.error.URLError as e:
            if not isinstance(getattr(e, "reason", None), ssl.SSLError):
                raise
            last = e
    raise last  # type: ignore[misc]


class HttpCache:
    """REQ-661: ETag cache persisted on disk. A 304 reply does not count against GitHub's rate limit."""

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.data: Dict[str, Any] = {}
        if path:
            try:
                with open(path) as f:
                    d = json.load(f)
                if isinstance(d, dict):
                    self.data = d
            except (OSError, ValueError):
                pass

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        e = self.data.get(url)
        return e if isinstance(e, dict) and e.get("etag") and "body" in e else None

    def put(self, url: str, etag: str, body: Any) -> None:
        self.data[url] = {"etag": etag, "body": body}
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self.data, f)
            os.replace(tmp, self.path)
        except OSError:
            pass  # a cache that cannot be written is only a missed optimisation


def _rate_limit_minutes(e: "urllib.error.HTTPError") -> int:
    h = getattr(e, "headers", None)
    try:
        reset = h.get("X-RateLimit-Reset") if h else None
        retry = h.get("Retry-After") if h else None
        if reset:
            return max(1, -(-(int(reset) - int(time.time())) // 60))
        if retry:
            return max(1, -(-int(retry) // 60))
    except (TypeError, ValueError):
        pass
    return 60


def _is_rate_limited(e: "urllib.error.HTTPError") -> bool:
    if e.code == 429:
        return True
    if e.code != 403:
        return False
    h = getattr(e, "headers", None)
    remaining = h.get("X-RateLimit-Remaining") if h else None
    return remaining == "0" or "rate limit" in str(getattr(e, "reason", "")).lower()


def _slim_release(r: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only what we read, so the on-disk cache stays small."""
    return {
        "tag_name": r.get("tag_name"), "prerelease": bool(r.get("prerelease")), "draft": bool(r.get("draft")),
        "body": r.get("body") or "", "target_commitish": r.get("target_commitish"),
        "assets": [{"name": a.get("name"), "browser_download_url": a.get("browser_download_url"),
                    "digest": a.get("digest")} for a in (r.get("assets") or [])],
    }


def fetch_releases(urlopen: Callable = urllib.request.urlopen, cache: Optional[HttpCache] = None):
    """REQ-660/661/662: one conditional request for the release list."""
    ent = cache.get(API_RELEASES) if cache else None
    headers = {"If-None-Match": ent["etag"]} if ent else {}
    try:
        with _open(API_RELEASES, urlopen, "application/vnd.github+json", headers) as r:
            raw = r.read(2 * 1024 * 1024)
            etag = r.headers.get("ETag") if getattr(r, "headers", None) else None
    except urllib.error.HTTPError as e:
        if e.code == 304 and ent:
            return ent["body"]
        if _is_rate_limited(e):
            raise RateLimited(_rate_limit_minutes(e)) from e
        raise
    data = json.loads(raw)
    if not isinstance(data, list):
        raise UpdateError("unexpected API response")
    slim = [_slim_release(x) for x in data if isinstance(x, dict)]
    if cache and etag:
        cache.put(API_RELEASES, etag, slim)
    return slim


def _asset(rel: Dict[str, Any], info: Dict[str, Any]) -> Dict[str, Any]:
    for a in rel.get("assets") or []:
        url = a.get("browser_download_url") or ""
        if a.get("name") == ASSET_NAME and url.startswith(DOWNLOAD_PREFIX):
            info["asset_url"], info["digest"] = url, a.get("digest")
            break
    return info


def stable_from(releases) -> Optional[Dict[str, Any]]:
    """REQ-600/631: newest non-prerelease with a valid SemVer tag (GitHub lists newest first)."""
    for r in releases:
        tag = r.get("tag_name")
        if r.get("prerelease") or r.get("draft") or not parse_version(tag):
            continue
        commit = r.get("target_commitish")
        info = {"tag": tag, "version": tag.lstrip("v"), "asset_url": None, "digest": None, "kind": "stable",
                "commit": commit if _SHA.match(commit or "") else None}
        return _asset(r, info)
    return None


def test_from(releases) -> Optional[Dict[str, Any]]:
    """REQ-650/652: the rolling `test-build` prerelease and the commit it was built from."""
    for r in releases:
        if r.get("tag_name") != TEST_TAG or r.get("draft"):
            continue
        body = r.get("body") or ""
        m = _BODY_COMMIT.search(body)
        tc = r.get("target_commitish")
        commit = m.group(1) if m else (tc if _SHA.match(tc or "") else None)
        v = _BODY_VERSION.search(body)
        version = v.group(1) if v and parse_version(v.group(1)) else None
        info = {"tag": TEST_TAG, "version": version, "asset_url": None, "digest": None, "kind": "test", "commit": commit}
        return _asset(r, info)
    return None


def download_verified(info: Dict[str, Any], urlopen: Callable = urllib.request.urlopen) -> bytes:
    """REQ-631/632: fail closed without a matching sha256 digest."""
    url, digest = info.get("asset_url"), info.get("digest") or ""
    if not url or not url.startswith(DOWNLOAD_PREFIX):
        raise UpdateError("release has no valid zip asset")
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise UpdateError("release asset has no sha256 digest")
    with _open(url, urlopen, "application/octet-stream") as r:
        data = r.read(MAX_ZIP + 1)
    if len(data) > MAX_ZIP:
        raise UpdateError("zip too large")
    if hashlib.sha256(data).hexdigest() != digest[7:].lower():
        raise UpdateError("sha256 mismatch")
    return data


# --- extract / validate / apply ---
def safe_extract(data: bytes, dest: str) -> str:
    """REQ-633: no absolute paths, '..', symlinks or files outside the zip root."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise UpdateError("invalid zip") from e
    with zf:
        total = 0
        for m in zf.infolist():
            name = m.filename
            parts = name.split("/")
            if name.startswith("/") or ".." in parts or "\\" in name or parts[0] != ZIP_ROOT:
                raise UpdateError(f"unsafe path: {name}")
            if stat.S_ISLNK(m.external_attr >> 16):
                raise UpdateError(f"symlink not allowed: {name}")
            total += m.file_size
            if total > MAX_UNPACKED:
                raise UpdateError("unpacked size too large")
        for m in zf.infolist():
            target = os.path.join(dest, m.filename)
            if m.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(m) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
    return os.path.join(dest, ZIP_ROOT)


def validate(root: str, expected_version: Optional[str] = None) -> None:
    """REQ-634."""
    try:
        with open(os.path.join(root, "plugin.json")) as f:
            name = json.load(f).get("name")
        with open(os.path.join(root, "package.json")) as f:
            version = json.load(f).get("version")
    except (OSError, ValueError, AttributeError) as e:
        raise UpdateError("package metadata missing") from e
    if name != PLUGIN_NAME:
        raise UpdateError("not a System Monitor package")
    for need in ("main.py", os.path.join("dist", "index.js")):
        if not os.path.isfile(os.path.join(root, need)):
            raise UpdateError(f"package missing {need}")
    if expected_version and version != expected_version:
        raise UpdateError("package version does not match release")


def _remove(path: str) -> None:
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.lexists(path):
        os.remove(path)


def _copy(src: str, dst: str) -> None:
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def apply_package(root: str, plugin_dir: str) -> None:
    """REQ-635: replace payload items; restore the backup on any failure."""
    backup = tempfile.mkdtemp(prefix="ssm-bak-", dir=os.path.dirname(os.path.abspath(plugin_dir)))
    try:
        for item in PAYLOAD:
            cur = os.path.join(plugin_dir, item)
            if os.path.lexists(cur):
                _copy(cur, os.path.join(backup, item))
        try:
            for item in PAYLOAD:
                src = os.path.join(root, item)
                if os.path.lexists(src):
                    dst = os.path.join(plugin_dir, item)
                    _remove(dst)
                    _copy(src, dst)
        except Exception:
            for item in PAYLOAD:
                _remove(os.path.join(plugin_dir, item))
                saved = os.path.join(backup, item)
                if os.path.lexists(saved):
                    _copy(saved, os.path.join(plugin_dir, item))
            raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


# --- orchestration ---
def _err(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"[:200]


def resolve(plugin_dir: str, urlopen: Callable = urllib.request.urlopen, test_channel: bool = False,
            cache: Optional[HttpCache] = None):
    """REQ-600..603, 650..654, 657, 660..663. Returns (state, info-to-install-or-None); never raises."""
    current = read_version(plugin_dir)
    build = read_build(plugin_dir)
    state: Dict[str, Any] = {"current": current, "available": False, "checked": True,
                             "checked_at": time.time(), "channel": "test" if test_channel else "stable",
                             **build_info(plugin_dir)}
    s = t = chosen = None
    try:
        releases = fetch_releases(urlopen, cache)
    except RateLimited as e:
        state["error"], state["retry_minutes"] = "RateLimited", e.minutes
        return state, None
    except Exception as e:  # network, JSON...
        state["error"] = _err(e)
        return state, None

    s = stable_from(releases)
    t = test_from(releases) if test_channel else None
    if s:
        state["latest"], state["latest_kind"] = s["version"], "stable"

    if t and t["asset_url"] and t["commit"] and t["commit"] != build["commit"] \
            and (not t["version"] or not is_older(t["version"], current)):
        # REQ-657: a test build made from the very commit of the stable release IS that release.
        same_as_stable = bool(s and s["asset_url"] and s["commit"] == t["commit"])
        chosen = s if same_as_stable else t  # REQ-654 otherwise: the test build wins
    if chosen is None and s and s["asset_url"] and is_newer(s["version"], current):
        chosen = s

    if chosen:
        state["available"] = True
        state["latest"] = chosen["version"] or current
        state["latest_kind"] = chosen["kind"]
        if chosen["kind"] == "test":
            state["commit"] = chosen["commit"][:7]
    if not build["kind"] and build["commit"]:  # REQ-663: manual install -> infer from the commit
        if s and s["commit"] == build["commit"]:
            state["current_kind"] = "stable"
        elif t and t["commit"] == build["commit"]:
            state["current_kind"] = "test"
    if not s and not t:
        state["error"] = "no stable release"  # REQ-602
    return state, chosen


def check(plugin_dir: str, urlopen: Callable = urllib.request.urlopen, test_channel: bool = False,
          cache: Optional[HttpCache] = None) -> Dict[str, Any]:
    return resolve(plugin_dir, urlopen, test_channel, cache)[0]


def install(plugin_dir: str, urlopen: Callable = urllib.request.urlopen, test_channel: bool = False,
            cache: Optional[HttpCache] = None) -> str:
    """REQ-630/655: refetch, require something new, download, verify, validate, apply. Returns the version."""
    if not os.access(plugin_dir, os.W_OK) or not os.access(os.path.dirname(os.path.abspath(plugin_dir)), os.W_OK):
        raise UpdateError("plugin folder is not writable: the backend must run as root (plugin.json flags)")
    state, info = resolve(plugin_dir, urlopen, test_channel, cache)
    if info is None:
        if state.get("retry_minutes"):
            raise RateLimited(state["retry_minutes"])
        raise UpdateError(state.get("error") or "already up to date")
    data = download_verified(info, urlopen)
    tmp = tempfile.mkdtemp(prefix="ssm-upd-")
    try:
        root = safe_extract(data, tmp)
        # stable: the package must be exactly the release; test: only well-formed
        validate(root, info["version"] if info["kind"] == "stable" else None)
        apply_package(root, plugin_dir)
        _stamp_kind(plugin_dir, info["kind"])  # REQ-663
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return info["version"] or read_version(plugin_dir)


def clean_env(env=None) -> Dict[str, str]:
    """Decky is a frozen (PyInstaller) app: its LD_LIBRARY_PATH breaks system binaries like systemctl."""
    env = dict(os.environ if env is None else env)
    orig = env.pop("LD_LIBRARY_PATH_ORIG", None)
    for k in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONHOME", "PYTHONPATH"):
        env.pop(k, None)
    if orig:
        env["LD_LIBRARY_PATH"] = orig
    env["PATH"] = ":".join(filter(None, [env.get("PATH"), "/usr/local/sbin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]))
    return env


def schedule_decky_restart(log_path: str = "/tmp/ssm-restart.log", delay: int = 3) -> None:
    """REQ-636: detached, with a clean environment; the outcome is written to log_path."""
    script = (
        f"sleep {int(delay)}; "
        "{ echo \"restart $(date)\"; "
        "systemctl restart plugin_loader || service plugin_loader restart; "
        "echo \"exit=$?\"; } >> \"$1\" 2>&1"
    )
    subprocess.Popen(
        ["sh", "-c", script, "sh", log_path],
        start_new_session=True,
        env=clean_env(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

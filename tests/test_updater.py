import hashlib
import io
import json
import os
import zipfile

import pytest

from sysmon import updater
from sysmon.updater import UpdateError


def make_zip(files, root=updater.ZIP_ROOT, extra=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(f"{root}/{name}" if root else name, data)
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


def good_files(version="0.2.0"):
    return {
        "plugin.json": json.dumps({"name": "System Monitor"}),
        "package.json": json.dumps({"version": version}),
        "main.py": "# new",
        "LICENSE": "x",
        "dist/index.js": "new js",
        "py_modules/sysmon.py": "new",
    }


class Resp:
    def __init__(self, data, headers=None):
        self._d = data
        self.headers = headers or {}

    def read(self, n=-1):
        return self._d if n < 0 else self._d[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def fake_urlopen(release=None, zip_bytes=b"", test_release=None):
    def _open(req, timeout=None, context=None):
        url = req.full_url
        if url == updater.API_RELEASES:  # REQ-660: one call lists stable + test-build
            items = [x for x in (test_release, release) if x is not None]
            if not items:
                raise OSError("offline")
            return Resp(json.dumps(items).encode())
        return Resp(zip_bytes)
    return _open


def release(zip_bytes, tag="v0.2.0", commit=None, **kw):
    a = {
        "name": updater.ASSET_NAME,
        "browser_download_url": updater.DOWNLOAD_PREFIX + f"{tag}/{updater.ASSET_NAME}",
        "digest": "sha256:" + hashlib.sha256(zip_bytes).hexdigest(),
    }
    a.update(kw.pop("asset", {}))
    r = {"tag_name": tag, "prerelease": False, "draft": False, "assets": [a]}
    if commit:
        r["target_commitish"] = commit
    r.update(kw)
    return r


def installed(tmp_path, version="0.1.1"):
    d = tmp_path / "plugins" / "System Monitor"
    (d / "dist").mkdir(parents=True)
    (d / "py_modules").mkdir()
    (d / "package.json").write_text(json.dumps({"version": version}))
    (d / "plugin.json").write_text(json.dumps({"name": "System Monitor"}))
    (d / "main.py").write_text("# old")
    (d / "dist" / "index.js").write_text("old js")
    (d / "py_modules" / "stale.py").write_text("stale")
    (d / "settings-keep.txt").write_text("keep")
    return str(d)


def test_semver_REQ601():
    assert updater.is_newer("v0.1.2", "0.1.1")
    assert updater.is_newer("1.0.0", "0.9.9")
    assert updater.is_newer("v0.10.0", "0.9.0")  # numeric, not lexicographic
    assert not updater.is_newer("0.1.1", "0.1.1")
    assert not updater.is_newer("0.1.0", "0.1.1")
    assert updater.is_newer("1.0.0", "1.0.0-rc1")
    assert not updater.is_newer("1.0.0-rc2", "1.0.0")
    assert not updater.is_newer("garbage", "0.1.1")
    assert not updater.is_newer("v9.9.9", "garbage")


def test_read_version(tmp_path):
    assert updater.read_version(installed(tmp_path)) == "0.1.1"
    assert updater.read_version(str(tmp_path / "nope")) == "0.0.0"


def test_check_available_and_uptodate_and_error_REQ602(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    st = updater.check(d, fake_urlopen(release(z), z))
    assert st["available"] and st["latest"] == "0.2.0" and st["current"] == "0.1.1" and "error" not in st
    st = updater.check(d, fake_urlopen(release(z, tag="v0.1.1"), z))
    assert not st["available"] and st["latest"] == "0.1.1"
    st = updater.check(d, fake_urlopen(None))  # offline: no raise
    assert not st["available"] and st["error"] and st["checked"]


def test_prerelease_and_bad_tag_ignored_REQ600(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    assert "error" in updater.check(d, fake_urlopen(release(z, prerelease=True), z))
    assert "error" in updater.check(d, fake_urlopen(release(z, tag="test-build"), z))


def test_foreign_asset_url_not_offered_REQ631(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    r = release(z, asset={"browser_download_url": "https://evil.example/steam-system-monitor.zip"})
    assert not updater.check(d, fake_urlopen(r, z))["available"]
    r = release(z, asset={"name": "other.zip"})
    assert not updater.check(d, fake_urlopen(r, z))["available"]


def test_install_happy_path_and_payload_replaced_REQ635(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    v = updater.install(d, fake_urlopen(release(z), z))
    assert v == "0.2.0"
    assert open(os.path.join(d, "main.py")).read() == "# new"
    assert open(os.path.join(d, "dist/index.js")).read() == "new js"
    assert updater.read_version(d) == "0.2.0"
    assert not os.path.exists(os.path.join(d, "py_modules/stale.py"))  # replaced wholesale
    assert open(os.path.join(d, "settings-keep.txt")).read() == "keep"  # non-payload untouched
    assert os.listdir(os.path.dirname(d)) == ["System Monitor"]  # backup cleaned


def test_install_requires_newer_REQ630(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.1.1"))
    with pytest.raises(UpdateError):
        updater.install(d, fake_urlopen(release(z, tag="v0.1.1"), z))


def test_digest_missing_or_mismatch_fails_closed_REQ632(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    r = release(z)
    r["assets"][0]["digest"] = None
    with pytest.raises(UpdateError, match="digest"):
        updater.install(d, fake_urlopen(r, z))
    r = release(z, asset={"digest": "sha256:" + "0" * 64})
    with pytest.raises(UpdateError, match="mismatch"):
        updater.install(d, fake_urlopen(r, z))
    assert open(os.path.join(d, "main.py")).read() == "# old"  # untouched


def test_zip_slip_symlink_and_foreign_root_REQ633(tmp_path):
    for bad in (
        make_zip(good_files(), extra={"steam-system-monitor/../evil.py": "x"}),
        make_zip(good_files(), extra={"/abs.py": "x"}),
        make_zip(good_files(), root="other"),
    ):
        with pytest.raises(UpdateError):
            updater.safe_extract(bad, str(tmp_path / "x"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        zi = zipfile.ZipInfo("steam-system-monitor/link")
        zi.external_attr = (0o120777) << 16
        z.writestr(zi, "/etc/passwd")
    with pytest.raises(UpdateError, match="symlink"):
        updater.safe_extract(buf.getvalue(), str(tmp_path / "y"))
    assert not (tmp_path / "evil.py").exists()


def test_validate_REQ634(tmp_path):
    for mutate in (
        lambda f: f.update({"plugin.json": json.dumps({"name": "Other"})}),
        lambda f: f.pop("main.py"),
        lambda f: f.pop("dist/index.js"),
    ):
        f = good_files()
        mutate(f)
        root = updater.safe_extract(make_zip(f), str(tmp_path / str(id(mutate))))
        with pytest.raises(UpdateError):
            updater.validate(root)
    root = updater.safe_extract(make_zip(good_files("0.9.0")), str(tmp_path / "v"))
    with pytest.raises(UpdateError, match="version"):
        updater.validate(root, "0.2.0")


def test_rollback_on_failure_REQ635(tmp_path, monkeypatch):
    d = installed(tmp_path)
    z = make_zip(good_files())
    real = updater._copy
    calls = {"n": 0}

    def flaky(src, dst):
        # let the backup phase succeed, fail midway through the apply phase
        if os.sep + "steam-system-monitor" + os.sep in src or src.endswith("steam-system-monitor"):
            calls["n"] += 1
            if calls["n"] == 3:
                raise OSError("disk full")
        return real(src, dst)

    monkeypatch.setattr(updater, "_copy", flaky)
    with pytest.raises(OSError):
        updater.install(d, fake_urlopen(release(z), z))
    assert open(os.path.join(d, "main.py")).read() == "# old"
    assert open(os.path.join(d, "dist/index.js")).read() == "old js"
    assert os.path.exists(os.path.join(d, "py_modules/stale.py"))
    assert updater.read_version(d) == "0.1.1"
    assert os.listdir(os.path.dirname(d)) == ["System Monitor"]


def test_cert_error_retries_with_alternative_bundle_only(monkeypatch, tmp_path):
    import ssl
    import urllib.error
    bundle = tmp_path / "ca.crt"
    bundle.write_text("x")
    monkeypatch.setattr(updater, "CA_BUNDLES", (str(bundle),))
    monkeypatch.setattr(updater.ssl, "create_default_context", lambda cafile=None: object())
    seen = []

    def urlopen(req, timeout=None, context=None):
        seen.append(context)
        if len(seen) == 1:
            raise urllib.error.URLError(ssl.SSLCertVerificationError("bad"))
        return Resp(b"{}")

    assert updater._open("https://x", urlopen, "a").read() == b"{}"
    assert len(seen) == 2  # default, then the alternative bundle

    def offline(req, timeout=None, context=None):
        raise urllib.error.URLError(OSError("offline"))
    with pytest.raises(urllib.error.URLError):  # non-cert errors are not retried
        updater._open("https://x", offline, "a")


def test_not_writable_fails_before_touching_anything_REQ638(tmp_path, monkeypatch):
    d = installed(tmp_path)
    z = make_zip(good_files())
    monkeypatch.setattr(updater.os, "access", lambda p, m: False)
    with pytest.raises(UpdateError, match="root"):
        updater.install(d, fake_urlopen(release(z), z))
    assert open(os.path.join(d, "main.py")).read() == "# old"


def test_clean_env_drops_pyinstaller_libs_REQ636():
    env = updater.clean_env({"LD_LIBRARY_PATH": "/tmp/_MEI1", "LD_LIBRARY_PATH_ORIG": "/usr/lib", "PATH": "/x", "PYTHONHOME": "/p"})
    assert env["LD_LIBRARY_PATH"] == "/usr/lib" and "PYTHONHOME" not in env and "LD_LIBRARY_PATH_ORIG" not in env
    assert "/usr/bin" in env["PATH"].split(":") and env["PATH"].startswith("/x")
    env = updater.clean_env({"LD_LIBRARY_PATH": "/tmp/_MEI1"})
    assert "LD_LIBRARY_PATH" not in env


def test_restart_is_detached_logged_and_clean_REQ636(monkeypatch):
    seen = {}

    def fake_popen(args, **kw):
        seen["args"], seen["kw"] = args, kw

    monkeypatch.setattr(updater.subprocess, "Popen", fake_popen)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/_MEIx")
    updater.schedule_decky_restart("/logs/restart.log", delay=2)
    assert seen["kw"]["start_new_session"] is True
    assert "LD_LIBRARY_PATH" not in seen["kw"]["env"]
    assert seen["args"][-1] == "/logs/restart.log"  # log path passed as $1, never interpolated
    assert "systemctl restart plugin_loader" in seen["args"][2] and "sleep 2" in seen["args"][2]


# ---------------- test channel (REQ-650..656) ----------------
SHA_A, SHA_B = "a" * 40, "b" * 40


def make_test_release(zip_bytes, commit=SHA_B, version="0.2.0", **kw):
    r = {
        "tag_name": updater.TEST_TAG, "prerelease": True, "draft": False,
        "body": f"version: {version}\ncommit: {commit}\n\nAutomatic TEST build", "target_commitish": commit,
        "assets": [{
            "name": updater.ASSET_NAME,
            "browser_download_url": updater.DOWNLOAD_PREFIX + f"{updater.TEST_TAG}/{updater.ASSET_NAME}",
            "digest": "sha256:" + hashlib.sha256(zip_bytes).hexdigest(),
        }],
    }
    r.update(kw)
    return r




def set_build(d, commit, version="0.1.1"):
    with open(os.path.join(d, "build.json"), "w") as f:
        json.dump({"version": version, "commit": commit}, f)


def test_test_build_ignored_when_channel_off_REQ654(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, version="0.9.0"))
    st = updater.check(d, uo)  # default: stable only
    assert not st["available"] and st["channel"] == "stable"


def test_new_test_build_offered_when_commit_differs_REQ653(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    st = updater.check(d, uo, test_channel=True)
    assert st["available"] and st["latest_kind"] == "test" and st["commit"] == SHA_B[:7] and st["channel"] == "test"


def test_same_commit_is_up_to_date_REQ653(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_B)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert not updater.check(d, uo, test_channel=True)["available"]


def test_older_test_version_is_not_offered_REQ653(tmp_path):
    d = installed(tmp_path, version="0.3.0")
    set_build(d, SHA_A, "0.3.0")
    z = make_zip(good_files("0.2.0"))
    uo = fake_urlopen(release(z, tag="v0.2.0"), z, test_release=make_test_release(z, commit=SHA_B, version="0.2.0"))
    assert not updater.check(d, uo, test_channel=True)["available"]  # no regression


def test_unknown_installed_commit_offers_test_build_REQ653(tmp_path):
    d = installed(tmp_path)  # no build.json (old install)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, version="0.1.1"))
    assert updater.check(d, uo, test_channel=True)["available"]


def test_newer_stable_when_no_new_test_build_REQ654(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_B)
    z = make_zip(good_files("0.5.0"))
    uo = fake_urlopen(release(z, tag="v0.5.0"), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    st = updater.check(d, uo, test_channel=True)
    assert st["available"] and st["latest_kind"] == "stable" and st["latest"] == "0.5.0"


def test_test_build_missing_does_not_break_stable_REQ654(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.2.0"))
    st = updater.check(d, fake_urlopen(release(z), z, test_release=None), test_channel=True)  # test-build 404
    assert st["available"] and st["latest_kind"] == "stable" and "error" not in st


def test_install_test_build_applies_and_records_commit_REQ655(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    files = good_files("0.1.1")
    files["build.json"] = json.dumps({"version": "0.1.1", "commit": SHA_B})
    z = make_zip(files)
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert updater.install(d, uo, test_channel=True) == "0.1.1"
    assert updater.read_build(d)["commit"] == SHA_B
    assert updater.read_build(d)["kind"] == "test"  # REQ-663
    assert open(os.path.join(d, "main.py")).read() == "# new"
    assert not updater.check(d, uo, test_channel=True)["available"]  # now up to date


def test_test_build_still_needs_digest_and_valid_package_REQ655(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.1.1"))
    t = make_test_release(z, version="0.1.1")
    t["assets"][0]["digest"] = None
    with pytest.raises(UpdateError, match="digest"):
        updater.install(d, fake_urlopen(release(z, tag="v0.1.1"), z, test_release=t), test_channel=True)
    bad = make_zip({**good_files("0.1.1"), "plugin.json": json.dumps({"name": "Other"})})
    with pytest.raises(UpdateError):
        updater.install(d, fake_urlopen(release(bad, tag="v0.1.1"), bad, test_release=make_test_release(bad, version="0.1.1")), test_channel=True)
    assert open(os.path.join(d, "main.py")).read() == "# old"


def test_install_stable_refuses_when_only_test_exists_REQ654(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1"), z, test_release=make_test_release(z, version="9.9.9"))
    with pytest.raises(UpdateError, match="up to date"):
        updater.install(d, uo)  # channel off: never installs the test build


def test_read_build_robust(tmp_path):
    d = installed(tmp_path)
    assert updater.read_build(d) == {"version": None, "commit": None, "kind": None}
    with open(os.path.join(d, "build.json"), "w") as f:
        f.write("{not json")
    assert updater.read_build(d)["commit"] is None
    set_build(d, "short")
    assert updater.read_build(d)["commit"] is None  # not a full sha


# ---------------- REQ-657: same commit => treated as the stable release ----------------
def test_test_build_with_stable_commit_is_labelled_stable_REQ657(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_B), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    st = updater.check(d, uo, test_channel=True)
    assert st["available"] and st["latest_kind"] == "stable" and "commit" not in st  # no test label/warning


def test_same_commit_as_stable_installs_the_stable_asset_REQ657(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    files = good_files("0.1.1")
    files["build.json"] = json.dumps({"version": "0.1.1", "commit": SHA_B})
    z = make_zip(files)
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_B), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert updater.install(d, uo, test_channel=True) == "0.1.1"
    assert updater.read_build(d)["commit"] == SHA_B


def test_installed_commit_equals_shared_commit_is_up_to_date_REQ657(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_B)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_B), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert not updater.check(d, uo, test_channel=True)["available"]


def test_different_commits_still_label_test_REQ654(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_A), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    st = updater.check(d, uo, test_channel=True)
    assert st["available"] and st["latest_kind"] == "test"


def test_stable_commit_unknown_branch_name_is_not_merged_REQ657(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(release(z, tag="v0.1.1", commit="main"), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert updater.check(d, uo, test_channel=True)["latest_kind"] == "test"  # cannot prove equality


def test_test_channel_ok_even_if_stable_fetch_fails_REQ654(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    z = make_zip(good_files("0.1.1"))
    uo = fake_urlopen(None, z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))  # stable API offline
    st = updater.check(d, uo, test_channel=True)
    assert st["available"] and st["latest_kind"] == "test" and "error" not in st


# ---------------- REQ-660..664: rate limit, cache, installed origin ----------------
import urllib.error


class Hdr(dict):
    pass


def http_error(code, headers=None, reason="rate limit exceeded"):
    return urllib.error.HTTPError(updater.API_RELEASES, code, reason, Hdr(headers or {}), None)


def test_single_api_request_per_check_REQ660(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.2.0"))
    calls = []
    inner = fake_urlopen(release(z), z, test_release=make_test_release(z, commit=SHA_B, version="0.2.0"))

    def counting(req, timeout=None, context=None):
        calls.append(req.full_url)
        return inner(req, timeout, context)

    updater.check(d, counting, test_channel=True)
    assert calls == [updater.API_RELEASES]  # was two calls with the test channel on


def test_rate_limited_is_reported_with_minutes_REQ662(tmp_path):
    d = installed(tmp_path)
    reset = str(int(__import__("time").time()) + 600)

    def limited(req, timeout=None, context=None):
        raise http_error(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset})

    st = updater.check(d, limited)
    assert st["error"] == "RateLimited" and 9 <= st["retry_minutes"] <= 11 and not st["available"]
    with pytest.raises(updater.RateLimited):
        updater.install(d, limited)


def test_rate_limit_detected_by_message_and_429_but_not_other_403_REQ662(tmp_path):
    d = installed(tmp_path)

    def by_reason(req, timeout=None, context=None):
        raise http_error(403, {}, "rate limit exceeded")

    def too_many(req, timeout=None, context=None):
        raise http_error(429, {"Retry-After": "120"}, "Too Many Requests")

    def forbidden(req, timeout=None, context=None):
        raise http_error(403, {"X-RateLimit-Remaining": "50"}, "Forbidden")

    assert updater.check(d, by_reason)["error"] == "RateLimited"
    st = updater.check(d, too_many)
    assert st["error"] == "RateLimited" and st["retry_minutes"] == 2
    assert updater.check(d, forbidden)["error"].startswith("HTTPError")  # a plain 403 is a normal failure


def test_etag_cache_serves_304_without_a_body_REQ661(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files("0.2.0"))
    cache = updater.HttpCache(str(tmp_path / "cache" / "http-cache.json"))
    sent = []
    inner = fake_urlopen(release(z), z)

    def server(req, timeout=None, context=None):
        sent.append(req.get_header("If-none-match"))
        if req.get_header("If-none-match") == '"v1"':
            raise http_error(304, {}, "Not Modified")
        r = inner(req, timeout, context)
        r.headers = {"ETag": '"v1"'}
        return r

    assert updater.check(d, server, cache=cache)["available"]
    assert updater.check(d, server, cache=cache)["available"]  # answered from cache via 304
    assert sent == [None, '"v1"']
    # persisted: a fresh cache object (new process after a Decky restart) still sends the ETag
    cache2 = updater.HttpCache(str(tmp_path / "cache" / "http-cache.json"))
    assert updater.check(d, server, cache=cache2)["available"]
    assert sent[-1] == '"v1"'


def test_corrupt_cache_file_is_ignored_REQ661(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{nope")
    assert updater.HttpCache(str(p)).get(updater.API_RELEASES) is None


def test_current_kind_from_build_json_after_install_REQ663(tmp_path):
    d = installed(tmp_path)
    set_build(d, SHA_A)
    with open(os.path.join(d, "build.json"), "w") as f:
        json.dump({"version": "0.1.1", "commit": SHA_A, "kind": "test"}, f)
    z = make_zip(good_files("0.1.1"))
    st = updater.check(d, fake_urlopen(release(z, tag="v0.1.1"), z))
    assert st["current_kind"] == "test" and st["current_commit"] == SHA_A[:7]


def test_current_kind_inferred_for_manual_installs_REQ663(tmp_path):
    z = make_zip(good_files("0.1.1"))
    d = installed(tmp_path)
    set_build(d, SHA_B)  # no kind recorded (installed by hand)
    # matches the test-build commit -> test
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_A), z, test_release=make_test_release(z, commit=SHA_B, version="0.1.1"))
    assert updater.check(d, uo, test_channel=True)["current_kind"] == "test"
    # matches the stable release commit -> stable
    uo = fake_urlopen(release(z, tag="v0.1.1", commit=SHA_B), z)
    assert updater.check(d, uo)["current_kind"] == "stable"
    # matches nothing -> unknown (None), but the commit is still shown
    set_build(d, SHA_A)
    st = updater.check(d, fake_urlopen(release(z, tag="v0.1.1", commit=SHA_B), z))
    assert st["current_kind"] is None and st["current_commit"] == SHA_A[:7]


def test_install_stable_records_kind_REQ663(tmp_path):
    d = installed(tmp_path)
    files = good_files("0.2.0")
    files["build.json"] = json.dumps({"version": "0.2.0", "commit": SHA_B})
    z = make_zip(files)
    updater.install(d, fake_urlopen(release(z, commit=SHA_B), z))
    assert updater.read_build(d)["kind"] == "stable"

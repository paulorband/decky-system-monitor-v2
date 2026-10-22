"""Spec 010: updates driven by release.json, with the API only as a fallback."""
import hashlib
import os
import urllib.error

import pytest

from sysmon import updater
from sysmon.updater import UpdateError
from test_updater import Resp, fake_urlopen, good_files, installed, make_zip, release

SHA_A = "a" * 40
SHA_B = "b" * 40


def manifest(z, tag="v0.2.0", version="0.2.0", commit=SHA_A, **kw):
    m = {"schema": 1, "tag": tag, "version": version, "kind": "stable" if tag != "test-build" else "test",
         "commit": commit, "asset": updater.ASSET_NAME, "sha256": hashlib.sha256(z).hexdigest(),
         "size": len(z), "notes": "### Novidades\n- algo"}
    m.update(kw)
    return m


def counting(inner):
    calls = []

    def _open(req, timeout=None, context=None):
        calls.append(req.full_url)
        return inner(req, timeout, context)
    return _open, calls


def test_manifests_need_no_api_call_AC1(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    ms = {updater.STABLE_MANIFEST: manifest(z),
          updater.TEST_MANIFEST: manifest(z, tag="test-build", commit=SHA_B)}
    op, calls = counting(fake_urlopen(None, z, manifests=ms))  # no API release at all
    st = updater.check(d, op, test_channel=True)
    assert st["available"] and st["latest"] == "0.2.0" and st["latest_kind"] == "test"
    assert updater.API_RELEASES not in calls
    st = updater.check(d, op)
    assert st["latest_kind"] == "stable" and st["notes"].startswith("### Novidades")
    assert updater.API_RELEASES not in calls


def test_install_uses_built_url_and_manifest_sha_AC2(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    op, calls = counting(fake_urlopen(None, z, manifests={updater.STABLE_MANIFEST: manifest(z)}))
    assert updater.install(d, op) == "0.2.0"
    assert updater.DOWNLOAD_PREFIX + "v0.2.0/" + updater.ASSET_NAME in calls
    assert updater.API_RELEASES not in calls

    d2 = installed(tmp_path / "second")
    bad = manifest(z, sha256="0" * 64)
    with pytest.raises(UpdateError, match="sha256 mismatch"):
        updater.install(d2, fake_urlopen(None, z, manifests={updater.STABLE_MANIFEST: bad}))
    assert updater.read_version(d2) == "0.1.1"


@pytest.mark.parametrize("override", [
    {"tag": "latest"}, {"tag": "v0.2"}, {"sha256": "xyz"}, {"schema": 2}, {"version": "0.9.9"},
    {"notes": "x" * (updater.MANIFEST_MAX + 1)},
])
def test_invalid_manifest_is_ignored_AC3(tmp_path, override):
    d = installed(tmp_path)
    z = make_zip(good_files())
    ms = {updater.STABLE_MANIFEST: manifest(z, **override)}
    op, calls = counting(fake_urlopen(None, z, manifests=ms))
    st = updater.check(d, op)  # falls back to the API, which has no release here
    assert updater.API_RELEASES in calls and not st["available"]


def test_manifest_cannot_redirect_the_download_AC3(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    m = manifest(z, asset="https://evil.example/x.zip", asset_url="https://evil.example/x.zip")
    op, calls = counting(fake_urlopen(None, z, manifests={updater.STABLE_MANIFEST: m}))
    updater.install(d, op)
    assert not any("evil" in c for c in calls)


def test_missing_manifest_falls_back_to_api_AC4(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    op, calls = counting(fake_urlopen(release(z), z))  # old release: no release.json (404)
    st = updater.check(d, op)
    assert st["available"] and st["latest"] == "0.2.0"
    assert calls.count(updater.API_RELEASES) == 1


def test_network_error_on_manifest_does_not_spend_the_api_AC4(tmp_path):
    d = installed(tmp_path)

    def offline(req, timeout=None, context=None):
        if req.full_url == updater.API_RELEASES:
            raise AssertionError("API must not be called")
        raise urllib.error.URLError(OSError("offline"))

    st = updater.check(d, offline)
    assert st["error"].startswith("URLError") and not st["available"]


def test_same_commit_test_build_is_the_stable_release_AC5(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    ms = {updater.STABLE_MANIFEST: manifest(z, commit=SHA_A),
          updater.TEST_MANIFEST: manifest(z, tag="test-build", commit=SHA_A)}
    st, info = updater.resolve(d, fake_urlopen(None, z, manifests=ms), test_channel=True)
    assert st["latest_kind"] == "stable" and info["tag"] == "v0.2.0"


def test_test_manifest_missing_uses_api_only_for_it(tmp_path):
    d = installed(tmp_path)
    z = make_zip(good_files())
    op, calls = counting(fake_urlopen(release(z), z, manifests={updater.STABLE_MANIFEST: manifest(z)}))
    st = updater.check(d, op, test_channel=True)
    assert st["latest_kind"] == "stable"
    assert calls.count(updater.API_RELEASES) == 1  # the stable part still came from the manifest


def test_real_package_manifest_matches_zip():
    """AC-6: the manifest script output agrees with the zip it describes (runs when a package was built)."""
    zip_path = os.path.join("out", updater.ASSET_NAME)
    json_path = os.path.join("out", updater.MANIFEST_NAME)
    if not (os.path.exists(zip_path) and os.path.exists(json_path)):
        pytest.skip("run `pnpm package` + scripts/release-manifest.mjs first")
    import json
    m = json.load(open(json_path, encoding="utf-8"))
    data = open(zip_path, "rb").read()
    assert m["sha256"] == hashlib.sha256(data).hexdigest() and m["size"] == len(data)
    info = updater.fetch_manifest("https://x", "stable" if m["tag"] != "test-build" else "test",
                                  lambda req, timeout=None, context=None: Resp(json.dumps(m).encode()))
    assert info["digest"] == "sha256:" + m["sha256"]

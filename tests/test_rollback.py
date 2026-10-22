"""Spec 009: rollback copy, restore and release notes."""
import json
import os

import pytest

from sysmon import updater
from sysmon.updater import UpdateError
from test_updater import fake_urlopen, good_files, installed, make_zip, release


def rb_dir(tmp_path):
    return str(tmp_path / "settings" / "steam-system-monitor" / "rollback")


def test_install_saves_previous_version_REQ700(tmp_path):  # AC-1
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    z = make_zip(good_files())
    assert updater.install(d, fake_urlopen(release(z), z), rollback_dir=rb) == "0.2.0"
    assert updater.read_version(rb) == "0.1.1"
    assert open(os.path.join(rb, "main.py")).read() == "# old"
    assert open(os.path.join(rb, "py_modules", "stale.py")).read() == "stale"
    assert not os.path.exists(os.path.join(rb, "settings-keep.txt"))  # only payload items
    assert sorted(os.listdir(os.path.dirname(rb))) == ["rollback"]  # no staging/.old leftovers
    assert updater.rollback_info(d, rb) == {"version": "0.1.1", "commit": None, "kind": None}


def test_second_install_replaces_the_copy_REQ700(tmp_path):
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    z = make_zip(good_files())
    updater.install(d, fake_urlopen(release(z), z), rollback_dir=rb)
    z3 = make_zip(good_files("0.3.0"))
    updater.install(d, fake_urlopen(release(z3, tag="v0.3.0"), z3), rollback_dir=rb)
    assert updater.read_version(rb) == "0.2.0"  # only the immediately previous version


def test_failed_copy_aborts_without_touching_install_REQ701(tmp_path, monkeypatch):  # AC-1
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    z = make_zip(good_files())

    def broken(*a):
        raise OSError("disk full")

    monkeypatch.setattr(updater, "save_rollback", broken)
    with pytest.raises(UpdateError, match="rollback copy"):
        updater.install(d, fake_urlopen(release(z), z), rollback_dir=rb)
    assert updater.read_version(d) == "0.1.1"
    assert open(os.path.join(d, "main.py")).read() == "# old"


def test_rollback_restores_exactly_and_drops_copy_REQ710(tmp_path):  # AC-2
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    files = good_files()
    files["build.json"] = json.dumps({"version": "0.2.0", "commit": "a" * 40})
    z = make_zip(files)
    updater.install(d, fake_urlopen(release(z), z), rollback_dir=rb)
    assert os.path.exists(os.path.join(d, "build.json"))

    assert updater.rollback(d, rb) == "0.1.1"
    assert updater.read_version(d) == "0.1.1"
    assert open(os.path.join(d, "main.py")).read() == "# old"
    assert open(os.path.join(d, "dist", "index.js")).read() == "old js"
    assert not os.path.exists(os.path.join(d, "build.json"))  # exact: the old version had none
    assert open(os.path.join(d, "settings-keep.txt")).read() == "keep"  # non-payload untouched
    assert not os.path.exists(rb)  # REQ-711: one-shot
    assert updater.rollback_info(d, rb) is None


def test_missing_invalid_or_identical_copy_REQ703(tmp_path):  # AC-3
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    assert updater.rollback_info(d, rb) is None
    with pytest.raises(UpdateError, match="no previous version"):
        updater.rollback(d, rb)

    updater.save_rollback(d, rb)  # identical to the installed one
    assert updater.rollback_info(d, rb) is None

    os.remove(os.path.join(rb, "main.py"))  # invalid copy
    with open(os.path.join(rb, "package.json"), "w") as f:
        json.dump({"version": "0.0.9"}, f)
    assert updater.rollback_info(d, rb) is None
    with pytest.raises(UpdateError):
        updater.rollback(d, rb)
    assert updater.read_version(d) == "0.1.1"


def test_rollback_failure_keeps_current_version_REQ635(tmp_path, monkeypatch):  # AC-4
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    z = make_zip(good_files())
    updater.install(d, fake_urlopen(release(z), z), rollback_dir=rb)
    real = updater._copy
    calls = {"n": 0}

    def flaky(src, dst):
        if src.startswith(rb):
            calls["n"] += 1
            if calls["n"] == 3:
                raise OSError("disk full")
        return real(src, dst)

    monkeypatch.setattr(updater, "_copy", flaky)
    with pytest.raises(OSError):
        updater.rollback(d, rb)
    assert updater.read_version(d) == "0.2.0"
    assert open(os.path.join(d, "main.py")).read() == "# new"
    assert os.path.isdir(rb)  # copy kept for another try


def test_rollback_requires_writable_folder_REQ712(tmp_path, monkeypatch):
    d, rb = installed(tmp_path), rb_dir(tmp_path)
    monkeypatch.setattr(updater.os, "access", lambda *a: False)
    with pytest.raises(UpdateError, match="not writable"):
        updater.rollback(d, rb)


def test_state_carries_release_notes_REQ722(tmp_path):  # AC-5
    d = installed(tmp_path)
    z = make_zip(good_files())
    rel = release(z, body="## [0.2.0]\n- Novidade **boa**\n" + "x" * 9000)
    st = updater.check(d, fake_urlopen(rel, z))
    assert st["available"] and st["notes"].startswith("## [0.2.0]\n- Novidade **boa**")
    assert len(st["notes"]) == updater.NOTES_MAX
    st = updater.check(d, fake_urlopen(release(make_zip(good_files("0.1.1")), tag="v0.1.1", body="old"), z))
    assert "notes" not in st  # nothing to install, nothing to describe

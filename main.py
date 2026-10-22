import asyncio
import os
import sys
import time

import decky  # provided by Decky Loader at runtime

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# Decky already adds py_modules to sys.path; keep a fallback for older loaders.
_PY_MODULES = os.path.join(PLUGIN_DIR, "py_modules")
if _PY_MODULES not in sys.path:
    sys.path.append(_PY_MODULES)

from sysmon import settings, updater  # noqa: E402
from sysmon.metrics import MetricsCollector  # noqa: E402
from sysmon.processes import ProcessSampler  # noqa: E402
from sysmon.steamapps import default_steam_dirs  # noqa: E402

# Update state lives at module level so the update methods never depend on _main having run (spec 008).
try:
    _current = updater.read_version(PLUGIN_DIR)
except Exception:  # never let a version read stop the backend from loading
    _current = "0.0.0"
try:
    _build = updater.build_info(PLUGIN_DIR)
except Exception:
    _build = {}
_update_state = {"current": _current, "available": False, "checked": False, **_build}
_installing = False


def _settings_dir() -> str:
    return getattr(decky, "DECKY_PLUGIN_SETTINGS_DIR", None) or os.path.join(PLUGIN_DIR, ".settings")


def _settings_path() -> str:
    return os.path.join(_settings_dir(), "settings.json")


def _rollback_dir() -> str:
    """Spec 009 REQ-700: outside the plugin folder, so Decky never loads it as a plugin."""
    return os.path.join(_settings_dir(), "rollback")


CHANGELOG_MAX = 64 * 1024  # spec 009 REQ-723


def _test_channel() -> bool:
    """REQ-655: the channel comes from our own persisted settings, never from the frontend."""
    try:
        return bool(settings.load(_settings_path()).get("test_channel"))
    except Exception:
        return False


def _err(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"[:200]


class Plugin:
    async def _main(self):
        self.metrics = MetricsCollector()
        # Decky may run plugins with a different HOME; it tells us the Steam user's home.
        home = getattr(decky, "DECKY_USER_HOME", None) or os.path.expanduser("~")
        self.processes = ProcessSampler(steam_dirs=default_steam_dirs(home))
        self.http_cache = updater.HttpCache(os.path.join(_settings_dir(), "http-cache.json"))
        decky.logger.info("System Monitor %s loaded (dir=%s)", _update_state["current"], PLUGIN_DIR)

    async def _unload(self):
        decky.logger.info("System Monitor unloaded")

    async def get_metrics(self) -> dict:
        try:
            return self.metrics.snapshot()
        except Exception:
            decky.logger.exception("get_metrics failed")
            raise

    async def get_processes(
        self,
        sort_key: str = "cpu",
        descending: bool = True,
        limit: int = 40,
        include_kernel: bool = False,
        group="app",  # "app" | "name" | "none" (bool accepted, spec 005)
    ) -> dict:
        try:
            return self.processes.sample(sort_key, descending, limit, include_kernel, group)
        except Exception:
            decky.logger.exception("get_processes failed")
            raise

    # ------------------------------------------------------------ settings (REQ-670)

    async def get_settings(self) -> dict:
        return settings.load(_settings_path())

    async def set_settings(self, data) -> dict:
        return settings.save(_settings_path(), data)

    # ------------------------------------------------------------ updates (spec 008)

    async def get_update_state(self) -> dict:
        return _update_state

    async def check_update(self, force: bool = False) -> dict:
        global _update_state
        st = _update_state
        try:
            test = _test_channel()
            same_channel = st.get("channel") == ("test" if test else "stable")
            if not force and same_channel and st.get("checked_at") \
                    and time.time() - st["checked_at"] < updater.CACHE_SECONDS:
                return st
            cache = getattr(self, "http_cache", None)
            loop = asyncio.get_running_loop()
            _update_state = await loop.run_in_executor(
                None, lambda: updater.check(PLUGIN_DIR, test_channel=test, cache=cache))
        except Exception as e:  # never reject: the UI shows the reason
            decky.logger.exception("check_update failed")
            _update_state = {**st, "checked": True, "available": False, "error": _err(e)}
        return _update_state

    async def install_update(self) -> dict:
        global _installing
        if _installing:  # REQ-637
            return {"ok": False, "error": "busy"}
        _installing = True
        try:
            test = _test_channel()
            cache = getattr(self, "http_cache", None)
            loop = asyncio.get_running_loop()
            version = await loop.run_in_executor(
                None, lambda: updater.install(PLUGIN_DIR, test_channel=test, cache=cache, rollback_dir=_rollback_dir()))
        except Exception as e:
            decky.logger.exception("install_update failed")
            return {"ok": False, "error": _err(e)}
        finally:
            _installing = False
        decky.logger.info("updated to %s; restarting Decky", version)
        log_dir = getattr(decky, "DECKY_PLUGIN_LOG_DIR", None) or "/tmp"
        updater.schedule_decky_restart(os.path.join(log_dir, "restart.log"))  # REQ-636
        return {"ok": True, "version": version}

    # ------------------------------------------------------------ rollback & changelog (spec 009)

    async def get_rollback_info(self):
        try:
            return updater.rollback_info(PLUGIN_DIR, _rollback_dir())
        except Exception:
            decky.logger.exception("get_rollback_info failed")
            return None

    async def rollback(self) -> dict:
        global _installing
        if _installing:  # REQ-712: shares the install lock
            return {"ok": False, "error": "busy"}
        _installing = True
        try:
            loop = asyncio.get_running_loop()
            version = await loop.run_in_executor(None, lambda: updater.rollback(PLUGIN_DIR, _rollback_dir()))
        except Exception as e:
            decky.logger.exception("rollback failed")
            return {"ok": False, "error": _err(e)}
        finally:
            _installing = False
        decky.logger.info("rolled back to %s; restarting Decky", version)
        log_dir = getattr(decky, "DECKY_PLUGIN_LOG_DIR", None) or "/tmp"
        updater.schedule_decky_restart(os.path.join(log_dir, "restart.log"))
        return {"ok": True, "version": version}

    async def get_changelog(self) -> str:
        try:
            with open(os.path.join(PLUGIN_DIR, "CHANGELOG.md"), encoding="utf-8", errors="replace") as f:
                return f.read(CHANGELOG_MAX)
        except OSError:
            return ""

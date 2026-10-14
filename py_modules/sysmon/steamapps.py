"""Steam library lookup: AppID -> game name from appmanifest files (spec 006)."""

import os
import re
from typing import Dict, List, Optional

from .fsutil import read_str

LIBRARY_PATH = re.compile(r'"path"\s+"([^"]+)"')
MANIFEST_NAME = re.compile(r'"name"\s+"([^"]*)"')


def default_steam_dirs(home: str) -> List[str]:
    return [
        os.path.join(home, ".local", "share", "Steam"),
        os.path.join(home, ".steam", "steam"),
    ]


class SteamLibrary:
    def __init__(self, root: str = "/", steam_dirs: Optional[List[str]] = None):
        self.root = root
        self.steam_dirs = steam_dirs if steam_dirs is not None else default_steam_dirs(os.path.expanduser("~"))
        self._libraries: Optional[List[str]] = None
        self._names: Dict[int, Optional[str]] = {}

    def _p(self, path: str) -> str:
        return os.path.join(self.root, path.lstrip("/\\"))

    def _library_dirs(self) -> List[str]:
        if self._libraries is None:
            libs: List[str] = []
            for steam in self.steam_dirs:
                libs.append(steam)
                vdf = read_str(self._p(os.path.join(steam, "steamapps", "libraryfolders.vdf"))) or ""
                libs.extend(m.replace("\\\\", "\\") for m in LIBRARY_PATH.findall(vdf))
            seen = set()
            unique = []
            for lib in libs:
                real = os.path.normpath(lib)
                if real not in seen:
                    seen.add(real)
                    unique.append(real)
            self._libraries = unique
        return self._libraries

    def game_name(self, app_id: int) -> Optional[str]:
        if app_id in self._names:
            return self._names[app_id]
        name = None
        if 0 < app_id < 2 ** 32:  # non-Steam shortcuts use 64-bit game IDs
            for lib in self._library_dirs():
                text = read_str(self._p(os.path.join(lib, "steamapps", f"appmanifest_{app_id}.acf")))
                if text:
                    match = MANIFEST_NAME.search(text)
                    if match and match.group(1):
                        name = match.group(1)
                        break
        self._names[app_id] = name
        return name

import os
import unittest

from fakefs import FakeFS
from sysmon.processes import ProcessSampler
from sysmon.steamapps import SteamLibrary
from test_processes import Clock, stat_line

HOME = "home/deck"
STEAM = f"/{HOME}/.local/share/Steam"
GOW = 2322010


class GameGroupingTest(unittest.TestCase):  # spec 006
    def setUp(self):
        self.fs = FakeFS()
        self.fs.write("proc/meminfo", "MemTotal:       16777216 kB\n")
        # Library: manifest lives in a second library listed in libraryfolders.vdf (AC-2)
        self.fs.write(f"{HOME}/.local/share/Steam/steamapps/libraryfolders.vdf",
                      '"libraryfolders"\n{\n  "0"\n  {\n    "path"\t\t"/home/deck/.local/share/Steam"\n  }\n'
                      '  "1"\n  {\n    "path"\t\t"/run/media/deck/SD/SteamLibrary"\n  }\n}\n')
        self.fs.write(f"run/media/deck/SD/SteamLibrary/steamapps/appmanifest_{GOW}.acf",
                      f'"AppState"\n{{\n\t"appid"\t\t"{GOW}"\n\t"name"\t\t"God of War Ragnarök"\n}}\n')

        # pid, name, ppid, rss_pages, cmdline, environ (None = unreadable)
        self.procs = [
            (1000, "steam", 1, 51200, b"/home/deck/.local/share/Steam/ubuntu12_32/steam\0", b"HOME=/home/deck\0"),
            (2000, "reaper", 1000, 256, b"/home/deck/.local/share/Steam/ubuntu12_32/reaper\0SteamLaunch\0AppId=2322010\0--\0", b"HOME=/home/deck\0"),
            (2100, "GoWR.exe", 2000, 1835008, b"S:\\common\\God of War Ragnarok\\GoWR.exe\0", b"SteamAppId=2322010\0SteamGameId=2322010\0"),
            (2200, "wineserver", 2000, 2560, b"/usr/bin/wineserver\0", b"SteamAppId=2322010\0"),
            (2300, "xalia.exe", 2100, 5120, b"C:\\windows\\system32\\xalia.exe\0", None),  # inherits from GoWR.exe
            (3000, "steamwebhelper", 1000, 25600, b"/x/steamwebhelper --type=renderer\0", b""),
            (3001, "steamwebhelper", 1000, 25600, b"/x/steamwebhelper --type=gpu\0", b""),
            # Non-Steam shortcut: SteamAppId=0, 64-bit SteamGameId (AC-3)
            (4000, "emu.exe", 1000, 51200, b"Z:\\emus\\emu.exe\0", b"SteamAppId=0\0SteamGameId=12345678901234567890\0"),
            (4001, "helper.exe", 4000, 2560, b"Z:\\emus\\helper.exe\0", b"SteamGameId=12345678901234567890\0"),
        ]
        for pid, name, ppid, rss, cmdline, environ in self.procs:
            self.fs.write(f"proc/{pid}/stat", stat_line(pid, name, ppid, 0, rss))
            self.write_bytes(f"proc/{pid}/cmdline", cmdline)
            if environ is not None:
                self.write_bytes(f"proc/{pid}/environ", environ)

        self.clock = Clock()
        self.sampler = ProcessSampler(root=self.fs.root, clock=self.clock, steam_dirs=[STEAM])
        self.sampler.clk_tck = 100
        self.sampler.page_size = 4096
        self.sampler.cpu_count = 4
        self.sampler.sample(group="app")
        self.clock.t += 1  # 400 ticks available
        for pid, name, ppid, rss, _, _ in self.procs:
            ticks = {2100: 200, 2200: 20, 2300: 4}.get(pid, 0)
            self.fs.write(f"proc/{pid}/stat", stat_line(pid, name, ppid, ticks, rss))

    def tearDown(self):
        self.fs.cleanup()

    def write_bytes(self, rel, data):
        path = self.fs.write(rel, "")
        with open(path, "wb") as f:
            f.write(data)

    def items(self, group="app"):
        return {i["key"]: i for i in self.sampler.sample("cpu", True, 100, False, group)["processes"]}

    def test_game_group(self):  # AC-1, AC-2
        game = self.items()[f"app:{GOW}"]
        self.assertEqual(game["kind"], "game")
        self.assertEqual(game["app_id"], GOW)
        self.assertEqual(game["name"], "God of War Ragnarök")
        self.assertEqual(game["count"], 4)  # reaper, GoWR.exe, wineserver, xalia.exe
        self.assertEqual(game["pid"], 2100)  # identity from the process using most RAM
        self.assertEqual(game["cpu"], 56.0)  # (200 + 20 + 4) / 400
        self.assertEqual([m["pid"] for m in game["members"]], [2100, 2200, 2300, 2000])

    def test_non_steam_shortcut_uses_heaviest_process_name(self):  # AC-3
        items = self.items()
        shortcut = items["app:12345678901234567890"]
        self.assertEqual((shortcut["kind"], shortcut["name"], shortcut["count"]), ("game", "emu.exe", 2))

    def test_other_processes_grouped_by_name(self):  # AC-4
        items = self.items()
        self.assertEqual(items["name:steamwebhelper"]["kind"], "group")
        self.assertEqual(items["name:steamwebhelper"]["count"], 2)
        self.assertEqual(items["pid:1000"]["kind"], "process")
        self.assertIsNone(items["pid:1000"]["app_id"])

    def test_bool_group_is_backward_compatible(self):  # AC-5
        by_name = self.items(True)
        self.assertNotIn(f"app:{GOW}", by_name)
        self.assertIn("name:steamwebhelper", by_name)
        flat = self.items(False)
        self.assertEqual(len(flat), len(self.procs))
        self.assertEqual(flat["pid:2300"]["app_id"], GOW)  # inherited even when not grouping
        self.assertEqual(flat["pid:2300"]["kind"], "process")


class SteamLibraryTest(unittest.TestCase):
    def test_missing_steam_and_unknown_ids(self):
        fs = FakeFS()
        try:
            lib = SteamLibrary(fs.root, [STEAM])
            self.assertIsNone(lib.game_name(GOW))
            self.assertIsNone(lib.game_name(2 ** 40))
            self.assertIsNone(lib.game_name(0))
        finally:
            fs.cleanup()

    def test_manifest_in_main_library(self):
        fs = FakeFS()
        try:
            fs.write(os.path.join(HOME, ".local/share/Steam/steamapps/appmanifest_570.acf"), '"AppState"\n{\n\t"name"\t\t"Dota 2"\n}\n')
            self.assertEqual(SteamLibrary(fs.root, [STEAM]).game_name(570), "Dota 2")
        finally:
            fs.cleanup()


if __name__ == "__main__":
    unittest.main()

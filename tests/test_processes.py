import unittest

from fakefs import FakeFS
from sysmon.processes import ProcessSampler


def stat_line(pid, comm, ppid, ticks, rss_pages, state="S", threads=1, starttime=1000):
    # Fields 3..24 of /proc/[pid]/stat; utime=ticks, stime=0
    fields = [state, ppid, pid, pid, 0, -1, 4194560, 0, 0, 0, 0, ticks, 0, 0, 0, 20, 0,
              threads, 0, starttime, 1000000, rss_pages]
    return f"{pid} ({comm}) " + " ".join(str(f) for f in fields) + "\n"


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class ProcessSamplerTest(unittest.TestCase):
    def setUp(self):
        self.fs = FakeFS()
        self.fs.write("proc/meminfo", "MemTotal:       16777216 kB\n")
        self.add(1, "systemd", 0, 0, 1024, b"/usr/lib/systemd/systemd\0--switched-root\0")
        self.add(2, "kthreadd", 0, 0, 0, b"")
        self.add(30, "kworker/0:1", 2, 0, 0, b"")
        self.add(400, "gamescope", 1, 100, 25600, b"/usr/bin/gamescope\0-e\0")
        self.add(500, "game.exe", 400, 50, 262144, b"C:\\Games\\game.exe\0-dx12\0")
        self.add(600, "Zeta proc", 1, 10, 512, b"")
        self.clock = Clock()
        self.sampler = ProcessSampler(root=self.fs.root, clock=self.clock)
        self.sampler.clk_tck = 100
        self.sampler.page_size = 4096
        self.sampler.cpu_count = 4

    def tearDown(self):
        self.fs.cleanup()

    def add(self, pid, comm, ppid, ticks, rss_pages, cmdline, starttime=1000):
        self.fs.write(f"proc/{pid}/stat", stat_line(pid, comm, ppid, ticks, rss_pages, starttime=starttime))
        path = self.fs.write(f"proc/{pid}/cmdline", "")
        with open(path, "wb") as f:
            f.write(cmdline)

    def by_pid(self, result):
        return {p["pid"]: p for p in result["processes"]}

    def test_cpu_percent_is_delta_over_machine(self):  # AC-1
        first = self.by_pid(self.sampler.sample(limit=100))
        self.assertEqual(first[400]["cpu"], 0.0)
        # 2 s later: gamescope +400 ticks, game +200 ticks; 4 cpus * 100 Hz * 2 s = 800 ticks
        self.clock.t += 2
        self.add(400, "gamescope", 1, 500, 25600, b"/usr/bin/gamescope\0")
        self.add(500, "game.exe", 400, 250, 262144, b"C:\\Games\\game.exe\0")
        procs = self.by_pid(self.sampler.sample(limit=100))
        self.assertEqual(procs[400]["cpu"], 50.0)
        self.assertEqual(procs[500]["cpu"], 25.0)
        self.assertEqual(procs[1]["cpu"], 0.0)

    def test_names_and_memory(self):  # AC-2, FR-3, FR-4
        procs = self.by_pid(self.sampler.sample(limit=100))
        self.assertEqual(procs[500]["name"], "game.exe")
        self.assertEqual(procs[500]["cmd"], "C:\\Games\\game.exe -dx12")
        self.assertEqual(procs[500]["mem_mb"], 1024.0)
        self.assertEqual(procs[500]["mem_percent"], 6.2)
        self.assertEqual(procs[1]["name"], "systemd")
        self.assertEqual(procs[600]["name"], "Zeta proc")  # empty cmdline falls back to comm

    def test_kernel_threads_hidden_by_default(self):  # AC-3
        result = self.sampler.sample(limit=100)
        self.assertEqual(set(self.by_pid(result)), {1, 400, 500, 600})
        self.assertEqual(result["total"], 4)
        result = self.sampler.sample(limit=100, include_kernel=True)
        self.assertEqual(result["total"], 6)

    def test_sorting_and_limit(self):  # AC-4
        names = [p["name"] for p in self.sampler.sample("name", False, 100)["processes"]]
        self.assertEqual(names, ["game.exe", "gamescope", "systemd", "Zeta proc"])
        names = [p["name"] for p in self.sampler.sample("name", True, 2)["processes"]]
        self.assertEqual(names, ["Zeta proc", "systemd"])
        mem = [p["pid"] for p in self.sampler.sample("mem", True, 100)["processes"]]
        self.assertEqual(mem, [500, 400, 1, 600])
        mem = [p["pid"] for p in self.sampler.sample("mem", False, 100)["processes"]]
        self.assertEqual(mem, [600, 1, 400, 500])
        result = self.sampler.sample("cpu", True, 2)
        self.assertEqual((result["total"], result["shown"], len(result["processes"])), (4, 2, 2))

    def test_exited_process_is_dropped(self):  # AC-5
        self.sampler.sample(limit=100)
        self.fs.write("proc/600/stat", "")  # unreadable/empty: process gone
        self.clock.t += 1
        result = self.sampler.sample(limit=100)
        self.assertNotIn(600, self.by_pid(result))
        self.assertNotIn((600, 1000), self.sampler._names)

    def test_pid_reuse_does_not_inherit_ticks(self):
        self.sampler.sample(limit=100)
        self.clock.t += 1
        self.add(600, "newproc", 1, 5000, 10, b"/bin/newproc\0", starttime=9999)
        procs = self.by_pid(self.sampler.sample(limit=100))
        self.assertEqual(procs[600]["name"], "newproc")
        self.assertEqual(procs[600]["cpu"], 0.0)

    def test_comm_with_parentheses(self):
        self.add(700, "weird) (name", 1, 0, 1, b"")
        procs = self.by_pid(self.sampler.sample(limit=100))
        self.assertEqual(procs[700]["name"], "weird) (name")


class GroupingTest(unittest.TestCase):
    def setUp(self):
        self.fs = FakeFS()
        self.fs.write("proc/meminfo", "MemTotal:       16777216 kB\n")
        self.clock = Clock()
        self.sampler = ProcessSampler(root=self.fs.root, clock=self.clock)
        self.sampler.clk_tck = 100
        self.sampler.page_size = 4096
        self.sampler.cpu_count = 4
        procs = [(1301, 10, 25600), (1300, 40, 51200), (1305, 0, 12800), (500, 80, 262144), (600, 0, 256)]
        for pid, _, rss in procs:
            self.write(pid, rss, 0)
        self.sampler.sample(group=True)
        self.clock.t += 1  # 400 ticks available per second
        for pid, ticks, rss in procs:
            self.write(pid, rss, ticks)

    def tearDown(self):
        self.fs.cleanup()

    def write(self, pid, rss, ticks):
        names = {500: "game.exe", 600: "bash"}
        name = names.get(pid, "steamwebhelper")
        self.fs.write(f"proc/{pid}/stat", stat_line(pid, name, 1, ticks, rss))
        path = self.fs.write(f"proc/{pid}/cmdline", "")
        with open(path, "wb") as f:
            f.write(f"/usr/bin/{name}\0".encode())

    def test_groups_sum_usage(self):  # AC-1
        items = {i["name"]: i for i in self.sampler.sample("cpu", True, 100, False, True)["processes"]}
        web = items["steamwebhelper"]
        self.assertEqual((web["key"], web["count"], web["pid"]), ("name:steamwebhelper", 3, 1300))
        self.assertEqual(web["cpu"], 12.5)  # (10 + 40 + 0) / 400
        self.assertEqual(web["mem_mb"], 350.0)
        self.assertEqual([m["pid"] for m in web["members"]], [1300, 1301, 1305])

    def test_single_process_group(self):  # AC-2
        items = {i["name"]: i for i in self.sampler.sample("cpu", True, 100, False, True)["processes"]}
        self.assertEqual((items["bash"]["count"], items["bash"]["members"]), (1, []))
        self.assertEqual(items["bash"]["key"], "pid:600")

    def test_sort_and_limit_apply_to_groups(self):  # AC-3
        result = self.sampler.sample("mem", False, 2, False, True)
        self.assertEqual([i["name"] for i in result["processes"]], ["bash", "steamwebhelper"])
        self.assertEqual((result["total"], result["shown"], result["process_count"]), (3, 2, 5))
        names = [i["name"] for i in self.sampler.sample("cpu", True, 100, False, True)["processes"]]
        self.assertEqual(names, ["game.exe", "steamwebhelper", "bash"])

    def test_flat_mode_keys(self):  # AC-4
        result = self.sampler.sample("cpu", True, 100, False, False)
        self.assertEqual(result["total"], 5)
        self.assertTrue(all(i["key"] == f"pid:{i['pid']}" and i["count"] == 1 for i in result["processes"]))


if __name__ == "__main__":
    unittest.main()

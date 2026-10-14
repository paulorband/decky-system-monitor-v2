import unittest

from fakefs import FakeFS, build_ally_x
from sysmon.metrics import MetricsCollector


class MetricsTest(unittest.TestCase):
    def setUp(self):
        self.fs = FakeFS()
        build_ally_x(self.fs)
        self.collector = MetricsCollector(root=self.fs.root)

    def tearDown(self):
        self.fs.cleanup()

    def test_cpu_first_call_uses_since_boot(self):  # AC-2
        cpu = self.collector.snapshot()["cpu"]
        self.assertEqual(cpu["usage"], 20.0)
        self.assertEqual(cpu["per_core"], [20.0, 20.0])
        self.assertEqual(cpu["cores"], 2)

    def test_cpu_usage_is_delta(self):  # AC-1
        self.collector.snapshot()
        self.fs.write("proc/stat", "cpu  200 0 200 900 0 0 0 0 0 0\n"
                                   "cpu0 150 0 150 400 0 0 0 0 0 0\n"
                                   "cpu1 50 0 50 500 0 0 0 0 0 0\n")
        cpu = self.collector.snapshot()["cpu"]
        self.assertEqual(cpu["usage"], 66.7)
        self.assertEqual(cpu["per_core"], [100.0, 0.0])

    def test_cpu_details(self):  # AC-3
        cpu = self.collector.snapshot()["cpu"]
        self.assertEqual(cpu["temp_c"], 67.5)
        self.assertEqual(cpu["freq_mhz"], 3000)
        self.assertEqual(cpu["freq_max_mhz"], 5100)
        self.assertEqual(cpu["model"], "AMD Ryzen Z1 Extreme")
        self.assertEqual(cpu["load_avg"], [1.5, 1.0, 0.5])

    def test_gpu_amd(self):  # AC-4
        gpu = self.collector.snapshot()["gpu"]
        self.assertEqual(gpu, {
            "name": "AMD", "usage": 92, "temp_c": 64.0, "freq_mhz": 2500,
            "vram_used_mb": 512, "vram_total_mb": 4096,
            "gtt_used_mb": 900, "gtt_total_mb": 12000, "power_w": 17.3,
        })

    def test_memory(self):
        mem = self.collector.snapshot()["memory"]
        self.assertEqual(mem["total_mb"], 23438)
        self.assertEqual(mem["used_mb"], 7812)
        self.assertEqual(mem["percent"], 33.3)
        self.assertEqual(mem["swap_used_mb"], 1953)
        self.assertEqual(mem["swap_percent"], 25.0)

    def test_battery_ignores_controller_and_derives_power(self):  # AC-5
        bat = self.collector.snapshot()["battery"]
        self.assertEqual(bat["percent"], 81)
        self.assertEqual(bat["power_w"], 20.0)
        self.assertEqual(bat["time_left_min"], 192)  # 4.0 Ah / 1.25 A
        self.assertEqual(bat["health_percent"], 96.2)

    def test_fans_skip_generic_acpi_fan(self):  # AC-8
        self.assertEqual(self.collector.snapshot()["fans"], [
            {"label": "cpu_fan", "rpm": 3400},
            {"label": "gpu_fan", "rpm": 3100},
        ])

    def test_fans_fall_back_to_acpi_fan(self):  # AC-8
        fs = FakeFS()
        try:
            fs.write("sys/class/hwmon/hwmon0/name", "acpi_fan")
            fs.write("sys/class/hwmon/hwmon0/fan1_input", 2000)
            fans = MetricsCollector(root=fs.root).snapshot()["fans"]
            self.assertEqual(fans, [{"label": None, "rpm": 2000}])
        finally:
            fs.cleanup()

    def test_unlabeled_platform_fan(self):  # AC-9: Steam Deck style driver without fan1_label
        fs = FakeFS()
        try:
            fs.write("sys/class/hwmon/hwmon2/name", "steamdeck_hwmon")
            fs.write("sys/class/hwmon/hwmon2/fan1_input", 3200)
            fans = MetricsCollector(root=fs.root).snapshot()["fans"]
            self.assertEqual(fans, [{"label": None, "rpm": 3200}])
        finally:
            fs.cleanup()

    def test_uptime(self):
        self.assertEqual(self.collector.snapshot()["uptime_s"], 3600.25)

    def test_missing_hardware_degrades(self):  # AC-6
        fs = FakeFS()
        try:
            fs.write("proc/stat", "cpu  1 0 1 8 0 0 0 0\n")
            snap = MetricsCollector(root=fs.root).snapshot()
            self.assertIsNone(snap["gpu"])
            self.assertIsNone(snap["battery"])
            self.assertEqual(snap["fans"], [])
            self.assertIsNone(snap["cpu"]["temp_c"])
            self.assertIsNone(snap["memory"]["percent"])
        finally:
            fs.cleanup()


if __name__ == "__main__":
    unittest.main()

"""Builds a fake root filesystem (/proc, /sys) in a temp dir for backend tests."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py_modules"))


class FakeFS:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def write(self, rel: str, content) -> str:
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
        return path

    def mkdir(self, rel: str) -> str:
        path = os.path.join(self.root, rel)
        os.makedirs(path, exist_ok=True)
        return path

    def cleanup(self):
        self._tmp.cleanup()


def build_ally_x(fs: FakeFS) -> None:
    """A trimmed-down ROG Ally X running Bazzite."""
    fs.write("proc/stat", "cpu  100 0 100 800 0 0 0 0 0 0\n"
                          "cpu0 50 0 50 400 0 0 0 0 0 0\n"
                          "cpu1 50 0 50 400 0 0 0 0 0 0\n"
                          "intr 1 2 3\n")
    fs.write("proc/cpuinfo", "processor\t: 0\nmodel name\t: AMD Ryzen Z1 Extreme\n")
    fs.write("proc/loadavg", "1.50 1.00 0.50 2/700 1234\n")
    fs.write("proc/uptime", "3600.25 7000.00\n")
    fs.write("proc/meminfo", "MemTotal:       24000000 kB\n"
                             "MemFree:         1000000 kB\n"
                             "MemAvailable:   16000000 kB\n"
                             "SwapTotal:       8000000 kB\n"
                             "SwapFree:        6000000 kB\n")
    for cpu, freq in (("cpu0", 2000000), ("cpu1", 4000000)):
        fs.write(f"sys/devices/system/cpu/{cpu}/cpufreq/scaling_cur_freq", freq)
        fs.write(f"sys/devices/system/cpu/{cpu}/cpufreq/cpuinfo_max_freq", 5100000)
    fs.mkdir("sys/devices/system/cpu/cpufreq")  # must be ignored

    # CPU hwmon (k10temp) with Tctl on temp1 and Tccd1 on temp3
    fs.write("sys/class/hwmon/hwmon3/name", "k10temp")
    fs.write("sys/class/hwmon/hwmon3/temp3_input", 55000)
    fs.write("sys/class/hwmon/hwmon3/temp3_label", "Tccd1")
    fs.write("sys/class/hwmon/hwmon3/temp1_input", 67500)
    fs.write("sys/class/hwmon/hwmon3/temp1_label", "Tctl")
    # Asus platform fan
    fs.write("sys/class/hwmon/hwmon6/name", "asus")
    fs.write("sys/class/hwmon/hwmon6/fan1_input", 3400)
    fs.write("sys/class/hwmon/hwmon6/fan1_label", "cpu_fan")

    # amdgpu
    dev = "sys/class/drm/card1/device"
    fs.write(f"{dev}/vendor", "0x1002")
    fs.write(f"{dev}/gpu_busy_percent", 92)
    fs.write(f"{dev}/mem_info_vram_used", 512 * 1048576)
    fs.write(f"{dev}/mem_info_vram_total", 4096 * 1048576)
    fs.write(f"{dev}/mem_info_gtt_used", 900 * 1048576)
    fs.write(f"{dev}/mem_info_gtt_total", 12000 * 1048576)
    fs.write(f"{dev}/hwmon/hwmon5/temp1_input", 64000)
    fs.write(f"{dev}/hwmon/hwmon5/freq1_input", 2500000000)
    fs.write(f"{dev}/hwmon/hwmon5/power1_input", 17300000)
    fs.write("sys/class/drm/card1-eDP-1/status", "connected")  # connector, must be ignored

    # Controller battery (ignored) + system battery
    fs.write("sys/class/power_supply/hid-xbox-battery/type", "Battery")
    fs.write("sys/class/power_supply/hid-xbox-battery/scope", "Device")
    fs.write("sys/class/power_supply/hid-xbox-battery/capacity", 10)
    bat = "sys/class/power_supply/BAT0"
    fs.write(f"{bat}/type", "Battery")
    fs.write(f"{bat}/status", "Discharging")
    fs.write(f"{bat}/capacity", 81)
    fs.write(f"{bat}/voltage_now", 16000000)
    fs.write(f"{bat}/current_now", 1250000)  # 1.25 A * 16 V = 20 W
    fs.write(f"{bat}/charge_now", 4000000)
    fs.write(f"{bat}/charge_full", 5000000)
    fs.write(f"{bat}/charge_full_design", 5200000)
    fs.write("sys/class/power_supply/ACAD/type", "Mains")

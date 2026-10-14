"""System metrics snapshot collected straight from /proc and /sys (spec 001)."""

import os
import time
from typing import Dict, List, Optional, Tuple

from .fsutil import list_dir, pct, read_float, read_int, read_str

CPU_HWMON_NAMES = ("k10temp", "zenpower", "coretemp", "cpu_thermal", "acpitz")
CPU_TEMP_LABELS = ("tctl", "tdie", "package id 0", "cpu")
VENDOR_NAMES = {"0x1002": "AMD", "0x8086": "Intel", "0x10de": "NVIDIA"}
GENERIC_FAN_HWMON = ("acpi_fan",)

# (busy, total) jiffies per cpu line; index 0 is the aggregate "cpu" line
CpuTimes = List[Tuple[int, int]]


def _parse_proc_stat(text: str) -> CpuTimes:
    times: CpuTimes = []
    for line in text.splitlines():
        if not line.startswith("cpu"):
            break
        fields = [int(x) for x in line.split()[1:9]]
        fields += [0] * (8 - len(fields))
        idle = fields[3] + fields[4]  # idle + iowait
        total = sum(fields)
        times.append((total - idle, total))
    return times


def _usage(prev: Tuple[int, int], cur: Tuple[int, int]) -> float:
    d_busy = cur[0] - prev[0]
    d_total = cur[1] - prev[1]
    if d_total <= 0:
        return 0.0
    return round(max(0.0, min(100.0, d_busy * 100.0 / d_total)), 1)


class MetricsCollector:
    def __init__(self, root: str = "/"):
        self.root = root
        self._prev_cpu: Optional[CpuTimes] = None
        self._discovered = False
        self._hwmon: Dict[str, List[str]] = {}
        self._gpu_dev: Optional[str] = None
        self._gpu_card: Optional[str] = None
        self._gpu_vendor: Optional[str] = None
        self._battery: Optional[str] = None
        self._cpu_model: Optional[str] = None
        self._cpu_dirs: List[str] = []

    def _p(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    # ---------------------------------------------------------------- discovery

    def _discover(self) -> None:
        if self._discovered:
            return
        self._discovered = True

        hwmon_root = self._p("sys", "class", "hwmon")
        for entry in list_dir(hwmon_root):
            path = os.path.join(hwmon_root, entry)
            name = read_str(os.path.join(path, "name")) or entry
            self._hwmon.setdefault(name, []).append(path)

        drm_root = self._p("sys", "class", "drm")
        candidates = []
        for entry in list_dir(drm_root):
            if not entry.startswith("card") or "-" in entry:
                continue
            dev = os.path.join(drm_root, entry, "device")
            vendor = read_str(os.path.join(dev, "vendor"))
            if vendor is None:
                continue
            has_busy = os.path.exists(os.path.join(dev, "gpu_busy_percent"))
            candidates.append((not has_busy, entry, dev, vendor))
        if candidates:
            candidates.sort()
            _, card, dev, vendor = candidates[0]
            self._gpu_card = os.path.join(drm_root, card)
            self._gpu_dev = dev
            self._gpu_vendor = vendor

        ps_root = self._p("sys", "class", "power_supply")
        for entry in list_dir(ps_root):
            path = os.path.join(ps_root, entry)
            if read_str(os.path.join(path, "type")) != "Battery":
                continue
            if (read_str(os.path.join(path, "scope")) or "").lower() == "device":
                continue
            self._battery = path
            break

        cpuinfo = read_str(self._p("proc", "cpuinfo")) or ""
        for line in cpuinfo.splitlines():
            if line.lower().startswith("model name"):
                self._cpu_model = line.split(":", 1)[1].strip()
                break

        cpu_root = self._p("sys", "devices", "system", "cpu")
        self._cpu_dirs = [
            os.path.join(cpu_root, e)
            for e in list_dir(cpu_root)
            if e.startswith("cpu") and e[3:].isdigit()
        ]

    # ---------------------------------------------------------------- sections

    def _cpu_temp(self) -> Optional[float]:
        for name in CPU_HWMON_NAMES:
            for path in self._hwmon.get(name, []):
                inputs = [e for e in list_dir(path) if e.startswith("temp") and e.endswith("_input")]
                if not inputs:
                    continue
                chosen = None
                for inp in inputs:
                    label = (read_str(os.path.join(path, inp.replace("_input", "_label"))) or "").lower()
                    if any(label.startswith(lbl) for lbl in CPU_TEMP_LABELS):
                        chosen = inp
                        break
                value = read_int(os.path.join(path, chosen or inputs[0]))
                if value is not None:
                    return round(value / 1000.0, 1)
        return None

    def _cpu(self) -> dict:
        times = _parse_proc_stat(read_str(self._p("proc", "stat")) or "")
        prev = self._prev_cpu
        if not prev or len(prev) != len(times):
            prev = [(0, 0)] * len(times)
        self._prev_cpu = times
        usages = [_usage(p, c) for p, c in zip(prev, times)]

        freqs = [read_int(os.path.join(d, "cpufreq", "scaling_cur_freq")) for d in self._cpu_dirs]
        freqs = [f for f in freqs if f]
        freq_max = None
        if self._cpu_dirs:
            freq_max = read_int(os.path.join(self._cpu_dirs[0], "cpufreq", "cpuinfo_max_freq"))

        load = read_str(self._p("proc", "loadavg"))
        load_avg = None
        if load:
            try:
                load_avg = [float(x) for x in load.split()[:3]]
            except ValueError:
                load_avg = None

        return {
            "usage": usages[0] if usages else None,
            "per_core": usages[1:],
            "temp_c": self._cpu_temp(),
            "freq_mhz": round(sum(freqs) / len(freqs) / 1000) if freqs else None,
            "freq_max_mhz": round(freq_max / 1000) if freq_max else None,
            "cores": max(len(times) - 1, 0) or None,
            "model": self._cpu_model,
            "load_avg": load_avg,
        }

    def _gpu(self) -> Optional[dict]:
        dev = self._gpu_dev
        if not dev:
            return None

        def mb(name: str) -> Optional[int]:
            value = read_int(os.path.join(dev, name))
            return round(value / 1048576) if value is not None else None

        gpu = {
            "name": VENDOR_NAMES.get(self._gpu_vendor or "", self._gpu_vendor),
            "usage": read_int(os.path.join(dev, "gpu_busy_percent")),
            "temp_c": None,
            "freq_mhz": None,
            "vram_used_mb": mb("mem_info_vram_used"),
            "vram_total_mb": mb("mem_info_vram_total"),
            "gtt_used_mb": mb("mem_info_gtt_used"),
            "gtt_total_mb": mb("mem_info_gtt_total"),
            "power_w": None,
        }

        hwmon_dir = os.path.join(dev, "hwmon")
        for entry in list_dir(hwmon_dir):
            path = os.path.join(hwmon_dir, entry)
            temp = read_int(os.path.join(path, "temp1_input"))
            if temp is not None:
                gpu["temp_c"] = round(temp / 1000.0, 1)
            freq = read_int(os.path.join(path, "freq1_input"))
            if freq is not None:
                gpu["freq_mhz"] = round(freq / 1_000_000)
            power = read_int(os.path.join(path, "power1_average"))
            if power is None:
                power = read_int(os.path.join(path, "power1_input"))
            if power is not None:
                gpu["power_w"] = round(power / 1_000_000, 1)
            break

        if gpu["freq_mhz"] is None and self._gpu_card:
            gpu["freq_mhz"] = read_int(os.path.join(self._gpu_card, "gt_cur_freq_mhz"))
        return gpu

    def _memory(self) -> dict:
        info: Dict[str, int] = {}
        for line in (read_str(self._p("proc", "meminfo")) or "").splitlines():
            key, _, rest = line.partition(":")
            try:
                info[key] = int(rest.split()[0])  # kB
            except (ValueError, IndexError):
                continue
        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", info.get("MemFree", 0))
        used = max(total - available, 0)
        swap_total = info.get("SwapTotal", 0)
        swap_used = max(swap_total - info.get("SwapFree", 0), 0)
        return {
            "total_mb": round(total / 1024),
            "used_mb": round(used / 1024),
            "available_mb": round(available / 1024),
            "percent": pct(used, total),
            "swap_total_mb": round(swap_total / 1024),
            "swap_used_mb": round(swap_used / 1024),
            "swap_percent": pct(swap_used, swap_total) if swap_total else 0.0,
        }

    def _battery_info(self) -> Optional[dict]:
        path = self._battery
        if not path:
            return None

        def r(name: str) -> Optional[int]:
            return read_int(os.path.join(path, name))

        status = read_str(os.path.join(path, "status"))
        percent = r("capacity")
        voltage = r("voltage_now")  # uV

        power_uw = r("power_now")
        current = r("current_now")  # uA
        if power_uw is None and current is not None and voltage is not None:
            power_uw = current * voltage / 1_000_000
        power_w = round(abs(power_uw) / 1_000_000, 1) if power_uw is not None else None

        # Prefer energy (uWh) with power; fall back to charge (uAh) with current.
        now, full, full_design, rate = r("energy_now"), r("energy_full"), r("energy_full_design"), power_uw
        if now is None or not rate:
            now, full, full_design, rate = r("charge_now"), r("charge_full"), r("charge_full_design"), current

        time_left = None
        if now is not None and rate:
            rate = abs(rate)
            if status == "Discharging":
                time_left = round(now / rate * 60)
            elif status == "Charging" and full is not None:
                time_left = round(max(full - now, 0) / rate * 60)

        health = pct(full, full_design) if full is not None and full_design else None
        return {
            "percent": percent,
            "status": status,
            "power_w": power_w,
            "time_left_min": time_left,
            "health_percent": health,
        }

    def _fans(self) -> List[dict]:
        fans = []
        generic = []
        for name, paths in sorted(self._hwmon.items()):
            target = generic if name in GENERIC_FAN_HWMON else fans
            for path in paths:
                for entry in list_dir(path):
                    if not (entry.startswith("fan") and entry.endswith("_input")):
                        continue
                    rpm = read_int(os.path.join(path, entry))
                    if rpm is None:
                        continue
                    label = read_str(os.path.join(path, entry.replace("_input", "_label")))
                    target.append({"label": label or name, "rpm": rpm})
        # The generic ACPI fan device mirrors fans a platform driver (asus, steamdeck_hwmon...)
        # already reports, so it only counts when nothing better exists.
        return fans or generic

    # ---------------------------------------------------------------- public

    def snapshot(self) -> dict:
        self._discover()
        uptime = read_float(self._p("proc", "uptime"))
        return {
            "ts": time.time(),
            "uptime_s": uptime,
            "cpu": self._cpu(),
            "gpu": self._gpu(),
            "memory": self._memory(),
            "battery": self._battery_info(),
            "fans": self._fans(),
        }

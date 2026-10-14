"""Per-process CPU and memory sampling from /proc (spec 003)."""

import os
import time
from typing import Dict, List, Optional, Tuple

from .fsutil import read_str

KTHREADD_PID = 2
SORT_KEYS = ("name", "cpu", "mem")
CMD_MAX = 300
MAX_MEMBERS = 50

ProcKey = Tuple[int, int]  # (pid, starttime) uniquely identifies a process across PID reuse


def _sysconf(name: str, fallback: int) -> int:
    try:
        value = os.sysconf(name)
        return value if value > 0 else fallback
    except (AttributeError, ValueError, OSError):
        return fallback


def _parse_stat(text: str) -> Optional[dict]:
    # comm may contain spaces and parentheses, so split around the last ')'
    open_paren = text.find("(")
    close_paren = text.rfind(")")
    if open_paren < 0 or close_paren < 0:
        return None
    fields = text[close_paren + 2:].split()
    if len(fields) < 22:
        return None
    try:
        return {
            "comm": text[open_paren + 1:close_paren],
            "state": fields[0],
            "ppid": int(fields[1]),
            "ticks": int(fields[11]) + int(fields[12]),
            "threads": int(fields[17]),
            "starttime": int(fields[19]),
            "rss_pages": int(fields[21]),
        }
    except ValueError:
        return None


def _name_from_cmdline(raw: Optional[bytes], comm: str) -> Tuple[str, str]:
    if not raw:
        return comm, ""
    args = [a for a in raw.split(b"\0") if a]
    if not args:
        return comm, ""
    argv = [a.decode("utf-8", "replace") for a in args]
    exe = argv[0].replace("\\", "/").rstrip("/").split("/")[-1]
    # Some programs rewrite argv[0] to a long title ("sshd: user@pts/0"); keep comm then.
    if not exe or " " in exe:
        exe = comm
    cmd = " ".join(argv)
    return exe, cmd[:CMD_MAX]


class ProcessSampler:
    def __init__(self, root: str = "/", clock=time.monotonic):
        self.root = root
        self.clock = clock
        self.clk_tck = _sysconf("SC_CLK_TCK", 100)
        self.page_size = _sysconf("SC_PAGE_SIZE", 4096)
        self.cpu_count = os.cpu_count() or 1
        self._prev: Dict[ProcKey, int] = {}
        self._prev_time: Optional[float] = None
        self._names: Dict[ProcKey, Tuple[str, str]] = {}
        self._mem_total_kb: Optional[int] = None

    def _p(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    def _read_cmdline(self, pid: int) -> Optional[bytes]:
        try:
            with open(self._p("proc", str(pid), "cmdline"), "rb") as f:
                return f.read(4096)
        except OSError:
            return None

    def _mem_total(self) -> int:
        if self._mem_total_kb is None:
            for line in (read_str(self._p("proc", "meminfo")) or "").splitlines():
                if line.startswith("MemTotal:"):
                    self._mem_total_kb = int(line.split()[1])
                    break
            else:
                self._mem_total_kb = 0
        return self._mem_total_kb

    def _scan(self) -> List[dict]:
        procs = []
        try:
            entries = os.listdir(self._p("proc"))
        except OSError:
            return procs
        for entry in entries:
            if not entry.isdigit():
                continue
            pid = int(entry)
            text = read_str(self._p("proc", entry, "stat"))
            if not text:
                continue  # exited between listdir and read
            st = _parse_stat(text)
            if st is None:
                continue
            st["pid"] = pid
            procs.append(st)
        return procs

    def sample(
        self,
        sort_key: str = "cpu",
        descending: bool = True,
        limit: int = 40,
        include_kernel: bool = False,
        group: bool = False,
    ) -> dict:
        if sort_key not in SORT_KEYS:
            sort_key = "cpu"
        now = self.clock()
        elapsed = (now - self._prev_time) if self._prev_time is not None else 0.0
        self._prev_time = now
        cpu_scale = 100.0 / (elapsed * self.clk_tck * self.cpu_count) if elapsed > 0 else 0.0
        mem_total_kb = self._mem_total()

        current: Dict[ProcKey, int] = {}
        rows = []
        for st in self._scan():
            key = (st["pid"], st["starttime"])
            current[key] = st["ticks"]
            is_kernel = st["pid"] == KTHREADD_PID or st["ppid"] == KTHREADD_PID
            if is_kernel and not include_kernel:
                continue

            prev_ticks = self._prev.get(key)
            cpu = 0.0
            if prev_ticks is not None and cpu_scale:
                cpu = max(0.0, (st["ticks"] - prev_ticks) * cpu_scale)

            names = self._names.get(key)
            if names is None:
                cmdline = None if is_kernel else self._read_cmdline(st["pid"])
                names = _name_from_cmdline(cmdline, st["comm"])
                self._names[key] = names

            mem_kb = st["rss_pages"] * self.page_size / 1024
            rows.append({
                "pid": st["pid"],
                "name": names[0],
                "cmd": names[1],
                "cpu": round(min(cpu, 100.0), 1),
                "mem_mb": round(mem_kb / 1024, 1),
                "mem_percent": round(mem_kb * 100 / mem_total_kb, 1) if mem_total_kb else None,
                "threads": st["threads"],
                "state": st["state"],
                "ppid": st["ppid"],
            })

        self._prev = current
        for key in list(self._names):
            if key not in current:
                del self._names[key]

        process_count = len(rows)
        items = _group(rows) if group else [_single(r) for r in rows]
        _sort(items, sort_key, descending)

        limit = max(1, int(limit))
        return {
            "total": len(items),
            "shown": min(limit, len(items)),
            "process_count": process_count,
            "cpu_count": self.cpu_count,
            "mem_total_mb": round(mem_total_kb / 1024) if mem_total_kb else None,
            "processes": items[:limit],
        }


def _sort(items: List[dict], sort_key: str, descending: bool) -> None:
    if sort_key == "name":
        items.sort(key=lambda r: (r["name"].lower(), r["pid"]), reverse=descending)
    elif sort_key == "cpu":
        items.sort(key=lambda r: (r["cpu"], r["mem_mb"]), reverse=descending)
    else:
        items.sort(key=lambda r: (r["mem_mb"], r["cpu"]), reverse=descending)


def _single(row: dict) -> dict:
    return {**row, "key": f"pid:{row['pid']}", "count": 1, "members": []}


def _group(rows: List[dict]) -> List[dict]:
    """Merge processes sharing a name into one item with summed usage (spec 005)."""
    by_name: Dict[str, List[dict]] = {}
    for row in rows:
        by_name.setdefault(row["name"], []).append(row)

    items = []
    for name, members in by_name.items():
        if len(members) == 1:
            items.append(_single(members[0]))
            continue
        main = min(members, key=lambda r: r["pid"])
        mem_percents = [m["mem_percent"] for m in members if m["mem_percent"] is not None]
        members.sort(key=lambda r: (r["cpu"], r["mem_mb"]), reverse=True)
        items.append({
            **main,
            "key": f"name:{name}",
            "count": len(members),
            "cpu": round(min(sum(m["cpu"] for m in members), 100.0), 1),
            "mem_mb": round(sum(m["mem_mb"] for m in members), 1),
            "mem_percent": round(sum(mem_percents), 1) if mem_percents else None,
            "threads": sum(m["threads"] for m in members),
            "members": members[:MAX_MEMBERS],
        })
    return items

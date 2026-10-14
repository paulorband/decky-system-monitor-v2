"""Small, exception-free helpers for reading /proc and /sys files."""

import os
from typing import Optional


def read_str(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except (OSError, ValueError):
        return None


def read_int(path: str) -> Optional[int]:
    value = read_str(path)
    if value is None:
        return None
    try:
        return int(value.split()[0])
    except (ValueError, IndexError):
        return None


def read_float(path: str) -> Optional[float]:
    value = read_str(path)
    if value is None:
        return None
    try:
        return float(value.split()[0])
    except (ValueError, IndexError):
        return None


def list_dir(path: str) -> list:
    try:
        return sorted(os.listdir(path))
    except OSError:
        return []


def pct(part: float, whole: float) -> Optional[float]:
    if not whole:
        return None
    return round(max(0.0, min(100.0, part * 100.0 / whole)), 1)

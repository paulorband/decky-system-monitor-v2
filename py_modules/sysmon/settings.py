"""Backend-owned, sanitized settings (specs/008-auto-atualizacao, REQ-670).

Only what the backend must trust itself lives here: whether to check for updates and the test channel
(REQ-655: the channel is never taken from a frontend parameter). UI preferences stay in localStorage.
"""

import json
import os
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {
    "auto_check": True,
    "test_channel": False,
}


def sanitize(raw: Any) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return out
    for key in DEFAULTS:
        if isinstance(raw.get(key), bool):
            out[key] = raw[key]
    return out


def load(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            return sanitize(json.load(f))
    except (OSError, ValueError):
        return sanitize(None)


def save(path: str, data: Any) -> Dict[str, Any]:
    clean = sanitize(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean, f)
    os.replace(tmp, path)
    return clean

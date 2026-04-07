#!/usr/bin/env python3
"""
Legacy compatibility entrypoint for Vitreos.

Canonical runtime:
    python src/main.py

This shim exists so older scripts or shortcuts that still call
`vitreos_main.py` continue to work.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict


def _load_settings(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main() -> int:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(root_dir, "config", "settings.json")
    settings = _load_settings(settings_path)
    webhook_url = (
        settings.get("discord", {}).get("webhook_url", "")
        or settings.get("webhook_url", "")
    )

    print("[DEPRECATED] `vitreos_main.py` now forwards to `src/main.py`.")

    try:
        from src.main import run_cli_loop
    except Exception as exc:
        print(f"[ERROR] Could not import `src/main.py`: {exc}", file=sys.stderr)
        return 1

    run_cli_loop(settings_path, webhook_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

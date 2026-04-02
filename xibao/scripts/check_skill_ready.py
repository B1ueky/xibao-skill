#!/usr/bin/env python3
"""Quick local readiness check for the xibao poster skill."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    print("== xibao skill readiness check ==")
    ok = True

    # 1) Core files
    required_files = [
        ROOT / "SKILL.md",
        ROOT / "scripts" / "generate_poster.py",
    ]
    for file_path in required_files:
        exists = file_path.is_file()
        print(f"[{'OK' if exists else 'FAIL'}] file: {file_path.relative_to(ROOT.parent)}")
        ok = ok and exists

    # 2) Python dependency
    pillow_ok = has_module("PIL")
    print(f"[{'OK' if pillow_ok else 'FAIL'}] python module: PIL (Pillow)")
    if not pillow_ok:
        ok = False
        print("       hint: install Pillow in your runtime before generating posters")

    # 3) Assets (at least one candidate per slot)
    asset_candidates = {
        "badge": ["he_badge.png", "贺章.png"],
        "top_wave": ["xianguyun_top.png", "金色祥云波浪带上.png"],
        "bottom_wave": ["xianguyun_bot.png", "金色祥云波浪带下.png"],
    }
    for key, names in asset_candidates.items():
        found = next((n for n in names if (ASSETS / n).is_file()), None)
        exists = found is not None
        print(f"[{'OK' if exists else 'FAIL'}] asset {key}: {found or '/'.join(names)}")
        ok = ok and exists

    print("\nResult:", "READY" if ok else "NOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""检查双模型权重文件存在且可被 Ultralytics 加载。"""
from __future__ import annotations

from pathlib import Path

import yaml
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent


def main() -> int:
    with (ROOT / "config.yaml").open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    paths = {
        "worker": ROOT / cfg["models"]["worker"],
        "machinery": ROOT / cfg["models"]["machinery"],
    }
    for tag, p in paths.items():
        if not p.is_file():
            print(f"FAIL missing: {tag} -> {p}")
            return 1
        mb = p.stat().st_size / (1024 * 1024)
        print(f"OK file {tag}: {p.name} ({mb:.1f} MB)")

    w = YOLO(str(paths["worker"]))
    m = YOLO(str(paths["machinery"]))
    print("worker classes:", w.names)
    print("machinery classes:", m.names)
    print("ALL_WEIGHTS_LOADED_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""在服务器上自检：RTMP 字符串 → 3 张 JPG 落盘。"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rtmp_pipeline import analyze_rtmp_stream


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stream_url", nargs="?", default="rtmp://10.148.1.22/live/test")
    ap.add_argument("-o", "--out", type=Path, default=ROOT / "output" / "mcp_test")
    args = ap.parse_args()

    result = analyze_rtmp_stream(args.stream_url)
    if not result.get("ok"):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in result["images"]:
        path = out_dir / item["filename"]
        path.write_bytes(base64.b64decode(item["base64"]))
        print(f"已保存 {path}")

    print(f"format={result['format']} count={result['image_count']}")
    print(f"worker={result['counts']['worker']} machinery={result['counts']['machinery']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

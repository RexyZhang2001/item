#!/usr/bin/env python3
"""从 RTMP 流定时截图，保存到当前目录（或指定目录）。"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

DEFAULT_RTMP = "rtmp://10.148.1.22/live/test"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RTMP 流自动截图")
    p.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_RTMP,
        help=f"RTMP 地址（默认: {DEFAULT_RTMP}）",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("."),
        help="截图保存目录（默认: 当前目录）",
    )
    p.add_argument(
        "-i",
        "--interval",
        type=float,
        default=5.0,
        help="截图间隔（秒），默认 5",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="只截一张图后退出",
    )
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=0,
        help="最多截图张数，0 表示不限制（需配合 Ctrl+C 结束）",
    )
    p.add_argument(
        "--prefix",
        default="snapshot",
        help="文件名前缀，默认 snapshot",
    )
    p.add_argument(
        "--retries",
        type=int,
        default=10,
        help="连接失败时的重试次数，默认 10",
    )
    p.add_argument(
        "--retry-delay",
        type=float,
        default=2.0,
        help="重试间隔（秒），默认 2",
    )
    p.add_argument(
        "--warmup",
        type=float,
        default=0.5,
        help="连接后冲刷缓冲的时长（秒），默认 0.5；设为 0 可跳过",
    )
    return p.parse_args()


def drain_stream(cap: cv2.VideoCapture, duration: float) -> None:
    """持续读帧并丢弃，清掉 RTMP 缓冲里的旧画面。"""
    if duration <= 0:
        return
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        cap.grab()


def wait_interval(cap: cv2.VideoCapture, interval: float) -> None:
    """等待指定秒数，期间持续消费流内帧，避免下次截到重复画面。"""
    if interval <= 0:
        return
    deadline = time.monotonic() + interval
    while time.monotonic() < deadline:
        cap.grab()


def open_stream(url: str, retries: int, retry_delay: float) -> cv2.VideoCapture | None:
    for attempt in range(1, retries + 1):
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            # 先读一帧，确认流真正有画面
            ok, _ = cap.read()
            if ok:
                return cap
            cap.release()
        else:
            if cap is not None:
                cap.release()
        print(f"[{attempt}/{retries}] 无法打开流，{retry_delay:.0f}s 后重试…")
        time.sleep(retry_delay)
    return None


def make_filename(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"{prefix}_{ts}.jpg"


def save_frame(frame, output_dir: Path, prefix: str) -> Path:
    """写入 JPEG；用 imencode + 二进制写文件，避免 Windows 中文路径下 imwrite 失败。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / make_filename(prefix)
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    path.write_bytes(buf.tobytes())
    return path


def main() -> int:
    args = parse_args()
    output_dir = args.output.resolve()
    print(f"流地址: {args.url}")
    print(f"保存目录: {output_dir}")

    cap = open_stream(args.url, args.retries, args.retry_delay)
    if cap is None:
        print("错误: 无法连接 RTMP 流。请确认与 10.148.1.22 同一内网/VPN。", file=sys.stderr)
        return 1

    print("已连接，冲刷缓冲…")
    drain_stream(cap, args.warmup)
    print(f"开始截图（间隔 {args.interval}s）…")

    saved = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("读帧失败，尝试重新连接…")
                cap.release()
                cap = open_stream(args.url, args.retries, args.retry_delay)
                if cap is None:
                    print("重连失败。", file=sys.stderr)
                    return 1
                drain_stream(cap, args.warmup)
                continue

            path = save_frame(frame, output_dir, args.prefix)
            saved += 1
            print(f"[{saved}] 已保存: {path.name}")

            if args.once:
                break
            if args.count > 0 and saved >= args.count:
                break

            wait_interval(cap, args.interval)
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        cap.release()

    print(f"共保存 {saved} 张截图。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

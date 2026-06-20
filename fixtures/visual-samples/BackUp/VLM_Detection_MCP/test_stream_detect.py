#!/usr/bin/env python3
"""视频流抽帧 + 双模型 YOLO（人 / 机械）联调。

用法:
  仅测拉流与保存一帧（无需权重）:
    python test_stream_detect.py --url rtmp://10.148.1.22/live/test --stream-only

  抽帧 + YOLO 检测并保存三图 + 打印 JSON 摘要:
    python test_stream_detect.py --url rtmp://10.148.1.22/live/test

依赖: pip install -r requirements.txt
权重: weights/worker/yolo26x_worker.pt 与 weights/machinery/yolo26l_machinery.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2

from stream_capture import capture_one_frame, enhance_contrast, preprocess_for_infer

ROOT = Path(__file__).resolve().parent


def save_jpeg(path: Path, bgr) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    path.write_bytes(buf.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser(description="RTMP/HLS 抽帧 + YOLO 人机检测联调")
    ap.add_argument(
        "--url",
        default="rtmp://10.148.1.22/live/test",
        help="视频流地址",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "output" / "stream_test",
        help="输出目录",
    )
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--stream-only", action="store_true", help="只拉流存图，不加载 YOLO")
    ap.add_argument("--no-preprocess", action="store_true", help="不做长边640缩放与增强")
    ap.add_argument("--retries", type=int, default=10, help="连接重试次数")
    ap.add_argument("--retry-delay", type=float, default=2.0)
    ap.add_argument("--warmup", type=float, default=0.5)
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.out if args.out.is_absolute() else (ROOT / args.out)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"流地址: {args.url}")
    print("正在连接并抽帧…")
    try:
        frame = capture_one_frame(
            args.url.strip(),
            retries=args.retries,
            retry_delay=args.retry_delay,
            warmup=args.warmup,
        )
    except RuntimeError as e:
        print(f"抽帧失败: {e}", file=sys.stderr)
        print(
            "请检查: 1) 与本机网络/VPN 是否可达摄像机网段 2) FFmpeg/OpenCV 是否支持该流 3) 流是否在线",
            file=sys.stderr,
        )
        return 2

    raw_path = out_dir / f"{ts}_frame_raw.jpg"
    save_jpeg(raw_path, frame)
    print(f"已保存原始帧: {raw_path}")

    if args.stream_only:
        print("(--stream-only) 已跳过 YOLO。")
        return 0

    from detect_core import build_triple_images, load_config, load_models, run_dual_detect

    proc = frame
    if not args.no_preprocess:
        proc = preprocess_for_infer(proc, max_side=640)
        proc = enhance_contrast(proc)

    cfg = load_config(args.config)
    try:
        bundle = load_models(cfg)
    except FileNotFoundError as e:
        print(f"缺少权重，无法做 YOLO: {e}", file=sys.stderr)
        print("可先运行: python scripts/redownload_weights.py", file=sys.stderr)
        print("或仅用抽帧验证: --stream-only", file=sys.stderr)
        return 3

    print("YOLO 推理中…")
    worker_rows, machinery_rows = run_dual_detect(bundle, proc, source_name="stream")
    original, human, machine = build_triple_images(proc, worker_rows, machinery_rows)

    stem = f"{ts}_yolo"
    save_jpeg(out_dir / f"{stem}_image.jpg", original)
    save_jpeg(out_dir / f"{stem}_image-human.jpg", human)
    save_jpeg(out_dir / f"{stem}_image-machine.jpg", machine)

    payload = {
        "stream_url_mask": args.url.split("@")[-1],
        "counts": {"worker": len(worker_rows), "machinery": len(machinery_rows)},
        "detections": {"worker": worker_rows, "machinery": machinery_rows},
        "saved": {
            "raw": str(raw_path),
            "image": str(out_dir / f"{stem}_image.jpg"),
            "image_human": str(out_dir / f"{stem}_image-human.jpg"),
            "image_machine": str(out_dir / f"{stem}_image-machine.jpg"),
        },
    }
    json_path = out_dir / f"{stem}_detections.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"人数相关框: {len(worker_rows)} | 机械框: {len(machinery_rows)}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

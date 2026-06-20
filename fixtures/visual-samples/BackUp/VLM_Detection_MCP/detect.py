#!/usr/bin/env python3
"""
工地双模型 YOLO 推理：工人/PPE + 施工机械（仅检测，不训练）。

用法:
  python detect.py --source input/demo.jpg
  python detect.py --source input/ --save-img --export-json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2

from detect_core import (
    ROOT,
    WORKER_COLOR,
    MACHINERY_COLOR,
    build_triple_images,
    draw_boxes,
    load_config,
    load_models,
    resolve_path,
    run_dual_detect,
)


def iter_sources(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
    return sorted(p for p in source.iterdir() if p.suffix.lower() in exts)


def main() -> int:
    ap = argparse.ArgumentParser(description="VLM-Detection 双模型工地目标检测")
    ap.add_argument("--source", type=Path, default=ROOT / "input", help="图片或目录")
    ap.add_argument("--config", type=Path, default=None, help="config.yaml 路径")
    ap.add_argument("--out", type=Path, default=ROOT / "output", help="输出目录")
    ap.add_argument("--conf", type=float, default=None, help="置信度阈值")
    ap.add_argument("--imgsz", type=int, default=None)
    ap.add_argument("--device", type=str, default=None)
    ap.add_argument("--worker-only", action="store_true", help="仅跑工人/PPE 模型")
    ap.add_argument("--machinery-only", action="store_true", help="仅跑机械模型")
    ap.add_argument("--save-img", action="store_true", help="保存标注图（合并两模型于一张）")
    ap.add_argument(
        "--triple",
        action="store_true",
        help="保存三张图：原图 / human / machine（HiAgent 固定顺序）",
    )
    ap.add_argument("--export-json", action="store_true", help="导出 JSON")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.device:
        cfg.setdefault("inference", {})["device"] = args.device

    bundle = load_models(cfg)
    run_worker = not args.machinery_only
    run_machinery = not args.worker_only

    source = args.source if args.source.is_absolute() else (ROOT / args.source)
    sources = iter_sources(source.resolve())
    if not sources:
        print(f"未找到图片: {source}")
        return 1

    out_dir = args.out if args.out.is_absolute() else (ROOT / args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = out_dir / "images"
    triple_dir = out_dir / "triple"
    if args.save_img or args.triple:
        img_dir.mkdir(parents=True, exist_ok=True)
    if args.triple:
        triple_dir.mkdir(parents=True, exist_ok=True)

    all_payload: list[dict] = []

    for img_path in sources:
        rel_name = img_path.name
        stem = img_path.stem
        image_bgr = cv2.imread(str(img_path))
        if image_bgr is None:
            print(f"跳过无法读取: {rel_name}")
            continue

        worker_rows: list[dict] = []
        machinery_rows: list[dict] = []

        if run_worker and run_machinery:
            worker_rows, machinery_rows = run_dual_detect(
                bundle, image_bgr, source_name=rel_name, conf=args.conf, imgsz=args.imgsz
            )
        else:
            from detect_core import collect_detections

            if run_worker:
                w_results = bundle.worker.predict(
                    source=image_bgr,
                    imgsz=args.imgsz or bundle.imgsz,
                    conf=args.conf if args.conf is not None else bundle.conf,
                    classes=bundle.worker_classes,
                    device=bundle.device,
                    verbose=False,
                )
                worker_rows = collect_detections(
                    w_results[0], bundle.worker_names, rel_name, "worker"
                )
            if run_machinery:
                m_results = bundle.machinery.predict(
                    source=image_bgr,
                    imgsz=args.imgsz or bundle.imgsz,
                    conf=args.conf if args.conf is not None else bundle.conf,
                    device=bundle.device,
                    verbose=False,
                )
                machinery_rows = collect_detections(
                    m_results[0], bundle.machinery_names, rel_name, "machinery"
                )

        merged = worker_rows + machinery_rows
        all_payload.append(
            {
                "image": rel_name,
                "detection_count": len(merged),
                "worker_count": len(worker_rows),
                "machinery_count": len(machinery_rows),
                "detections": merged,
            }
        )

        print(
            f"{rel_name}: worker={len(worker_rows)} machinery={len(machinery_rows)} total={len(merged)}"
        )

        if args.triple:
            original, human, machine = build_triple_images(image_bgr, worker_rows, machinery_rows)
            cv2.imwrite(str(triple_dir / f"{stem}_01_original.jpg"), original)
            cv2.imwrite(str(triple_dir / f"{stem}_02_human.jpg"), human)
            cv2.imwrite(str(triple_dir / f"{stem}_03_machine.jpg"), machine)

        if args.save_img:
            vis = image_bgr.copy()
            draw_boxes(vis, worker_rows, WORKER_COLOR)
            draw_boxes(vis, machinery_rows, MACHINERY_COLOR)
            cv2.imwrite(str(img_dir / rel_name), vis)

    if args.export_json:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_path = out_dir / f"detections_{stamp}.json"
        worker_path = resolve_path(cfg["models"]["worker"])
        machinery_path = resolve_path(cfg["models"]["machinery"])
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "config": {
                        "worker_weights": str(worker_path),
                        "machinery_weights": str(machinery_path),
                        "conf": args.conf if args.conf is not None else bundle.conf,
                        "imgsz": args.imgsz if args.imgsz is not None else bundle.imgsz,
                    },
                    "images": all_payload,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"JSON -> {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

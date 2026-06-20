"""RTMP/视频流 → 抽帧 → YOLO 双模型 → 固定顺序三图（原图 / 人 / 机）。"""
from __future__ import annotations

import base64
import os
import uuid
from typing import Any

import cv2

from detect_core import build_triple_images, load_config, load_models, run_dual_detect
from stream_capture import capture_one_frame, enhance_contrast, preprocess_for_infer

_bundle = None


def _jpeg_b64(bgr) -> str:
    q = int(os.environ.get("VLM_JPEG_QUALITY", "82"))
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _get_bundle():
    global _bundle
    if _bundle is None:
        from pathlib import Path

        cfg_path = os.environ.get("VLM_CONFIG", "").strip() or None
        cfg = load_config(Path(cfg_path)) if cfg_path else load_config()
        _bundle = load_models(cfg)
    return _bundle


def analyze_rtmp_stream(stream_url: str, *, return_urls: bool = False) -> dict[str, Any]:
    """输入 RTMP/HLS/FLV 地址字符串，返回固定顺序三张图。

    顺序（与产品规格一致）:
      1. image — 当前帧原图（预处理后）
      2. image-human — 人员/PPE 检测叠加
      3. image-machine — 机械检测叠加
    """
    url = (stream_url or "").strip()
    if not url:
        return {"ok": False, "error": "stream_url 为空"}

    retries = int(os.environ.get("VLM_STREAM_RETRIES", "10"))
    retry_delay = float(os.environ.get("VLM_STREAM_RETRY_DELAY", "2"))
    warmup = float(os.environ.get("VLM_STREAM_WARMUP", "0.5"))

    try:
        frame = capture_one_frame(url, retries=retries, retry_delay=retry_delay, warmup=warmup)
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    proc = enhance_contrast(preprocess_for_infer(frame, max_side=640))
    workers, machines = run_dual_detect(_get_bundle(), proc, source_name="rtmp")
    original, human_vis, machine_vis = build_triple_images(proc, workers, machines)

    b1, b2, b3 = _jpeg_b64(original), _jpeg_b64(human_vis), _jpeg_b64(machine_vis)

    out: dict[str, Any] = {
        "ok": True,
        "format": "jpeg",
        "image_count": 3,
        "stream_url": url.split("@")[-1][:200],
        "counts": {"worker": len(workers), "machinery": len(machines)},
        "detections": {"worker": workers, "machinery": machines},
        "images": [
            {
                "index": 1,
                "role": "image",
                "filename": "image.jpg",
                "mime": "image/jpeg",
                "base64": b1,
            },
            {
                "index": 2,
                "role": "image-human",
                "filename": "image-human.jpg",
                "mime": "image/jpeg",
                "base64": b2,
            },
            {
                "index": 3,
                "role": "image-machine",
                "filename": "image-machine.jpg",
                "mime": "image/jpeg",
                "base64": b3,
            },
        ],
        "image": b1,
        "image_human": b2,
        "image_machine": b3,
    }

    if return_urls:
        from artifact_storage import upload_triple_jpg

        job_id = uuid.uuid4().hex
        store = upload_triple_jpg(job_id, original, human_vis, machine_vis)
        out["storage"] = {"mode": store.mode, "detail": store.detail}
        if store.image:
            out["image_url"] = store.image
            out["image_human_url"] = store.image_human
            out["image_machine_url"] = store.image_machine

    return out

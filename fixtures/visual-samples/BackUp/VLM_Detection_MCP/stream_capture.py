"""从 RTMP / HLS / FLV 等地址抽取单帧（OpenCV + FFmpeg 后端）。"""
from __future__ import annotations

import os
import time

import cv2
import numpy as np


def drain_capture(cap: cv2.VideoCapture, duration: float) -> None:
    if duration <= 0:
        return
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        cap.grab()


def open_stream(url: str, *, retries: int, retry_delay: float) -> cv2.VideoCapture | None:
    open_timeout_ms = int(os.environ.get("VLM_STREAM_OPEN_TIMEOUT_MS", "8000"))
    for attempt in range(1, retries + 1):
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if open_timeout_ms > 0 and hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, open_timeout_ms)
        if open_timeout_ms > 0 and hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, open_timeout_ms)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                return cap
            cap.release()
        else:
            if cap is not None:
                cap.release()
        if attempt < retries:
            time.sleep(retry_delay)
    return None


def capture_one_frame(
    url: str,
    *,
    retries: int | None = None,
    retry_delay: float | None = None,
    warmup: float = 0.5,
) -> np.ndarray:
    if retries is None:
        retries = int(os.environ.get("VLM_STREAM_RETRIES", "3"))
    if retry_delay is None:
        retry_delay = float(os.environ.get("VLM_STREAM_RETRY_DELAY", "1"))
    cap = open_stream(url, retries=retries, retry_delay=retry_delay)
    if cap is None:
        raise RuntimeError(f"无法打开视频流: {url}")
    try:
        drain_capture(cap, warmup)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("读取帧失败")
        return frame
    finally:
        cap.release()


def preprocess_for_infer(image_bgr: np.ndarray, max_side: int = 640) -> np.ndarray:
    h, w = image_bgr.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return image_bgr
    scale = max_side / float(m)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    return cv2.resize(image_bgr, (nw, nh), interpolation=cv2.INTER_AREA)


def enhance_contrast(image_bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    merged = cv2.merge([l2, a, b])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

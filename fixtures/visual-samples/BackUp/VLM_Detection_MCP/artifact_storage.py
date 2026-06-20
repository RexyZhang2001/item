"""三图落盘 / MinIO 上传，返回可对平台暴露的 URL（v2 规格）。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from io import BytesIO

import cv2
import numpy as np


@dataclass(frozen=True)
class StorageResult:
    image: str | None
    image_human: str | None
    image_machine: str | None
    mode: str
    detail: dict[str, Any]


def _jpeg_bytes(image_bgr: np.ndarray, quality: int | None = None) -> bytes:
    q = quality if quality is not None else int(os.environ.get("VLM_JPEG_QUALITY", "82"))
    ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    return buf.tobytes()


def _png_bytes(image_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise RuntimeError("PNG 编码失败")
    return buf.tobytes()


def _minio_client():
    from minio import Minio

    raw = os.environ.get("MINIO_ENDPOINT", "").strip()
    access = os.environ.get("MINIO_ACCESS_KEY", "").strip()
    secret = os.environ.get("MINIO_SECRET_KEY", "").strip()
    if not raw or not access or not secret:
        return None
    secure = os.environ.get("MINIO_SECURE", "true").lower() in ("1", "true", "yes")
    if raw.startswith("https://"):
        raw = raw[8:]
        secure = True
    elif raw.startswith("http://"):
        raw = raw[7:]
        secure = False
    return Minio(raw, access_key=access, secret_key=secret, secure=secure)


def upload_triple_jpg(
    job_id: str,
    original: np.ndarray,
    human: np.ndarray,
    machine: np.ndarray,
) -> StorageResult:
    """上传固定顺序三图，文件格式均为 JPEG（.jpg）。"""
    names = (
        (f"{job_id}_image.jpg", original),
        (f"{job_id}_image-human.jpg", human),
        (f"{job_id}_image-machine.jpg", machine),
    )
    blobs = [(n, _jpeg_bytes(img)) for n, img in names]
    return _store_blobs(job_id, blobs, content_type="image/jpeg")


def upload_triple_png(
    job_id: str,
    original: np.ndarray,
    human: np.ndarray,
    machine: np.ndarray,
) -> StorageResult:
    names = (
        (f"{job_id}_image.png", original),
        (f"{job_id}_image-human.png", human),
        (f"{job_id}_image-machine.png", machine),
    )
    blobs = [(n, _png_bytes(img)) for n, img in names]
    return _store_blobs(job_id, blobs, content_type="image/png")


def _store_blobs(
    job_id: str,
    blobs: list[tuple[str, bytes]],
    *,
    content_type: str,
) -> StorageResult:
    bucket = os.environ.get("MINIO_BUCKET", "").strip()
    public_prefix = os.environ.get("MINIO_PUBLIC_URL", "").strip().rstrip("/")

    client = _minio_client()
    if bucket and client:
        return _upload_minio(job_id, bucket, blobs, public_prefix, content_type)

    root = os.environ.get("ARTIFACT_ROOT", "").strip()
    public_base = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8080").strip().rstrip("/")
    if root:
        return _write_local(job_id, Path(root), public_base, blobs)

    return StorageResult(
        image=None,
        image_human=None,
        image_machine=None,
        mode="none",
        detail={"message": "未配置 MINIO_BUCKET 或 ARTIFACT_ROOT，仅返回 base64"},
    )


def _upload_minio(
    job_id: str,
    bucket: str,
    blobs: list[tuple[str, bytes]],
    public_prefix: str,
    content_type: str,
) -> StorageResult:
    client = _minio_client()
    if client is None:
        raise RuntimeError("MinIO 客户端初始化失败")
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    prefix = os.environ.get("MINIO_OBJECT_PREFIX", "vlm").strip().strip("/") or "vlm"
    keys: list[str] = []
    for filename, data in blobs:
        object_name = f"{prefix}/{job_id}/{filename}"
        client.put_object(
            bucket,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        keys.append(object_name)

    if public_prefix:
        urls = [f"{public_prefix.rstrip('/')}/{k}" for k in keys]
    else:
        urls = [
            client.presigned_get_object(bucket, k, expires=timedelta(days=7))
            for k in keys
        ]

    return StorageResult(
        image=urls[0],
        image_human=urls[1],
        image_machine=urls[2],
        mode="minio",
        detail={"bucket": bucket, "keys": keys},
    )


def _write_local(
    job_id: str,
    root: Path,
    public_base: str,
    blobs: list[tuple[str, bytes]],
) -> StorageResult:
    job_dir = root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    for filename, data in blobs:
        path = job_dir / filename
        path.write_bytes(data)
        urls.append(f"{public_base}/static/jobs/{job_id}/{filename}")

    return StorageResult(
        image=urls[0],
        image_human=urls[1],
        image_machine=urls[2],
        mode="local",
        detail={"dir": str(job_dir.resolve())},
    )

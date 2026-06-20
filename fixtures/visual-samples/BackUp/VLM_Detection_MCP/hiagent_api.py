#!/usr/bin/env python3
"""
HiAgent / 耀耀工厂 插件：VLM-Detection v2 HTTP 服务。

- 图片：multipart / JSON（base64 或 URL）
- 视频流：JSON 传入 RTMP/HLS/FLV，抽帧 → 三图 PNG → MinIO 或本地 URL

本地启动:
  uvicorn hiagent_api:app --host 0.0.0.0 --port 8080

环境变量:
  HIAGENT_API_KEY   可选；设置后请求头须带 X-API-Key
  VLM_CONFIG        可选；config.yaml 路径
  ARTIFACT_ROOT     可选；三图落盘根目录，对应挂载路径 /static/jobs
  PUBLIC_BASE_URL   可选；拼本地 URL，默认 http://127.0.0.1:8080
  MINIO_ENDPOINT    可选；如 minio:9000
  MINIO_ACCESS_KEY  MINIO_SECRET_KEY  MINIO_BUCKET
  MINIO_SECURE      可选；默认 true（无 http(s) 前缀时）
  MINIO_PUBLIC_URL  可选；公网访问 URL 前缀；不填则使用预签名 URL
  MINIO_OBJECT_PREFIX 可选；对象键前缀，默认 vlm
"""
from __future__ import annotations

import base64
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from artifact_storage import upload_triple_png
from detect_core import (
    ModelBundle,
    build_triple_images,
    decode_image_bytes,
    encode_jpeg_b64,
    load_config,
    load_models,
    run_dual_detect,
    run_triple_detect,
)
from stream_capture import capture_one_frame, enhance_contrast, preprocess_for_infer

API_KEY = os.environ.get("HIAGENT_API_KEY", "").strip()
CONFIG_PATH = os.environ.get("VLM_CONFIG", "").strip() or None

_bundle: ModelBundle | None = None


def _get_bundle() -> ModelBundle:
    if _bundle is None:
        raise RuntimeError("模型未加载")
    return _bundle


def _check_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bundle
    cfg = load_config(CONFIG_PATH) if CONFIG_PATH else load_config()
    _bundle = load_models(cfg)
    yield
    _bundle = None


app = FastAPI(
    title="VLM-Detection HiAgent Plugin",
    description="v2：图片或视频流；三图固定顺序；MinIO / 本地 URL / base64。",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ARTIFACT_ROOT = os.environ.get("ARTIFACT_ROOT", "").strip()
if _ARTIFACT_ROOT:
    _artifact_path = Path(_ARTIFACT_ROOT)
    _artifact_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static/jobs", StaticFiles(directory=str(_artifact_path)), name="job_artifacts")


class DetectJsonRequest(BaseModel):
    image_base64: str | None = Field(default=None, description="图片 Base64（与 image_url 二选一）")
    image_url: str | None = Field(default=None, description="图片公网 URL（与 image_base64 二选一）")
    conf: float | None = Field(default=None, ge=0.0, le=1.0, description="置信度阈值")
    imgsz: int | None = Field(default=None, ge=320, le=1280, description="推理尺寸")


class StreamAnalyzeRequest(BaseModel):
    stream_url: str = Field(..., description="RTMP / HLS / FLV 等地址")
    conf: float | None = Field(default=None, ge=0.0, le=1.0)
    imgsz: int | None = Field(default=None, ge=320, le=1280)
    preprocess_resize: bool = Field(default=True, description="长边缩放到 640")
    enhance_contrast: bool = Field(default=True, description="CLAHE 对比度增强")
    retries: int = Field(default=8, ge=1, le=30)
    retry_delay: float = Field(default=2.0, ge=0.2, le=30.0)
    warmup: float = Field(default=0.5, ge=0.0, le=10.0)
    include_base64: bool = Field(default=False, description="在有 URL 时仍返回 base64")


async def _fetch_url(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        if len(resp.content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片超过 5MB（HiAgent 单图限制）")
        return resp.content


def _triple_response(
    image_bgr,
    *,
    source_name: str,
    conf: float | None,
    imgsz: int | None,
) -> dict[str, Any]:
    payload = run_triple_detect(
        _get_bundle(), image_bgr, source_name=source_name, conf=conf, imgsz=imgsz
    )
    return {"ok": True, **payload}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "vlm-detection-hiagent", "version": "2.0.0"}


@app.post("/v1/analyze/stream", dependencies=[Depends(_check_api_key)])
def analyze_stream(body: StreamAnalyzeRequest) -> dict[str, Any]:
    """视频流抽一帧 → 三图上传 → 返回 image / image_human / image_machine URL。"""
    job_id = uuid.uuid4().hex
    url = body.stream_url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="stream_url 为空")
    try:
        frame = capture_one_frame(
            url,
            retries=body.retries,
            retry_delay=body.retry_delay,
            warmup=body.warmup,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    proc = frame
    if body.preprocess_resize:
        proc = preprocess_for_infer(proc, max_side=640)
    if body.enhance_contrast:
        proc = enhance_contrast(proc)

    bundle = _get_bundle()
    worker_rows, machinery_rows = run_dual_detect(
        bundle, proc, source_name="stream", conf=body.conf, imgsz=body.imgsz
    )
    original, human, machine = build_triple_images(proc, worker_rows, machinery_rows)
    store = upload_triple_png(job_id, original, human, machine)

    out: dict[str, Any] = {
        "ok": True,
        "job_id": job_id,
        "image": store.image,
        "image_human": store.image_human,
        "image_machine": store.image_machine,
        "storage": {"mode": store.mode, "detail": store.detail},
        "detections": {"worker": worker_rows, "machinery": machinery_rows},
        "counts": {"worker": len(worker_rows), "machinery": len(machinery_rows)},
    }
    if store.mode == "none" or body.include_base64:
        out["images"] = [
            {"role": "original", "mime": "image/jpeg", "base64": encode_jpeg_b64(original)},
            {"role": "human", "mime": "image/jpeg", "base64": encode_jpeg_b64(human)},
            {"role": "machine", "mime": "image/jpeg", "base64": encode_jpeg_b64(machine)},
        ]
    return out


@app.post("/v1/detect/triple", dependencies=[Depends(_check_api_key)])
async def detect_triple_multipart(
    file: UploadFile = File(..., description="待检测图片"),
    conf: float | None = None,
    imgsz: int | None = None,
) -> dict[str, Any]:
    """multipart 上传单张图片，返回固定顺序 3 张图（original / human / machine）。"""
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片超过 5MB")
    try:
        image_bgr = decode_image_bytes(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _triple_response(image_bgr, source_name=file.filename or "upload", conf=conf, imgsz=imgsz)


@app.post("/v1/detect/triple/json", dependencies=[Depends(_check_api_key)])
async def detect_triple_json(body: DetectJsonRequest) -> dict[str, Any]:
    """JSON 请求：image_base64 或 image_url 二选一。"""
    if bool(body.image_base64) == bool(body.image_url):
        raise HTTPException(status_code=400, detail="请提供 image_base64 或 image_url 之一")

    if body.image_url:
        try:
            data = await _fetch_url(body.image_url)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"拉取图片失败: {e}") from e
        source_name = body.image_url.rsplit("/", 1)[-1] or "url"
    else:
        raw = body.image_base64 or ""
        if "," in raw:
            raw = raw.split(",", 1)[1]
        try:
            data = base64.b64decode(raw, validate=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail="image_base64 无效") from e
        source_name = "base64"

    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片超过 5MB")

    try:
        image_bgr = decode_image_bytes(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _triple_response(image_bgr, source_name=source_name, conf=body.conf, imgsz=body.imgsz)

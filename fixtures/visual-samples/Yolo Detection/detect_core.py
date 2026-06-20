"""双模型工地检测核心逻辑（CLI 与 HiAgent HTTP 插件共用）。"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent

WORKER_COLOR = (0, 200, 0)  # BGR
MACHINERY_COLOR = (0, 140, 255)


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or ROOT / "config.yaml"
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else (ROOT / p).resolve()


def box_record(xyxy, conf, cls_id, names: dict, source: str, model_tag: str) -> dict:
    x1, y1, x2, y2 = (float(v) for v in xyxy)
    cid = int(cls_id)
    return {
        "model": model_tag,
        "source": source,
        "class_id": cid,
        "class_name": names.get(cid, str(cid)),
        "confidence": round(float(conf), 4),
        "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
        "bbox_xywh": [
            round(x1, 2),
            round(y1, 2),
            round(x2 - x1, 2),
            round(y2 - y1, 2),
        ],
    }


def collect_detections(result, names: dict, source: str, model_tag: str) -> list[dict]:
    rows: list[dict] = []
    if result.boxes is None:
        return rows
    for xyxy, conf, cls_id in zip(
        result.boxes.xyxy.tolist(),
        result.boxes.conf.tolist(),
        result.boxes.cls.tolist(),
    ):
        rows.append(box_record(xyxy, conf, cls_id, names, source, model_tag))
    return rows


def draw_boxes(image: np.ndarray, rows: list[dict], color: tuple[int, int, int]) -> None:
    for r in rows:
        x1, y1, x2, y2 = (int(v) for v in r["bbox_xyxy"])
        label = f"{r['class_name']} {r['confidence']:.2f}"
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            label,
            (x1, max(y1 - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )


def decode_image_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片（支持 jpg/png/webp 等）")
    return img


def encode_jpeg_b64(image: np.ndarray, quality: int = 90) -> str:
    ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    return base64.b64encode(buf.tobytes()).decode("ascii")


@dataclass
class ModelBundle:
    worker: YOLO
    machinery: YOLO
    worker_names: dict[int, str]
    machinery_names: dict[int, str]
    worker_classes: list[int] | None
    conf: float
    imgsz: int
    device: str | None


def load_models(cfg: dict | None = None) -> ModelBundle:
    cfg = cfg or load_config()
    inf = cfg["inference"]
    device = inf.get("device") or None
    if device == "":
        device = None
    worker_path = resolve_path(cfg["models"]["worker"])
    machinery_path = resolve_path(cfg["models"]["machinery"])
    if not worker_path.is_file():
        raise FileNotFoundError(f"工人权重不存在: {worker_path}")
    if not machinery_path.is_file():
        raise FileNotFoundError(f"机械权重不存在: {machinery_path}")
    return ModelBundle(
        worker=YOLO(str(worker_path)),
        machinery=YOLO(str(machinery_path)),
        worker_names={int(k): v for k, v in cfg["worker_class_names"].items()},
        machinery_names={int(k): v for k, v in cfg["machinery_class_names"].items()},
        worker_classes=cfg.get("worker_classes"),
        conf=float(inf["conf"]),
        imgsz=int(inf["imgsz"]),
        device=device,
    )


def run_dual_detect(
    bundle: ModelBundle,
    image_bgr: np.ndarray,
    *,
    source_name: str = "upload",
    conf: float | None = None,
    imgsz: int | None = None,
) -> tuple[list[dict], list[dict]]:
    conf_v = conf if conf is not None else bundle.conf
    imgsz_v = imgsz if imgsz is not None else bundle.imgsz

    w_results = bundle.worker.predict(
        source=image_bgr,
        imgsz=imgsz_v,
        conf=conf_v,
        classes=bundle.worker_classes,
        device=bundle.device,
        verbose=False,
    )
    m_results = bundle.machinery.predict(
        source=image_bgr,
        imgsz=imgsz_v,
        conf=conf_v,
        device=bundle.device,
        verbose=False,
    )
    worker_rows = collect_detections(w_results[0], bundle.worker_names, source_name, "worker")
    machinery_rows = collect_detections(
        m_results[0], bundle.machinery_names, source_name, "machinery"
    )
    return worker_rows, machinery_rows


def build_triple_images(
    image_bgr: np.ndarray, worker_rows: list[dict], machinery_rows: list[dict]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    original = image_bgr.copy()
    human = image_bgr.copy()
    machine = image_bgr.copy()
    draw_boxes(human, worker_rows, WORKER_COLOR)
    draw_boxes(machine, machinery_rows, MACHINERY_COLOR)
    return original, human, machine


def run_triple_detect(
    bundle: ModelBundle,
    image_bgr: np.ndarray,
    *,
    source_name: str = "upload",
    conf: float | None = None,
    imgsz: int | None = None,
) -> dict[str, Any]:
    worker_rows, machinery_rows = run_dual_detect(
        bundle, image_bgr, source_name=source_name, conf=conf, imgsz=imgsz
    )
    original, human, machine = build_triple_images(image_bgr, worker_rows, machinery_rows)
    return {
        "images": [
            {"role": "original", "mime": "image/jpeg", "base64": encode_jpeg_b64(original)},
            {"role": "human", "mime": "image/jpeg", "base64": encode_jpeg_b64(human)},
            {"role": "machine", "mime": "image/jpeg", "base64": encode_jpeg_b64(machine)},
        ],
        "detections": {"worker": worker_rows, "machinery": machinery_rows},
        "counts": {"worker": len(worker_rows), "machinery": len(machinery_rows)},
    }

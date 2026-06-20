#!/usr/bin/env python3
"""权重丢失时从 HuggingFace 重新下载（需网络）。"""
from pathlib import Path
import shutil

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    w = hf_hub_download(
        repo_id="yihong1120/Construction-Hazard-Detection",
        filename="models/yolo26/pt/yolo26x.pt",
        local_dir=str(ROOT / "weights" / "_hf_worker"),
    )
    dst_w = ROOT / "weights" / "worker" / "yolo26x_worker.pt"
    dst_w.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(w, dst_w)
    print("worker ->", dst_w)

    m = hf_hub_download(
        repo_id="Zaafan/sitesense-weights",
        filename="yolo26l_construction_v1.pt",
        local_dir=str(ROOT / "weights" / "_hf_machinery"),
    )
    dst_m = ROOT / "weights" / "machinery" / "yolo26l_machinery.pt"
    dst_m.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(m, dst_m)
    print("machinery ->", dst_m)


if __name__ == "__main__":
    main()

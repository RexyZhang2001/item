from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _path_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value) if value else default


def _str_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    host: str = _str_env("AGENT_TOOLBOX_HOST", "127.0.0.1")
    port: int = _int_env("AGENT_TOOLBOX_PORT", 8899)
    root: Path = _path_env("AGENT_TOOLBOX_ROOT", ROOT)
    workspace: Path = _path_env("AGENT_TOOLBOX_WORKSPACE", ROOT / "workspace")

    vlm_detection_dir: Path = _path_env(
        "VLM_DETECTION_DIR",
        Path(r"J:\China Oversea  Final\VLM Detection"),
    )
    vlm_python: str = _str_env("VLM_PYTHON", "python")

    rtmp_snapshot_script: Path = _path_env(
        "RTMP_SNAPSHOT_SCRIPT",
        Path(r"J:\China Oversea  Final\3311 AI\rtmp_snapshot.py"),
    )
    rtmp_python: str = _str_env("RTMP_PYTHON", "python")
    default_rtmp_url: str = _str_env("DEFAULT_RTMP_URL", "rtmp://10.148.1.22/live/test")

    report_script: Path = _path_env(
        "REPORT_SCRIPT",
        Path(r"J:\China Oversea  Final\3311 AI\generate_community_doc.py"),
    )
    report_python: str = _str_env("REPORT_PYTHON", "python")

    whatsapp_archive_base_url: str = _str_env("WHATSAPP_ARCHIVE_BASE_URL", "http://127.0.0.1:8787")
    wacli_bin: str = _str_env("WACLI_BIN", "wacli")
    wacli_workdir: Path = _path_env("WACLI_WORKDIR", workspace / "wacli")
    wacli_store_dir: Path = _path_env("WACLI_STORE_DIR", workspace / "wacli")

    feishu_webhook_url: str = _str_env("FEISHU_WEBHOOK_URL", "")
    feishu_webhook_secret: str = _str_env("FEISHU_WEBHOOK_SECRET", "")
    feishu_app_id: str = _str_env("FEISHU_APP_ID", "")
    feishu_app_secret: str = _str_env("FEISHU_APP_SECRET", "")
    feishu_verification_token: str = _str_env("FEISHU_VERIFICATION_TOKEN", "")
    feishu_encrypt_key: str = _str_env("FEISHU_ENCRYPT_KEY", "")
    feishu_api_base_url: str = _str_env("FEISHU_API_BASE_URL", "https://open.feishu.cn")

    safety_policy_templates_dir: Path = _path_env(
        "SAFETY_POLICY_TEMPLATES_DIR",
        ROOT.parent / "safety-policy-templates-20241025",
    )
    safety_database_path: Path = _path_env(
        "SAFETY_DATABASE_PATH",
        workspace / "safety_platform.db",
    )

    # ── Yaoyao (structured input / OCR) settings ──
    yaoyao_work_dir: Path = _path_env(
        "YAOYAO_WORK_DIR",
        workspace / "yaoyao",
    )
    yaoyao_model_dir: Path = _path_env(
        "YAOYAO_MODEL_DIR",
        workspace / "yaoyao" / "models",
    )
    yaoyao_python_bin: str = _str_env("YAOYAO_PYTHON_BIN", "")
    yaoyao_worker_timeout: int = _int_env("YAOYAO_WORKER_TIMEOUT", 60)

    # ── SecureEye VLM 大模型配置 ──
    secureeye_base_url: str = _str_env("SECUREEYE_BASE_URL", "https://api.openai.com/v1")
    secureeye_api_key: str = _str_env("SECUREEYE_API_KEY", "")
    secureeye_model: str = _str_env("SECUREEYE_MODEL", "gpt-4o")
    secureeye_timeout_seconds: int = _int_env("SECUREEYE_TIMEOUT_SECONDS", 30)
    secureeye_max_concurrency: int = _int_env("SECUREEYE_MAX_CONCURRENCY", 4)
    yolo_conf_threshold: float = _float_env("YOLO_CONF_THRESHOLD", 0.45)


settings = Settings()

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8999

    agent_toolbox_base_url: str = "http://127.0.0.1:8899"

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    chitung_data_dir: Path = ROOT / "data"
    chitung_skills_dir: Path = ROOT / "skills"
    chitung_workflows_dir: Path = ROOT / "workflows"
    chitung_audit_log: Path = ROOT / "data" / "audit.jsonl"
    rag_chroma_dir: Path = ROOT / "data" / "rag_chroma"
    rag_meta_path: Path = ROOT / "data" / "rag_meta.json"
    rag_upload_dir: Path = ROOT / "data" / "rag_uploads"
    llm_embedding_base_url: str = ""
    llm_embedding_model: str = ""
    table_mapping_script_dir: Path = ROOT / "table-mapping" / "auto-fill-script"
    table_mapping_node_bin: str = "node"
    table_mapping_timeout_seconds: int = 180

    enable_feishu_adapter: bool = False
    enable_zht_adapter: bool = False
    enable_chitong_lingxun_adapter: bool = False
    enable_docmate_adapter: bool = False
    enable_yaoyao_huidu_adapter: bool = False
    enable_openclaw_adapter: bool = False

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)


settings = Settings(
    _env_file=str(ROOT / ".env"),
    _env_file_encoding="utf-8",
)

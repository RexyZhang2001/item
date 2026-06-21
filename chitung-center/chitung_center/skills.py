from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chitung_center.config import settings


@dataclass
class SkillInfo:
    name: str
    path: str
    summary: str
    enabled: bool = True
    category: str = "builtin"
    status: str = "ready"
    phase: str = ""
    tools: list[str] = field(default_factory=list)
    workflow: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "summary": self.summary,
            "enabled": self.enabled,
            "category": self.category,
            "status": self.status,
            "phase": self.phase,
            "tools": self.tools,
            "workflow": self.workflow,
        }


class SkillLoader:
    INDEX_FILE = "skills_index.json"

    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = skills_dir or settings.chitung_skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.skills_dir / self.INDEX_FILE
        self._index = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        if not self._index_path.exists():
            return {}
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index, ensure_ascii=False, indent=2), encoding="utf-8")

    def _meta(self, name: str) -> dict[str, Any]:
        meta = self._index.get(name, {})
        return meta if isinstance(meta, dict) else {}

    def _set_meta(self, name: str, meta: dict[str, Any]) -> None:
        self._index[name] = meta
        self._save_index()

    def list_skills(self, enabled_only: bool = False) -> list[SkillInfo]:
        skills: list[SkillInfo] = []
        for path in sorted(self.skills_dir.glob("*/SKILL.md")):
            name = path.parent.name
            meta = self._meta(name)
            if enabled_only and meta.get("enabled") is False:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = [line.strip("# ").strip() for line in text.splitlines() if line.strip()]
            summary = lines[1] if len(lines) > 1 else "No summary provided."
            skills.append(
                SkillInfo(
                    name=name,
                    path=str(path),
                    summary=summary,
                    enabled=bool(meta.get("enabled", True)),
                    category=str(meta.get("category", "builtin")),
                    status=str(meta.get("status", "ready")),
                    phase=str(meta.get("phase", "")),
                    tools=meta.get("tools") if isinstance(meta.get("tools"), list) else self._extract_tools(text),
                    workflow=str(meta.get("workflow", "")),
                )
            )
        return skills

    def get_info(self, name: str) -> SkillInfo | None:
        for skill in self.list_skills():
            if skill.name == name:
                return skill
        return None

    def read_skill(self, name: str) -> str | None:
        if any(part in name for part in ("/", "\\", "..")):
            return None
        path = self.skills_dir / name / "SKILL.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="ignore")

    def set_enabled(self, name: str, enabled: bool) -> bool:
        if self.read_skill(name) is None:
            return False
        meta = self._meta(name)
        meta["enabled"] = enabled
        self._set_meta(name, meta)
        return True

    def import_skill(self, name: str, content: str) -> SkillInfo | None:
        clean_name = _clean_name(name)
        if not clean_name or not content.strip():
            return None
        skill_dir = self.skills_dir / clean_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        md_path = skill_dir / "SKILL.md"
        md_path.write_text(content, encoding="utf-8")
        lines = [line.strip("# ").strip() for line in content.splitlines() if line.strip()]
        summary = lines[1] if len(lines) > 1 else "Imported skill."
        tools = self._extract_tools(content)
        meta = {
            "enabled": True,
            "category": "external",
            "status": "ready",
            "phase": "Imported",
            "tools": tools,
            "workflow": "",
        }
        self._set_meta(clean_name, meta)
        return SkillInfo(
            name=clean_name,
            path=str(md_path),
            summary=summary,
            enabled=True,
            category="external",
            status="ready",
            phase="Imported",
            tools=tools,
        )

    def delete_skill(self, name: str) -> bool:
        info = self.get_info(name)
        if not info or info.category != "external":
            return False
        skill_dir = self.skills_dir / name
        if not skill_dir.exists():
            return False
        shutil.rmtree(skill_dir, ignore_errors=True)
        self._index.pop(name, None)
        self._save_index()
        return True

    def skill_for_intent(self, intent: str) -> SkillInfo | None:
        name = INTENT_TO_SKILL.get(intent)
        if not name:
            return None
        for skill in self.list_skills():
            if skill.name == name and skill.enabled:
                return skill
        return None

    @staticmethod
    def _extract_tools(text: str) -> list[str]:
        tools: list[str] = []
        in_tools_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("##") and ("tool" in stripped.lower() or "preferred" in stripped.lower()):
                in_tools_section = True
                continue
            if in_tools_section and stripped.startswith("##"):
                in_tools_section = False
            if in_tools_section:
                tools.extend(re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*)`", stripped))
        return list(dict.fromkeys(tools))


# Maps router intents to the SKILL.md directory that governs that flow.
INTENT_TO_SKILL: dict[str, str] = {
    "hazard_intake": "hazard-intake",
    "weather_news_risk": "daily-risk-briefing",
    "document_form": "shanshan-doc",
}


def _clean_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-_")
    return cleaned[:80]


skill_loader = SkillLoader()

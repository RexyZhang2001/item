from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chitung_center.config import settings
from chitung_center.workflow_templates import WORKFLOW_TEMPLATES


@dataclass
class WorkflowInfo:
    name: str
    path: str
    summary: str
    enabled: bool = True
    category: str = "builtin"
    status: str = "ready"
    phase: str = ""
    priority: str = ""
    triggers: str = ""
    agents: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    existing_tools: list[str] = field(default_factory=list)
    pending_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "summary": self.summary,
            "enabled": self.enabled,
            "category": self.category,
            "status": self.status,
            "phase": self.phase,
            "priority": self.priority,
            "triggers": self.triggers,
            "agents": self.agents,
            "steps": self.steps,
            "existing_tools": self.existing_tools,
            "pending_tools": self.pending_tools,
        }


class WorkflowLoader:
    INDEX_FILE = "workflows_index.json"

    def __init__(self, workflows_dir: Path | None = None) -> None:
        self.workflows_dir = workflows_dir or settings.chitung_workflows_dir
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.workflows_dir / self.INDEX_FILE
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

    def list_workflows(self, enabled_only: bool = False) -> list[WorkflowInfo]:
        workflows = self._builtin_workflows()
        external_names = {item.name for item in workflows}
        for path in sorted(self.workflows_dir.glob("*/WORKFLOW.md")):
            name = path.parent.name
            if name in external_names:
                continue
            meta = self._meta(name)
            if enabled_only and meta.get("enabled") is False:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            workflows.append(self._info_from_text(name, path, text, meta))
        return sorted(workflows, key=lambda item: (item.category != "builtin", item.name))

    def read_workflow(self, name: str) -> str | None:
        if _unsafe_name(name):
            return None
        path = self.workflows_dir / name / "WORKFLOW.md"
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
        template = WORKFLOW_TEMPLATES.get(name)
        if not template:
            return None
        steps = "\n".join(
            f"{idx + 1}. {step.agent_name}: {step.name}"
            + (f" (`{step.tool_name}`)" if step.tool_name else "")
            for idx, step in enumerate(template.steps)
        )
        return (
            f"# {template.title}\n\n"
            f"{template.description}\n\n"
            f"## Intent\n\n`{template.intent}`\n\n"
            f"## Steps\n\n{steps or 'No steps registered.'}\n"
        )

    def get_info(self, name: str) -> WorkflowInfo | None:
        for workflow in self.list_workflows():
            if workflow.name == name:
                return workflow
        return None

    def set_enabled(self, name: str, enabled: bool) -> bool:
        if self.read_workflow(name) is None:
            return False
        meta = self._meta(name)
        meta["enabled"] = enabled
        self._set_meta(name, meta)
        return True

    def import_workflow(self, name: str, content: str) -> WorkflowInfo | None:
        clean_name = _clean_name(name)
        if not clean_name or not content.strip():
            return None
        workflow_dir = self.workflows_dir / clean_name
        workflow_dir.mkdir(parents=True, exist_ok=True)
        md_path = workflow_dir / "WORKFLOW.md"
        md_path.write_text(content, encoding="utf-8")
        meta = {
            "enabled": True,
            "category": "external",
            "status": "ready",
            "phase": "Imported",
            "priority": "",
            "triggers": "",
            "agents": "",
            "steps": [],
        }
        self._set_meta(clean_name, meta)
        return self._info_from_text(clean_name, md_path, content, meta)

    def delete_workflow(self, name: str) -> bool:
        info = self.get_info(name)
        if not info or info.category != "external":
            return False
        workflow_dir = self.workflows_dir / name
        if not workflow_dir.exists():
            return False
        shutil.rmtree(workflow_dir, ignore_errors=True)
        self._index.pop(name, None)
        self._save_index()
        return True

    def _builtin_workflows(self) -> list[WorkflowInfo]:
        workflows: list[WorkflowInfo] = []
        for name, template in WORKFLOW_TEMPLATES.items():
            meta = self._meta(name)
            steps = [
                {
                    "step": idx + 1,
                    "agent": step.agent_name,
                    "action": step.name,
                    "tool": step.tool_name,
                    "requires_confirmation": step.requires_confirmation,
                }
                for idx, step in enumerate(template.steps)
            ]
            workflows.append(
                WorkflowInfo(
                    name=name,
                    path=f"builtin://workflow_templates/{name}",
                    summary=template.description,
                    enabled=bool(meta.get("enabled", True)),
                    category="builtin",
                    status=str(meta.get("status", "done")),
                    phase=str(meta.get("phase", "Core")),
                    triggers=template.intent,
                    agents=", ".join(sorted({step.agent_name for step in template.steps})),
                    steps=steps,
                    existing_tools=[step.tool_name for step in template.steps if step.tool_name],
                )
            )
        return workflows

    def _info_from_text(self, name: str, path: Path, text: str, meta: dict[str, Any]) -> WorkflowInfo:
        lines = [line.strip("# ").strip() for line in text.splitlines() if line.strip()]
        summary = lines[1] if len(lines) > 1 else "No summary provided."
        return WorkflowInfo(
            name=name,
            path=str(path),
            summary=summary,
            enabled=bool(meta.get("enabled", True)),
            category=str(meta.get("category", "external")),
            status=str(meta.get("status", "ready")),
            phase=str(meta.get("phase", "")),
            priority=str(meta.get("priority", "")),
            triggers=str(meta.get("triggers", "")),
            agents=str(meta.get("agents", "")),
            steps=meta.get("steps") if isinstance(meta.get("steps"), list) else [],
            existing_tools=self._extract_section_tools(text, "Existing Tools"),
            pending_tools=self._extract_section_tools(text, "Pending Tools"),
        )

    @staticmethod
    def _extract_section_tools(text: str, section_header: str) -> list[str]:
        tools: list[str] = []
        in_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("##") and section_header.lower() in stripped.lower():
                in_section = True
                continue
            if in_section and stripped.startswith("##"):
                break
            if in_section:
                tools.extend(re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*)`", stripped))
        return list(dict.fromkeys(tools))


def _clean_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-_")[:80]


def _unsafe_name(name: str) -> bool:
    return any(part in name for part in ("/", "\\", ".."))


workflow_loader = WorkflowLoader()

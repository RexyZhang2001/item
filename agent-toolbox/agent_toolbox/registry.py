from __future__ import annotations

from pathlib import Path
from typing import Callable

import requests

from .config import settings
from .models import ToolSpec
from .tools.confirmations import CONFIRMATION_TOOL_SPECS
from .tools.feishu_events import FEISHU_EVENT_TOOL_SPECS
from .tools.future_operations import future_tool_specs
from .tools.docmate_docx import ALL_DOCMATE_SPECS
from .workflow_tools import workflow_tool_specs


ToolHandler = Callable[..., object]


def _exists(path: Path) -> bool:
    return path.exists()


def health_checks() -> dict[str, dict[str, object]]:
    checks: dict[str, dict[str, object]] = {
        "rtmp_snapshot": {
            "available": _exists(settings.rtmp_snapshot_script),
            "path": str(settings.rtmp_snapshot_script),
        },
        "vlm_detect": {
            "available": _exists(settings.vlm_detection_dir / "detect.py"),
            "path": str(settings.vlm_detection_dir / "detect.py"),
        },
        "generate_report": {
            "available": _exists(settings.report_script),
            "path": str(settings.report_script),
        },
        "whatsapp_archive": {
            "available": False,
            "url": settings.whatsapp_archive_base_url,
        },
        "feishu_notify": {
            "available": bool(settings.feishu_webhook_url),
            "configured": bool(settings.feishu_webhook_url),
        },
        "feishu_openapi_bot": {
            "available": bool(settings.feishu_app_id and settings.feishu_app_secret),
            "configured": bool(settings.feishu_app_id and settings.feishu_app_secret),
            "api_base_url": settings.feishu_api_base_url,
            "event_token_configured": bool(settings.feishu_verification_token),
            "encrypt_key_configured": bool(settings.feishu_encrypt_key),
        },
        "hko_weather_api": {
            "available": True,
            "url": "https://data.weather.gov.hk/weatherAPI/opendata/weather.php",
            "configured": True,
        },
        "hk_safety_update_sources": {
            "available": True,
            "official_sources": [
                "labour_department",
                "housing_authority",
                "development_bureau",
                "buildings_department",
                "oshc",
            ],
            "media_sources": ["hk01", "sing_tao"],
            "configured": True,
        },
        "safety_policy_templates": {
            "available": _exists(settings.safety_policy_templates_dir / "table_index.json"),
            "path": str(settings.safety_policy_templates_dir),
        },
        "safety_platform_database": {
            "available": settings.safety_database_path.exists(),
            "path": str(settings.safety_database_path),
            "configured": True,
        },
    }

    try:
        resp = requests.get(f"{settings.whatsapp_archive_base_url.rstrip('/')}/api/health", timeout=2)
        checks["whatsapp_archive"]["available"] = resp.ok
        checks["whatsapp_archive"]["status_code"] = resp.status_code
    except requests.RequestException as exc:
        checks["whatsapp_archive"]["error"] = str(exc)

    return checks


def tool_specs() -> list[ToolSpec]:
    specs = [
        ToolSpec(
            name="rtmp_snapshot",
            description="Capture one or more JPEG screenshots from an RTMP stream.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "count": {"type": "integer", "minimum": 1, "default": 1},
                    "interval": {"type": "number", "default": 5},
                    "prefix": {"type": "string", "default": "snapshot"},
                },
            },
        ),
        ToolSpec(
            name="vlm_detect",
            description="Run dual YOLO construction-site detection on an image or image directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "conf": {"type": "number"},
                    "device": {"type": "string"},
                    "worker_only": {"type": "boolean"},
                    "machinery_only": {"type": "boolean"},
                },
                "required": ["source"],
            },
        ),
        ToolSpec(
            name="whatsapp_search",
            description="Search archived WhatsApp messages through the local app-server.",
            input_schema={
                "type": "object",
                "properties": {
                    "q": {"type": "string"},
                    "chat": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["q"],
            },
        ),
        ToolSpec(
            name="whatsapp_download_media",
            description="Download WhatsApp media for a message ID through the local app-server.",
            input_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "dir": {"type": "string"},
                },
                "required": ["message_id"],
            },
        ),
        ToolSpec(
            name="whatsapp_auth_start",
            description="Start local wacli WhatsApp login. Returns QR payload and/or pairing code through status polling.",
            input_schema={
                "type": "object",
                "properties": {
                    "phone": {"type": "string", "description": "Hong Kong phone number, e.g. 91234567 or +85291234567"},
                    "mode": {"type": "string", "default": "qr"},
                    "timeout_seconds": {"type": "integer", "default": 120},
                },
            },
        ),
        ToolSpec(
            name="whatsapp_auth_status",
            description="Poll current local WhatsApp/wacli login state, including QR payload or pairing code.",
            input_schema={"type": "object", "properties": {"include_logs": {"type": "boolean", "default": True}}},
        ),
        ToolSpec(
            name="whatsapp_auth_stop",
            description="Stop the running local WhatsApp/wacli login process.",
            input_schema={"type": "object", "properties": {"reason": {"type": "string", "default": "manual_stop"}}},
        ),
        ToolSpec(
            name="whatsapp_auth_logout",
            description="Logout local WhatsApp/wacli session after human confirmation.",
            input_schema={"type": "object", "properties": {"confirmed": {"type": "boolean", "default": False}, "reason": {"type": "string", "default": "manual_logout"}}},
        ),
        ToolSpec(
            name="whatsapp_groups_wacli",
            description="List WhatsApp groups through local wacli (real connector; fails if wacli is not installed/logged in).",
            input_schema={
                "type": "object",
                "properties": {
                    "include_archived": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "default": 50},
                    "dry_run": {"type": "boolean", "default": False},
                },
            },
        ),
        ToolSpec(
            name="whatsapp_groups_refresh",
            description="Refresh joined WhatsApp groups live through local wacli and return the updated local list.",
            input_schema={"type": "object", "properties": {"dry_run": {"type": "boolean", "default": False}}},
        ),
        ToolSpec(
            name="whatsapp_send_text_confirmed",
            description="Send WhatsApp text via local wacli only after human confirmation; dry_run validates the flow without sending.",
            input_schema={
                "type": "object",
                "properties": {
                    "chat": {"type": "string"},
                    "text": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                    "dry_run": {"type": "boolean", "default": False},
                    "confirmed_by": {"type": "string"},
                },
                "required": ["chat", "text"],
            },
        ),
        ToolSpec(
            name="generate_report",
            description="Generate the existing digital employee community Word report template.",
            input_schema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string"},
                },
            },
        ),
        ToolSpec(
            name="notify_feishu",
            description="Send a text message through a configured Feishu custom bot webhook.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
        ),
        ToolSpec(
            name="feishu_get_tenant_access_token",
            description="Get a Feishu tenant_access_token using configured app_id/app_secret.",
            input_schema={"type": "object", "properties": {"force_refresh": {"type": "boolean", "default": False}}},
        ),
        ToolSpec(
            name="feishu_send_text_message",
            description="Send a text message through Feishu OpenAPI using receive_id/open_id/chat_id.",
            input_schema={
                "type": "object",
                "properties": {"receive_id": {"type": "string"}, "receive_id_type": {"type": "string", "default": "chat_id"}, "text": {"type": "string"}},
                "required": ["receive_id", "text"],
            },
        ),
        ToolSpec(
            name="feishu_send_interactive_card",
            description="Send an interactive card through Feishu OpenAPI.",
            input_schema={
                "type": "object",
                "properties": {"receive_id": {"type": "string"}, "receive_id_type": {"type": "string", "default": "chat_id"}, "card": {"type": "object"}},
                "required": ["receive_id", "card"],
            },
        ),
        ToolSpec(
            name="feishu_build_safety_review_card",
            description="Build or send a Feishu safety review card for hazard, external risk, report, or form confirmation.",
            input_schema={
                "type": "object",
                "properties": {
                    "receive_id": {"type": "string"},
                    "receive_id_type": {"type": "string", "default": "chat_id"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "risk_level": {"type": "string", "default": "medium"},
                    "actions": {"type": "array", "items": {"type": "object"}},
                    "source_case_id": {"type": "integer"},
                    "source_event_id": {"type": "integer"},
                    "send": {"type": "boolean", "default": False},
                },
                "required": ["title", "summary"],
            },
        ),
        ToolSpec(
            name="feishu_handle_event_callback",
            description="Handle Feishu event callback payloads, including URL verification challenge and event archiving.",
            input_schema={"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]},
        ),
        ToolSpec(
            name="feishu_list_chats",
            description="List Feishu chats visible to the configured bot.",
            input_schema={"type": "object", "properties": {"page_size": {"type": "integer", "default": 20}, "page_token": {"type": "string"}}},
        ),
        ToolSpec(
            name="feishu_archive_event",
            description="Archive a Feishu callback event into local SQLite.",
            input_schema={"type": "object", "properties": {"event_type": {"type": "string"}, "payload": {"type": "object"}, "status": {"type": "string", "default": "received"}}, "required": ["event_type"]},
        ),
        ToolSpec(
            name="feishu_event_to_platform_event",
            description="Convert a Feishu message/event callback into a local platform_event payload.",
            input_schema={"type": "object", "properties": {"event_payload": {"type": "object"}, "default_risk_level": {"type": "string", "default": "medium"}}, "required": ["event_payload"]},
        ),
        ToolSpec(
            name="fetch_hko_weather",
            description="Fetch Hong Kong Observatory Open Data API weather reports, warnings, tips, and forecasts.",
            input_schema={
                "type": "object",
                "properties": {
                    "lang": {"type": "string", "default": "tc", "enum": ["en", "tc", "sc"]},
                    "data_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["rhrread", "warnsum", "warningInfo", "swt", "flw", "fnd"],
                    },
                    "timeout_seconds": {"type": "number", "default": 10},
                },
            },
        ),
        ToolSpec(
            name="fetch_hk_safety_updates",
            description="Fetch construction-safety-related updates from approved Hong Kong government and media sources.",
            input_schema={
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [
                            "labour_department",
                            "housing_authority",
                            "development_bureau",
                            "buildings_department",
                            "oshc",
                            "hk01",
                            "sing_tao",
                        ],
                    },
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "limit_per_source": {"type": "integer", "default": 10},
                    "timeout_seconds": {"type": "number", "default": 10},
                },
            },
        ),
        ToolSpec(
            name="fetch_hk_industrial_news",
            description="Fetch industrial-accident news only from approved Hong Kong media sources: HK01 and Sing Tao.",
            input_schema={
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["hk01", "sing_tao"],
                    },
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "limit_per_source": {"type": "integer", "default": 10},
                    "timeout_seconds": {"type": "number", "default": 10},
                },
            },
        ),
        ToolSpec(
            name="persist_external_risk_items",
            description="Persist fetched weather warnings, government updates, and media risk items into local SQLite.",
            input_schema={
                "type": "object",
                "properties": {
                    "weather_result": {"type": "object"},
                    "safety_updates_result": {"type": "object"},
                    "items": {"type": "array", "items": {"type": "object"}},
                    "source_batch": {"type": "string", "default": "manual"},
                },
            },
        ),
        ToolSpec(
            name="summarize_external_risks",
            description="Create a rule-based summary of external weather, official, and media safety risks.",
            input_schema={
                "type": "object",
                "properties": {
                    "weather_result": {"type": "object"},
                    "safety_updates_result": {"type": "object"},
                    "items": {"type": "array", "items": {"type": "object"}},
                    "include_recommended_actions": {"type": "boolean", "default": True},
                },
            },
        ),
        ToolSpec(
            name="draft_daily_risk_briefing",
            description="Draft a daily external-risk briefing in Markdown from weather and safety update inputs.",
            input_schema={
                "type": "object",
                "properties": {
                    "weather_result": {"type": "object"},
                    "safety_updates_result": {"type": "object"},
                    "items": {"type": "array", "items": {"type": "object"}},
                    "project_name": {"type": "string"},
                    "audience": {"type": "string", "default": "site_safety_team"},
                    "language": {"type": "string", "default": "zh-HK"},
                },
            },
        ),
        ToolSpec(
            name="link_external_risk_to_forms",
            description="Suggest safety form templates for external weather, government, or media risk items.",
            input_schema={
                "type": "object",
                "properties": {
                    "weather_result": {"type": "object"},
                    "safety_updates_result": {"type": "object"},
                    "items": {"type": "array", "items": {"type": "object"}},
                    "limit_per_risk": {"type": "integer", "default": 5},
                },
            },
        ),
        ToolSpec(
            name="search_form_templates",
            description="Search extracted safety policy form templates by keyword, scene, or template ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "scene": {"type": "string"},
                    "template_ids": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        ToolSpec(
            name="get_form_template_detail",
            description="Read one extracted form template detail, including JSON cells and optional Markdown preview.",
            input_schema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string"},
                    "include_cells": {"type": "boolean", "default": True},
                    "include_markdown": {"type": "boolean", "default": False},
                },
                "required": ["template_id"],
            },
        ),
        ToolSpec(
            name="suggest_forms_for_case",
            description="Suggest form templates for a safety scene, risk level, case ID, or case description.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "case_id": {"type": "integer"},
                    "description": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        ),
        ToolSpec(
            name="prefill_form_fields",
            description="Create candidate field JSON for a selected form template from text and known fields.",
            input_schema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string"},
                    "source_text": {"type": "string"},
                    "case_id": {"type": "integer"},
                    "known_fields": {"type": "object"},
                },
                "required": ["template_id"],
            },
        ),
        ToolSpec(
            name="generate_docx_from_template",
            description="Generate a first-pass DOCX draft by copying an extracted template and saving field payload JSON.",
            input_schema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string"},
                    "fields": {"type": "object"},
                    "output_path": {"type": "string"},
                    "case_id": {"type": "integer"},
                    "record": {"type": "boolean", "default": True},
                },
                "required": ["template_id"],
            },
        ),
        ToolSpec(
            name="export_form_record",
            description="Record a form generation or draft payload in local SQLite.",
            input_schema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string"},
                    "payload": {"type": "object"},
                    "case_id": {"type": "integer"},
                    "output_path": {"type": "string"},
                    "status": {"type": "string", "default": "draft"},
                },
                "required": ["template_id"],
            },
        ),
        ToolSpec(
            name="create_safety_case",
            description="Create or reuse a local safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "scene": {"type": "string"},
                    "risk_level": {"type": "string", "default": "medium"},
                    "area": {"type": "string"},
                    "contractor": {"type": "string"},
                    "source_type": {"type": "string", "default": "manual"},
                    "source_id": {"type": "string"},
                    "recommended_action": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["description"],
            },
        ),
        ToolSpec(
            name="update_safety_case_status",
            description="Update a safety case status and record the action.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["case_id", "status"],
            },
        ),
        ToolSpec(
            name="assign_safety_case",
            description="Assign a safety case to a responsible person, contractor, due date, or priority.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "assignee": {"type": "string"},
                    "contractor": {"type": "string"},
                    "due_date": {"type": "string"},
                    "priority": {"type": "string"},
                },
                "required": ["case_id"],
            },
        ),
        ToolSpec(
            name="add_case_evidence",
            description="Add file, chat, image, or video evidence to a safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "path": {"type": "string"},
                    "kind": {"type": "string", "default": "file"},
                    "source_type": {"type": "string", "default": "manual"},
                    "source_id": {"type": "string"},
                    "metadata": {"type": "object"},
                },
                "required": ["case_id", "path"],
            },
        ),
        ToolSpec(
            name="generate_rectification_notice",
            description="Generate a rectification notice draft for a safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "language": {"type": "string", "default": "zh-HK"},
                    "tone": {"type": "string", "default": "formal"},
                },
                "required": ["case_id"],
            },
        ),
        ToolSpec(
            name="generate_warning_letter",
            description="Generate a warning letter draft for a safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "language": {"type": "string", "default": "zh-HK"},
                    "tone": {"type": "string", "default": "formal"},
                },
                "required": ["case_id"],
            },
        ),
        ToolSpec(
            name="close_case_with_review",
            description="Close a safety case after review notes and optional review evidence.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "review_notes": {"type": "string"},
                    "reviewer": {"type": "string"},
                    "evidence_paths": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["case_id", "review_notes"],
            },
        ),
        ToolSpec(
            name="query_safety_cases",
            description="Query local safety cases for tables and dashboards.",
            input_schema={"type": "object", "properties": {"status": {"type": "string"}, "scene": {"type": "string"}, "risk_level": {"type": "string"}, "limit": {"type": "integer", "default": 50}}},
        ),
        ToolSpec(
            name="query_external_risks",
            description="Query persisted external weather, government, and media risk items.",
            input_schema={"type": "object", "properties": {"source": {"type": "string"}, "risk_level": {"type": "string"}, "limit": {"type": "integer", "default": 50}}},
        ),
        ToolSpec(
            name="query_form_records",
            description="Query local form generation records.",
            input_schema={"type": "object", "properties": {"template_id": {"type": "string"}, "case_id": {"type": "integer"}, "limit": {"type": "integer", "default": 50}}},
        ),
        ToolSpec(
            name="query_pending_actions",
            description="Query pending safety cases that need confirmation, rectification, or review.",
            input_schema={"type": "object", "properties": {"limit": {"type": "integer", "default": 100}}},
        ),
        ToolSpec(
            name="get_dashboard_metrics",
            description="Build local dashboard metrics for safety cases, external risks, and form records.",
            input_schema={"type": "object", "properties": {"include_samples": {"type": "boolean", "default": True}}},
        ),
        ToolSpec(
            name="export_safety_data",
            description="Export selected local safety data to JSON or CSV under the workspace task folder.",
            input_schema={"type": "object", "properties": {"table": {"type": "string", "default": "safety_cases"}, "format": {"type": "string", "default": "json"}, "limit": {"type": "integer", "default": 500}}},
        ),
        ToolSpec(
            name="list_whatsapp_groups",
            description="List WhatsApp groups. Placeholder until ChitongLingxun/wacli is wired.",
            input_schema={"type": "object", "properties": {"include_archived": {"type": "boolean", "default": False}}},
        ),
        ToolSpec(
            name="draft_group_message",
            description="Create a group message draft requiring human confirmation before sending.",
            input_schema={"type": "object", "properties": {"recipients": {"type": "array", "items": {"type": "string"}}, "subject": {"type": "string"}, "body": {"type": "string"}, "source_case_id": {"type": "integer"}, "source_risk_id": {"type": "integer"}, "channel": {"type": "string", "default": "whatsapp"}}, "required": ["body"]},
        ),
        ToolSpec(
            name="send_group_message_with_confirm",
            description="Confirm a message draft. Real sender is reserved for later integration.",
            input_schema={"type": "object", "properties": {"draft_id": {"type": "integer"}, "confirmed": {"type": "boolean", "default": False}, "confirmed_by": {"type": "string"}}, "required": ["draft_id"]},
        ),
        ToolSpec(
            name="archive_sent_notification",
            description="Archive a notification send record locally.",
            input_schema={"type": "object", "properties": {"channel": {"type": "string"}, "recipients": {"type": "array", "items": {"type": "string"}}, "text": {"type": "string"}, "status": {"type": "string", "default": "sent"}, "metadata": {"type": "object"}}, "required": ["channel", "text"]},
        ),
        ToolSpec(
            name="extract_hazards_from_recent_chats",
            description="Placeholder workflow for extracting hazards from recent chat messages.",
            input_schema={"type": "object", "properties": {"q": {"type": "string"}, "chat": {"type": "string"}, "limit": {"type": "integer", "default": 50}}},
        ),
        ToolSpec(
            name="summarize_chat_group_daily",
            description="Placeholder daily chat summary for a WhatsApp or project group.",
            input_schema={"type": "object", "properties": {"chat": {"type": "string"}, "date": {"type": "string"}, "limit": {"type": "integer", "default": 100}}},
        ),
        ToolSpec(
            name="capture_camera_snapshot",
            description="Capture CCTV/RTMP snapshots through the existing RTMP snapshot tool.",
            input_schema={"type": "object", "properties": {"url": {"type": "string"}, "count": {"type": "integer", "default": 1}, "interval": {"type": "number", "default": 5}, "prefix": {"type": "string", "default": "camera_snapshot"}}},
        ),
        ToolSpec(
            name="run_vlm_detection_batch",
            description="Run VLM detection on an image or directory through the existing detector.",
            input_schema={"type": "object", "properties": {"source": {"type": "string"}, "conf": {"type": "number"}, "device": {"type": "string"}, "worker_only": {"type": "boolean"}, "machinery_only": {"type": "boolean"}}, "required": ["source"]},
        ),
        ToolSpec(
            name="classify_vlm_hazard",
            description="Convert VLM detections into safety hazard candidates.",
            input_schema={"type": "object", "properties": {"detections": {"type": "object"}, "vlm_result_path": {"type": "string"}, "task_id": {"type": "string"}, "image_path": {"type": "string"}, "area": {"type": "string"}, "contractor": {"type": "string"}}},
        ),
        ToolSpec(
            name="create_case_from_vlm",
            description="Create a safety case from VLM visual hazard output.",
            input_schema={"type": "object", "properties": {"detections": {"type": "object"}, "vlm_result_path": {"type": "string"}, "task_id": {"type": "string"}, "image_path": {"type": "string"}, "area": {"type": "string"}, "contractor": {"type": "string"}, "description": {"type": "string"}}},
        ),
        ToolSpec(
            name="compare_vlm_before_after",
            description="Placeholder for before/after rectification image comparison.",
            input_schema={"type": "object", "properties": {"before_image": {"type": "string"}, "after_image": {"type": "string"}, "notes": {"type": "string"}}, "required": ["before_image", "after_image"]},
        ),
        ToolSpec(
            name="schedule_camera_patrol",
            description="Placeholder for scheduled camera patrol jobs.",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}, "camera_urls": {"type": "array", "items": {"type": "string"}}, "cron": {"type": "string", "default": "0 8 * * *"}, "enabled": {"type": "boolean", "default": False}}, "required": ["name"]},
        ),
        ToolSpec(
            name="ocr_document_or_image",
            description="Placeholder OCR for images/PDFs. Reserved for PaddleOCR/RapidOCR integration.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}, "engine": {"type": "string", "default": "reserved"}}, "required": ["path"]},
        ),
        ToolSpec(
            name="extract_tables_from_document",
            description="Placeholder table extraction for PDF/Word documents.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}, "engine": {"type": "string", "default": "reserved"}}, "required": ["path"]},
        ),
        ToolSpec(
            name="classify_document_type",
            description="Rule-based document type classifier for certificates, forms, letters, and policies.",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}, "path": {"type": "string"}}},
        ),
        ToolSpec(
            name="extract_certificate_fields",
            description="Extract candidate certificate fields and dates from text.",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}, "path": {"type": "string"}}},
        ),
        ToolSpec(
            name="check_certificate_expiry",
            description="Check certificate expiry dates and warning windows.",
            input_schema={"type": "object", "properties": {"certificates": {"type": "array", "items": {"type": "object"}}, "warning_days": {"type": "integer", "default": 30}}},
        ),
        ToolSpec(
            name="summarize_policy_document",
            description="Prepare policy document summary source text from the extracted safety policy full text.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}, "max_chars": {"type": "integer", "default": 2000}}},
        ),
        ToolSpec(
            name="search_policy_clauses",
            description="Search extracted safety policy text for relevant clauses and snippets.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}, "context_chars": {"type": "integer", "default": 120}}, "required": ["query"]},
        ),
        ToolSpec(
            name="record_tool_audit",
            description="Record a local audit entry for a tool call.",
            input_schema={"type": "object", "properties": {"tool_name": {"type": "string"}, "user_id": {"type": "string"}, "channel": {"type": "string"}, "input_summary": {"type": "object"}, "output_summary": {"type": "object"}, "status": {"type": "string", "default": "ok"}}, "required": ["tool_name"]},
        ),
        ToolSpec(
            name="record_llm_audit",
            description="Record a local audit entry for an LLM call.",
            input_schema={"type": "object", "properties": {"provider": {"type": "string"}, "model": {"type": "string"}, "user_id": {"type": "string"}, "prompt_summary": {"type": "object"}, "response_summary": {"type": "object"}, "sanitized": {"type": "boolean", "default": True}, "status": {"type": "string", "default": "ok"}}},
        ),
        ToolSpec(
            name="list_audit_logs",
            description="List local audit logs.",
            input_schema={"type": "object", "properties": {"event_type": {"type": "string"}, "user_id": {"type": "string"}, "limit": {"type": "integer", "default": 100}}},
        ),
        ToolSpec(
            name="manage_user_roles",
            description="Create or update a local user role.",
            input_schema={"type": "object", "properties": {"user_id": {"type": "string"}, "role": {"type": "string"}, "display_name": {"type": "string"}}, "required": ["user_id", "role"]},
        ),
        ToolSpec(
            name="check_action_permission",
            description="Check whether a local user role may perform an action.",
            input_schema={"type": "object", "properties": {"user_id": {"type": "string"}, "action": {"type": "string"}, "default_role": {"type": "string", "default": "viewer"}}, "required": ["user_id", "action"]},
        ),
        ToolSpec(
            name="list_prompt_templates",
            description="List local prompt templates used for LLM-assisted classification and drafting.",
            input_schema={"type": "object", "properties": {}},
        ),
        ToolSpec(
            name="render_prompt_template",
            description="Render a local prompt template with simple variables.",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}, "variables": {"type": "object"}}, "required": ["name"]},
        ),
        ToolSpec(
            name="list_reference_adapters",
            description="List adapter interfaces inspired by selected open-source construction safety projects.",
            input_schema={"type": "object", "properties": {}},
        ),
        ToolSpec(
            name="map_mcp_construction_tool",
            description="Map an MCP-construction style workflow to local Chitung/AgentToolbox tools.",
            input_schema={"type": "object", "properties": {"workflow": {"type": "string"}, "include_schema_hint": {"type": "boolean", "default": True}}, "required": ["workflow"]},
        ),
        ToolSpec(
            name="normalize_visual_safety_event",
            description="Normalize visual safety events from HazardLens/PPE Detection/SafetyVision style outputs.",
            input_schema={"type": "object", "properties": {"source_project": {"type": "string"}, "camera_id": {"type": "string"}, "image_path": {"type": "string"}, "timestamp": {"type": "string"}, "detections": {"type": "array", "items": {"type": "object"}}, "raw_event": {"type": "object"}}},
        ),
        ToolSpec(
            name="evaluate_hazard_zone_rules",
            description="Evaluate restricted-zone and person-equipment proximity rules inspired by Construction-Hazard-Detection.",
            input_schema={"type": "object", "properties": {"persons": {"type": "array", "items": {"type": "object"}}, "equipment": {"type": "array", "items": {"type": "object"}}, "restricted_zones": {"type": "array", "items": {"type": "object"}}, "min_person_equipment_distance": {"type": "number", "default": 80}, "coordinate_unit": {"type": "string", "default": "pixel"}}},
        ),
        ToolSpec(
            name="recommend_visual_safety_pipeline",
            description="Recommend a future visual-safety implementation path using the selected reference projects.",
            input_schema={"type": "object", "properties": {"scenario": {"type": "string", "default": "ppe"}, "deployment": {"type": "string", "default": "local"}, "priority": {"type": "string", "default": "fast_mvp"}}},
        ),
        ToolSpec(
            name="draft_safety_report_from_events",
            description="Draft a SafetyVision-style safety report from normalized events.",
            input_schema={"type": "object", "properties": {"events": {"type": "array", "items": {"type": "object"}}, "project_name": {"type": "string"}, "report_type": {"type": "string", "default": "visual_safety"}, "include_recommendations": {"type": "boolean", "default": True}}},
        ),
        ToolSpec(
            name="init_safety_database",
            description="Initialize the local SQLite database for safety hazards, classifications, evidence, forms, and feedback.",
            input_schema={
                "type": "object",
                "properties": {
                    "reset": {"type": "boolean", "default": False},
                },
            },
        ),
        ToolSpec(
            name="ai_archive_classifier",
            description="Classify text, document notes, attachments, or VLM summaries into safety scenes and optionally persist a safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_type": {"type": "string", "default": "manual_input"},
                    "source_id": {"type": "string"},
                    "time": {"type": "string"},
                    "area": {"type": "string"},
                    "contractor": {"type": "string"},
                    "description": {"type": "string"},
                    "text": {"type": "string"},
                    "evidence_files": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"},
                    "raw_payload": {"type": "object"},
                    "persist": {"type": "boolean", "default": True},
                    "create_case": {"type": "boolean", "default": True},
                },
            },
        ),
        ToolSpec(
            name="ingest_chat_hazards",
            description="Ingest ChitongLingxun or WhatsApp-like chat messages and extract safety hazard candidates.",
            input_schema={
                "type": "object",
                "properties": {
                    "messages": {"type": "array", "items": {"type": "object"}},
                    "q": {"type": "string"},
                    "chat": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                    "persist": {"type": "boolean", "default": True},
                },
            },
        ),
        ToolSpec(
            name="ingest_vlm_hazards",
            description="Convert VLM-Detection JSON output into visual safety hazard candidates.",
            input_schema={
                "type": "object",
                "properties": {
                    "detections": {"type": "object"},
                    "vlm_result_path": {"type": "string"},
                    "task_id": {"type": "string"},
                    "image_path": {"type": "string"},
                    "area": {"type": "string"},
                    "contractor": {"type": "string"},
                    "persist": {"type": "boolean", "default": True},
                },
            },
        ),
        ToolSpec(
            name="dedupe_and_link_hazards",
            description="Find and mark potential duplicate safety cases by scene, area, and contractor, merging evidence into the keeper case.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        ToolSpec(
            name="connect_hazard_actions",
            description="Create follow-up action suggestions and form suggestions from confirmed or candidate safety cases.",
            input_schema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer"},
                    "status": {"type": "string", "default": "candidate"},
                    "create_form_suggestions": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        ToolSpec(
            name="record_classification_feedback",
            description="Record manual correction or confirmation for an AI classification or safety case.",
            input_schema={
                "type": "object",
                "properties": {
                    "classification_id": {"type": "integer"},
                    "case_id": {"type": "integer"},
                    "corrected_scene": {"type": "string"},
                    "corrected_risk_level": {"type": "string"},
                    "corrected_status": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
        ),
    ]
    return (
        specs
        + ALL_DOCMATE_SPECS
        + CONFIRMATION_TOOL_SPECS
        + FEISHU_EVENT_TOOL_SPECS
        + future_tool_specs()
        + workflow_tool_specs()
    )

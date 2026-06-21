from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from ..config import settings
from ..models import ToolResult
from .whatsapp import WhatsAppWacliGroupsRequest, list_groups_wacli


class WhatsAppGroupListRequest(BaseModel):
    include_archived: bool = False


class GroupMessageDraftRequest(BaseModel):
    recipients: list[str] = Field(default_factory=list)
    subject: str | None = None
    body: str
    source_case_id: int | None = None
    source_risk_id: int | None = None
    channel: str = "whatsapp"


class ConfirmedSendRequest(BaseModel):
    draft_id: int
    confirmed: bool = False
    confirmed_by: str | None = None


class NotificationArchiveRequest(BaseModel):
    channel: str
    recipients: list[str] = Field(default_factory=list)
    text: str
    status: str = "sent"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecentChatHazardRequest(BaseModel):
    q: str = "隐患 OR 整改 OR 工伤 OR 意外"
    chat: str | None = None
    limit: int = 50


class ChatGroupDailySummaryRequest(BaseModel):
    chat: str | None = None
    date: str | None = None
    limit: int = 100


def list_whatsapp_groups(req: WhatsAppGroupListRequest) -> ToolResult:
    wacli = list_groups_wacli(
        WhatsAppWacliGroupsRequest(include_archived=req.include_archived, limit=200)
    )
    if wacli.ok:
        wacli.tool = "list_whatsapp_groups"
        return wacli
    groups = [
        {"id": "placeholder-safety-group", "name": "安全管理群（占位）", "source": "placeholder"},
        {"id": "placeholder-project-group", "name": "项目管理群（占位）", "source": "placeholder"},
    ]
    return ToolResult(
        ok=True,
        tool="list_whatsapp_groups",
        summary="Returned placeholder groups. Wire to ChitongLingxun/wacli later.",
        data={"items": groups, "include_archived": req.include_archived},
    )


def draft_group_message(req: GroupMessageDraftRequest) -> ToolResult:
    _ensure_comm_schema()
    now = _now()
    text = f"{req.subject}\n\n{req.body}" if req.subject else req.body
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notification_drafts (
                channel, recipients_json, subject, body, source_case_id, source_risk_id,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """,
            (
                req.channel,
                json.dumps(req.recipients, ensure_ascii=False),
                req.subject,
                req.body,
                req.source_case_id,
                req.source_risk_id,
                now,
                now,
            ),
        )
        draft_id = int(cursor.lastrowid)
    return ToolResult(
        ok=True,
        tool="draft_group_message",
        summary=f"Created message draft {draft_id}.",
        data={"draft_id": draft_id, "text": text, "requires_human_confirmation": True},
    )


def send_group_message_with_confirm(req: ConfirmedSendRequest) -> ToolResult:
    _ensure_comm_schema()
    if not req.confirmed:
        return ToolResult(ok=False, tool="send_group_message_with_confirm", summary="Human confirmation is required.", data=req.model_dump(), error="confirmed must be true")
    now = _now()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM notification_drafts WHERE id = ?", (req.draft_id,)).fetchone()
        if row is None:
            raise ValueError(f"Draft not found: {req.draft_id}")
        conn.execute("UPDATE notification_drafts SET status = 'confirmed_pending_sender', updated_at = ? WHERE id = ?", (now, req.draft_id))
        conn.execute(
            """
            INSERT INTO notification_records (channel, recipients_json, text, status, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["channel"],
                row["recipients_json"],
                row["body"],
                "confirmed_pending_sender",
                json.dumps({"draft_id": req.draft_id, "confirmed_by": req.confirmed_by}, ensure_ascii=False),
                now,
            ),
        )
    return ToolResult(
        ok=True,
        tool="send_group_message_with_confirm",
        summary="Draft confirmed and archived. Real sender is not wired yet.",
        data={"draft_id": req.draft_id, "status": "confirmed_pending_sender"},
    )


def archive_sent_notification(req: NotificationArchiveRequest) -> ToolResult:
    _ensure_comm_schema()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notification_records (channel, recipients_json, text, status, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                req.channel,
                json.dumps(req.recipients, ensure_ascii=False),
                req.text,
                req.status,
                json.dumps(req.metadata, ensure_ascii=False, sort_keys=True),
                _now(),
            ),
        )
        record_id = int(cursor.lastrowid)
    return ToolResult(ok=True, tool="archive_sent_notification", summary=f"Archived notification {record_id}.", data={"record_id": record_id})


def extract_hazards_from_recent_chats(req: RecentChatHazardRequest) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="extract_hazards_from_recent_chats",
        summary="Placeholder: call ingest_chat_hazards or WhatsApp archive search in the next integration pass.",
        data=req.model_dump(),
    )


def summarize_chat_group_daily(req: ChatGroupDailySummaryRequest) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="summarize_chat_group_daily",
        summary="Placeholder daily chat summary.",
        data={
            "chat": req.chat,
            "date": req.date,
            "summary": "今日聊天摘要功能已预留，后续接入赤瞳灵讯聊天库后生成。",
            "limit": req.limit,
        },
    )


def _ensure_comm_schema() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notification_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                recipients_json TEXT NOT NULL DEFAULT '[]',
                subject TEXT,
                body TEXT,
                source_case_id INTEGER,
                source_risk_id INTEGER,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notification_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                recipients_json TEXT NOT NULL DEFAULT '[]',
                text TEXT,
                status TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            """
        )


def _connect() -> sqlite3.Connection:
    path = settings.safety_database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

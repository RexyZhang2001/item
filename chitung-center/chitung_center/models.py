from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


IntentName = Literal[
    "hazard_intake",
    "visual_detection",
    "document_form",
    "weather_news_risk",
    "knowledge_query",
    "general_chat",
]


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    channel: str = "local_web"
    user_id: str = "local_user"
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntentResult(BaseModel):
    intent: IntentName
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    suggested_tools: list[str] = Field(default_factory=list)


class ActionCard(BaseModel):
    card_type: str
    title: str
    summary: str
    actions: list[dict[str, Any]] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    reply: str
    intent: IntentResult
    cards: list[ActionCard] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    audit_id: str
    applied_skill: Optional[dict[str, Any]] = None


class CardActionRequest(BaseModel):
    action_id: str
    card_data: dict[str, Any] = Field(default_factory=dict)
    user_id: str = "local_user"
    channel: str = "local_web"


class ConfirmationResolveApiRequest(BaseModel):
    confirmation_id: str
    decision: Literal["approve", "reject"]
    user_id: str = "local_user"
    notes: str | None = None


class FeishuEventWebhookRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunRequest(BaseModel):
    workflow_name: str = Field(min_length=1)
    message: str = Field(min_length=1)
    channel: str = "local_web"
    user_id: str = "local_user"
    metadata: dict[str, Any] = Field(default_factory=dict)


class HazardStatusUpdateRequest(BaseModel):
    status: str = "confirmed"
    notes: str | None = None


class DocumentRevisionRequest(BaseModel):
    title: str = "AI 文档改写预览"
    source: str = "chitung-center"
    instruction: str
    original_text: str
    revised_text: str | None = None


class SmartFormDraftRequest(BaseModel):
    query: str
    source_text: str
    template_id: str | None = None
    case_id: int | None = None
    known_fields: dict[str, Any] = Field(default_factory=dict)
    instruction: str = "生成安全表格草稿，并保留人工采纳确认。"


class SmartFormAcceptRequest(BaseModel):
    template_id: str
    fields: dict[str, Any] = Field(default_factory=dict)
    output_path: str | None = None
    case_id: int | None = None
    notes: str | None = None


class VisualPatrolDraftRequest(BaseModel):
    camera_id: str | None = None
    camera_url: str | None = None
    source: str | None = None
    area: str | None = None
    contractor: str | None = None
    count: int = 1
    conf: float | None = None
    analysis_mode: Literal["yolo_only", "hybrid"] = "hybrid"
    yolo_conf_threshold: float = 0.45
    vlm_enabled: bool = True
    use_guardian_pipeline: bool = False


class VisualPatrolBatchRequest(BaseModel):
    camera_id: str | None = None
    vlm_enabled: bool = True
    yolo_only: bool = False


class VisualPatrolConfirmRequest(BaseModel):
    detections: dict[str, Any] | None = None
    vlm_result_path: str | None = None
    task_id: str | None = None
    image_path: str | None = None
    area: str | None = None
    contractor: str | None = None
    description: str | None = None


class CaseWorkflowRequest(BaseModel):
    case_id: int
    contractor: str | None = None
    due_date: str | None = None
    notes: str | None = None
    reviewer: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class ReportGenerateRequest(BaseModel):
    report_type: Literal["community", "daily_safety", "rectification"] = "daily_safety"
    case_id: int | None = None
    title: str | None = None


class NotificationSendRequest(BaseModel):
    case_id: int
    text: str
    contractor: str | None = None
    channel: Literal["feishu", "whatsapp"] = "feishu"
    confirmed_by: str = "desktop_user"


class LlmSettingsRequest(BaseModel):
    base_url: str
    api_key: str
    model: str


class ConnectorSettingsRequest(BaseModel):
    whatsapp_archive_base_url: str = ""
    feishu_webhook_url: str = ""
    feishu_webhook_secret: str = ""
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_encrypt_key: str = ""
    feishu_api_base_url: str = "https://open.feishu.cn"


class ProjectConfig(BaseModel):
    name: str = "赤瞳示范项目"
    default_area: str = "B2"
    location: str = "Hong Kong"


class CameraConfig(BaseModel):
    id: str
    name: str
    area: str
    rtmp_url: str | None = None
    enabled: bool = True


class ContractorConfig(BaseModel):
    id: str
    name: str
    contact: str | None = None
    channel: str | None = None
    default_due_days: int = 3


class AppConfigRequest(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    cameras: list[CameraConfig] = Field(default_factory=list)
    contractors: list[ContractorConfig] = Field(default_factory=list)


class IntegrationStatus(BaseModel):
    name: str
    display_name: str
    enabled: bool
    category: str
    notes: str


class ToolCallPlan(BaseModel):
    tool_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class SkillEnableRequest(BaseModel):
    enabled: bool


class SkillImportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    content: str = Field(..., min_length=1)


class WorkflowEnableRequest(BaseModel):
    enabled: bool


class WorkflowImportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    content: str = Field(..., min_length=1)


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    collection: str | None = Field(default=None, max_length=80)


class WhatsAppSearchApiRequest(BaseModel):
    q: str = Field(min_length=1)
    chat: str | None = None
    limit: int = Field(default=20, ge=1, le=200)


class WhatsAppGroupsApiRequest(BaseModel):
    include_archived: bool = False


PlanStatus = Literal[
    "DRAFT",
    "PLANNED",
    "PENDING_CONFIRMATION",
    "CONFIRMED",
    "EXECUTING",
    "SUCCEEDED",
    "FAILED",
]


RiskLevelName = Literal["low", "medium", "high", "critical"]


class HybridPlanRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    prefer_codex: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class HybridActionView(BaseModel):
    action_id: str
    sequence_no: int
    tool_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevelName = "medium"
    requires_confirmation: bool = True
    status: str
    retry_count: int = 0
    max_retries: int = 2
    result: dict[str, Any] = Field(default_factory=dict)
    last_error: str | None = None


class HybridPlanView(BaseModel):
    plan_id: str
    session_id: str
    user_input: str
    workflow: str
    planner_mode: str
    status: PlanStatus
    fallback_used: bool = False
    fallback_reason: str | None = None
    selected_action_ids: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    last_error: str | None = None
    created_at: str
    updated_at: str
    actions: list[HybridActionView] = Field(default_factory=list)


class HybridPlanResponse(BaseModel):
    ok: bool = True
    audit_id: str
    plan: HybridPlanView


class HybridConfirmRequest(BaseModel):
    session_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    action_ids: list[str] = Field(default_factory=list)
    confirmed_by: str = "local_user"
    notes: str | None = None


class HybridExecuteRequest(BaseModel):
    session_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    idempotency_key: str | None = None
    retry_failed_only: bool = True
    dry_run: bool = False


class HybridExecuteResponse(BaseModel):
    ok: bool
    audit_id: str
    idempotent_hit: bool = False
    plan: HybridPlanView
    action_results: list[dict[str, Any]] = Field(default_factory=list)


class AuditEventRequest(BaseModel):
    event_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    plan_id: str | None = None
    action_id: str | None = None
    status: str | None = None


class AuditEventResponse(BaseModel):
    ok: bool = True
    audit_id: str


# ── DocMate (闪闪文档) 模型 ──────────────────────────────────────

class DocmateReadRequest(BaseModel):
    file_path: str = Field(..., description=".docx 文件路径")


class DocmateGenerateRequest(BaseModel):
    doc_id: str = Field(..., description="文档 ID")
    instruction: str = Field(..., description="用户编辑指令")
    context: Optional[str] = Field(default=None, description="额外上下文（文本）")


class DocmatePreviewRequest(BaseModel):
    changeset_id: str = Field(..., description="ChangeSet ID")


class DocmateApplyRequest(BaseModel):
    changeset_id: str = Field(..., description="ChangeSet ID")
    accepted_change_ids: list[str] = Field(default_factory=list, description="接受的变更 ID")
    save_as: Optional[str] = Field(default=None, description="输出文件路径（可选，默认 source_modified.docx）")


class DocmatePipelineRequest(BaseModel):
    file_path: str = Field(..., description=".docx 文件路径")
    instruction: str = Field(..., description="用户编辑指令")
    save_as: Optional[str] = Field(default=None, description="输出文件路径（可选）")
    context: Optional[str] = Field(default=None, description="额外上下文（文本）")


class TableMappingExtractRequest(BaseModel):
    file_path: str = Field(..., description=".docx 文件路径")
    form_id: str = Field(..., description="C-SMART 表单 ID，如 4.2")


class TableMappingRunRequest(BaseModel):
    file_path: str = Field(..., description=".docx 文件路径")
    form_id: str = Field(..., description="C-SMART 表单 ID，如 4.2")
    fields: dict[str, str] | None = Field(default=None, description="用户确认后的字段值；为空时自动抽取")
    action: str = Field(default="draft", description="当前支持 draft/save_draft")
    screenshot: bool = Field(default=True, description="执行后保存截图")
    dry_run: bool = Field(default=False, description="只预览命令和映射，不执行 Playwright")


# ── Yaoyao structured input models ─────────────────────────────


class YaoyaoRegion(BaseModel):
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0


class YaoyaoStructuredDraftRequest(BaseModel):
    file_path: str
    page_index: int | None = None
    regions: list[YaoyaoRegion] = Field(default_factory=list)
    template_id: str | None = None
    case_id: int | None = None
    render_width: int = 2000
    render_height: int = 2800


class YaoyaoFieldCandidate(BaseModel):
    field_name: str
    value: str = ""
    confidence: float = 0.0
    source_region: str = ""
    page_number: int = 1


class YaoyaoStructuredDraftResponse(BaseModel):
    ok: bool = True
    draft_id: str
    preview_image_path: str | None = None
    regions: list[dict[str, Any]] = Field(default_factory=list)
    field_candidates: list[YaoyaoFieldCandidate] = Field(default_factory=list)
    requires_acceptance: bool = True
    confirm_payload: dict[str, Any] = Field(default_factory=dict)


class YaoyaoTemplateSaveRequest(BaseModel):
    regions: list[YaoyaoRegion] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    name: str | None = None
    template_id: str | None = None


class YaoyaoTemplateLoadRequest(BaseModel):
    template_id: str


class YaoyaoConfirmRequest(BaseModel):
    draft_id: str
    fields: dict[str, Any] = Field(default_factory=dict)
    template_id: str | None = None
    case_id: int | None = None
    notes: str | None = None

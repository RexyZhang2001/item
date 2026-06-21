from __future__ import annotations

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Any

from .config import settings
from .models import HealthResult
from .registry import health_checks, tool_specs
from .mcp_server import _call_tool
from .tasks import ensure_workspace
from .tools.audit_permissions import (
    ActionPermissionCheckRequest,
    AuditLogQueryRequest,
    LlmAuditRecordRequest,
    ToolAuditRecordRequest,
    UserRoleManageRequest,
    check_action_permission,
    list_audit_logs,
    manage_user_roles,
    record_llm_audit,
    record_tool_audit,
)
from .tools.communications import (
    ChatGroupDailySummaryRequest,
    ConfirmedSendRequest,
    GroupMessageDraftRequest,
    NotificationArchiveRequest,
    RecentChatHazardRequest,
    WhatsAppGroupListRequest,
    archive_sent_notification,
    draft_group_message,
    extract_hazards_from_recent_chats,
    list_whatsapp_groups,
    send_group_message_with_confirm,
    summarize_chat_group_daily,
)
from .tools.documents_ocr import (
    CertificateExpiryCheckRequest,
    CertificateFieldExtractRequest,
    DocumentTypeClassifyRequest,
    OcrDocumentRequest,
    PolicyClauseSearchRequest,
    PolicyDocumentSummarizeRequest,
    TableExtractionRequest,
    check_certificate_expiry,
    classify_document_type,
    extract_certificate_fields,
    extract_tables_from_document,
    ocr_document_or_image,
    search_policy_clauses,
    summarize_policy_document,
)
from .tools.case_management import (
    CaseCloseReviewRequest,
    CaseDraftRequest,
    CaseEvidenceRequest,
    SafetyCaseAssignRequest,
    SafetyCaseCreateRequest,
    SafetyCaseStatusRequest,
    add_case_evidence,
    assign_safety_case,
    close_case_with_review,
    create_safety_case,
    generate_rectification_notice,
    generate_warning_letter,
    update_safety_case_status,
)
from .tools.external_risk import (
    DailyRiskBriefingRequest,
    ExternalRiskFetchRequest,
    ExternalRiskPersistRequest,
    ExternalRiskFormLinkRequest,
    ExternalRiskSummarizeRequest,
    HkoWeatherFetchRequest,
    draft_daily_risk_briefing,
    fetch_hk_industrial_news,
    fetch_hk_safety_updates,
    fetch_hko_weather,
    link_external_risk_to_forms,
    persist_external_risk_items,
    summarize_external_risks,
)
from .tools.confirmations import (
    PendingConfirmationCreateRequest,
    PendingConfirmationQueryRequest,
    PendingConfirmationResolveRequest,
    WorkflowArtifactRecordRequest,
    WorkflowEventLinkRequest,
    WorkflowRunCreateRequest,
    WorkflowSchemaInitRequest,
    WorkflowStepAppendRequest,
    WorkflowStepUpdateRequest,
    append_workflow_step,
    create_pending_confirmation,
    create_workflow_run,
    init_workflow_confirmation_schema,
    link_workflow_event,
    query_pending_confirmations,
    record_workflow_artifact,
    resolve_pending_confirmation,
    update_workflow_step,
)
from .tools.feishu_events import (
    FeishuCardActionParseRequest,
    FeishuCenterRoutePayloadRequest,
    FeishuMessageParseRequest,
    FeishuPlatformMessageRequest,
    feishu_build_center_route_payload,
    feishu_event_to_platform_message,
    feishu_parse_card_action,
    feishu_parse_message_event,
)
from .tools.feishu import (
    FeishuChatListRequest,
    FeishuEventArchiveRequest,
    FeishuEventCallbackRequest,
    FeishuEventToPlatformEventRequest,
    FeishuNotifyRequest,
    FeishuSafetyCardRequest,
    FeishuSendCardRequest,
    FeishuSendMessageRequest,
    FeishuTenantTokenRequest,
    feishu_archive_event,
    feishu_build_safety_review_card,
    feishu_event_to_platform_event,
    feishu_get_tenant_access_token,
    feishu_handle_event_callback,
    feishu_list_chats,
    feishu_send_interactive_card,
    feishu_send_text_message,
    notify_feishu,
)
from .tools.forms import (
    DocxGenerateFromTemplateRequest,
    FormPrefillRequest,
    FormRecordExportRequest,
    FormSuggestionRequest,
    FormTemplateDetailRequest,
    FormTemplateSearchRequest,
    export_form_record,
    generate_docx_from_template,
    get_form_template_detail,
    prefill_form_fields,
    search_form_templates,
    suggest_forms_for_case,
)
from .tools.docmate_docx import (
    ApplyChangesetRequest,
    GenerateChangesetRequest,
    PreviewChangesetRequest,
    ReadDocxRequest,
    tool_docmate_apply_changeset,
    tool_docmate_generate_changeset,
    tool_docmate_preview_changeset,
    tool_docmate_read_docx,
)
from .tools.future_operations import FUTURE_TOOL_MODELS, call_future_tool
from .tools.queries import (
    DashboardMetricsRequest,
    ExternalRiskQueryRequest,
    FormRecordQueryRequest,
    PendingActionQueryRequest,
    SafetyCaseQueryRequest,
    SafetyDataExportRequest,
    export_safety_data,
    get_dashboard_metrics,
    query_external_risks,
    query_form_records,
    query_pending_actions,
    query_safety_cases,
)
from .tools.reference_adapters import (
    ConstructionToolMapRequest,
    HazardZoneRuleRequest,
    ReferenceAdapterListRequest,
    SafetyReportFromEventsRequest,
    VisualPipelineRecommendRequest,
    VisualSafetyEventNormalizeRequest,
    draft_safety_report_from_events,
    evaluate_hazard_zone_rules,
    list_reference_adapters,
    map_mcp_construction_tool,
    normalize_visual_safety_event,
    recommend_visual_safety_pipeline,
)
from .tools.prompt_templates import (
    PromptTemplateListRequest,
    PromptTemplateRenderRequest,
    list_prompt_templates,
    render_prompt_template,
)
from .tools.report import GenerateReportRequest, generate_report
from .tools.rtmp import RtmpSnapshotRequest, run_rtmp_snapshot
from .tools.safety import (
    AIArchiveClassifyRequest,
    ChatHazardIngestRequest,
    ClassificationFeedbackRequest,
    HazardDedupeRequest,
    SafetyActionConnectRequest,
    SafetyDatabaseInitRequest,
    VlmHazardIngestRequest,
    ai_archive_classifier,
    connect_hazard_actions,
    dedupe_and_link_hazards,
    ingest_chat_hazards,
    ingest_vlm_hazards,
    init_safety_database,
    record_classification_feedback,
)
from .tools.vlm import VlmDetectRequest, run_vlm_detect
from .tools.vlm_workflows import (
    CameraPatrolScheduleRequest,
    CameraSnapshotRequest,
    VlmBatchRequest,
    VlmBeforeAfterCompareRequest,
    VlmCaseCreateRequest,
    VlmHazardClassifyRequest,
    capture_camera_snapshot,
    classify_vlm_hazard,
    compare_vlm_before_after,
    create_case_from_vlm,
    run_vlm_detection_batch,
    schedule_camera_patrol,
)
from .tools.secureeye_vlm import (
    SecureEyeBatchAnalyzeRequest,
    SecureEyeCropAnalyzeRequest,
    SecureEyeMergeRequest,
    analyze_batch,
    analyze_crop,
    merge_results,
)
from .tools.whatsapp import (
    WhatsAppAuthStartRequest,
    WhatsAppAuthLogoutRequest,
    WhatsAppAuthStatusRequest,
    WhatsAppAuthStopRequest,
    WhatsAppDownloadMediaRequest,
    WhatsAppGroupsRefreshRequest,
    WhatsAppSendTextRequest,
    WhatsAppSearchRequest,
    WhatsAppWacliGroupsRequest,
    auth_status,
    download_media,
    list_groups_wacli,
    logout_auth,
    refresh_groups_wacli,
    search_messages,
    send_text_confirmed,
    start_auth,
    stop_auth,
)
from .tools.yaoyao_ocr_engine import get_engine
from .tools.yaoyao_pdf_render import get_pdf_render_service
from .tools.yaoyao_structured_input import get_workflow_service
from .tools.yaoyao_template_store import get_template_store


app = FastAPI(
    title="AgentToolbox",
    version="0.1.0",
    description="Expose local programs as HTTP tools for AI agents.",
)


class GenericToolCallRequest(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


@app.on_event("startup")
def _startup() -> None:
    ensure_workspace()


@app.get("/health", response_model=HealthResult)
def health() -> HealthResult:
    checks = health_checks()
    return HealthResult(
        ok=all(bool(item.get("available")) for name, item in checks.items() if name != "feishu_notify"),
        workspace=str(settings.workspace),
        tools=checks,
    )


@app.get("/tools")
def list_tools() -> dict:
    return {"tools": [spec.model_dump() for spec in tool_specs()]}


@app.post("/integrations/feishu/events")
async def feishu_events_callback(request: Request):
    payload = await request.json()
    result = feishu_handle_event_callback(FeishuEventCallbackRequest(payload=payload))
    response = result.data.get("response")
    if response:
        return response
    return result.model_dump()


@app.post("/tools/call")
def call_tool(req: GenericToolCallRequest) -> dict[str, Any]:
    return _call_tool(req.name, req.arguments)


@app.post("/tools/future/{tool_name}")
def call_future_operation(tool_name: str, arguments: dict[str, Any] | None = None):
    if tool_name not in FUTURE_TOOL_MODELS:
        return {"ok": False, "tool": tool_name, "summary": "Unknown future operation tool.", "error": f"Unknown tool: {tool_name}"}
    return call_future_tool(tool_name, arguments or {})


@app.post("/tools/rtmp_snapshot")
def rtmp_snapshot(req: RtmpSnapshotRequest):
    return run_rtmp_snapshot(req)


@app.post("/tools/vlm_detect")
def vlm_detect(req: VlmDetectRequest):
    return run_vlm_detect(req)


@app.post("/tools/whatsapp_search")
def whatsapp_search(req: WhatsAppSearchRequest):
    return search_messages(req)


@app.post("/tools/whatsapp_download_media")
def whatsapp_download_media(req: WhatsAppDownloadMediaRequest):
    return download_media(req)


@app.post("/tools/whatsapp_auth_start")
def whatsapp_auth_start(req: WhatsAppAuthStartRequest):
    return start_auth(req)


@app.post("/tools/whatsapp_auth_status")
def whatsapp_auth_status(req: WhatsAppAuthStatusRequest):
    return auth_status(req)


@app.post("/tools/whatsapp_auth_stop")
def whatsapp_auth_stop(req: WhatsAppAuthStopRequest):
    return stop_auth(req)


@app.post("/tools/whatsapp_auth_logout")
def whatsapp_auth_logout(req: WhatsAppAuthLogoutRequest):
    return logout_auth(req)


@app.post("/tools/whatsapp_groups_wacli")
def whatsapp_groups_wacli(req: WhatsAppWacliGroupsRequest):
    return list_groups_wacli(req)


@app.post("/tools/whatsapp_groups_refresh")
def whatsapp_groups_refresh(req: WhatsAppGroupsRefreshRequest):
    return refresh_groups_wacli(req)


@app.post("/tools/whatsapp_send_text_confirmed")
def whatsapp_send_text_confirmed(req: WhatsAppSendTextRequest):
    return send_text_confirmed(req)


@app.post("/tools/generate_report")
def report(req: GenerateReportRequest):
    return generate_report(req)


@app.post("/tools/notify_feishu")
def feishu_notify(req: FeishuNotifyRequest):
    return notify_feishu(req)


@app.post("/tools/feishu_get_tenant_access_token")
def feishu_tenant_access_token(req: FeishuTenantTokenRequest):
    return feishu_get_tenant_access_token(req)


@app.post("/tools/feishu_send_text_message")
def feishu_text_message_send(req: FeishuSendMessageRequest):
    return feishu_send_text_message(req)


@app.post("/tools/feishu_send_interactive_card")
def feishu_interactive_card_send(req: FeishuSendCardRequest):
    return feishu_send_interactive_card(req)


@app.post("/tools/feishu_build_safety_review_card")
def feishu_safety_review_card_build(req: FeishuSafetyCardRequest):
    return feishu_build_safety_review_card(req)


@app.post("/tools/feishu_handle_event_callback")
def feishu_event_callback_handle(req: FeishuEventCallbackRequest):
    return feishu_handle_event_callback(req)


@app.post("/tools/feishu_list_chats")
def feishu_chats_list(req: FeishuChatListRequest):
    return feishu_list_chats(req)


@app.post("/tools/feishu_archive_event")
def feishu_event_archive(req: FeishuEventArchiveRequest):
    return feishu_archive_event(req)


@app.post("/tools/feishu_event_to_platform_event")
def feishu_to_platform_event(req: FeishuEventToPlatformEventRequest):
    return feishu_event_to_platform_event(req)


@app.post("/tools/fetch_hko_weather")
def hko_weather(req: HkoWeatherFetchRequest):
    return fetch_hko_weather(req)


@app.post("/tools/fetch_hk_safety_updates")
def hk_safety_updates(req: ExternalRiskFetchRequest):
    return fetch_hk_safety_updates(req)


@app.post("/tools/fetch_hk_industrial_news")
def hk_industrial_news(req: ExternalRiskFetchRequest):
    return fetch_hk_industrial_news(req)


@app.post("/tools/persist_external_risk_items")
def external_risk_persist(req: ExternalRiskPersistRequest):
    return persist_external_risk_items(req)


@app.post("/tools/summarize_external_risks")
def external_risk_summary(req: ExternalRiskSummarizeRequest):
    return summarize_external_risks(req)


@app.post("/tools/draft_daily_risk_briefing")
def daily_risk_briefing(req: DailyRiskBriefingRequest):
    return draft_daily_risk_briefing(req)


@app.post("/tools/link_external_risk_to_forms")
def external_risk_form_link(req: ExternalRiskFormLinkRequest):
    return link_external_risk_to_forms(req)


@app.post("/tools/search_form_templates")
def form_templates_search(req: FormTemplateSearchRequest):
    return search_form_templates(req)


@app.post("/tools/get_form_template_detail")
def form_template_detail(req: FormTemplateDetailRequest):
    return get_form_template_detail(req)


@app.post("/tools/suggest_forms_for_case")
def forms_for_case(req: FormSuggestionRequest):
    return suggest_forms_for_case(req)


@app.post("/tools/prefill_form_fields")
def form_fields_prefill(req: FormPrefillRequest):
    return prefill_form_fields(req)


@app.post("/tools/generate_docx_from_template")
def docx_from_template(req: DocxGenerateFromTemplateRequest):
    return generate_docx_from_template(req)


@app.post("/tools/export_form_record")
def form_record_export(req: FormRecordExportRequest):
    return export_form_record(req)


@app.post("/tools/create_safety_case")
def safety_case_create(req: SafetyCaseCreateRequest):
    return create_safety_case(req)


@app.post("/tools/update_safety_case_status")
def safety_case_status_update(req: SafetyCaseStatusRequest):
    return update_safety_case_status(req)


@app.post("/tools/assign_safety_case")
def safety_case_assign(req: SafetyCaseAssignRequest):
    return assign_safety_case(req)


@app.post("/tools/add_case_evidence")
def case_evidence_add(req: CaseEvidenceRequest):
    return add_case_evidence(req)


@app.post("/tools/generate_rectification_notice")
def rectification_notice_generate(req: CaseDraftRequest):
    return generate_rectification_notice(req)


@app.post("/tools/generate_warning_letter")
def warning_letter_generate(req: CaseDraftRequest):
    return generate_warning_letter(req)


@app.post("/tools/close_case_with_review")
def case_close_review(req: CaseCloseReviewRequest):
    return close_case_with_review(req)


@app.post("/tools/query_safety_cases")
def safety_cases_query(req: SafetyCaseQueryRequest):
    return query_safety_cases(req)


@app.post("/tools/query_external_risks")
def external_risks_query(req: ExternalRiskQueryRequest):
    return query_external_risks(req)


@app.post("/tools/query_form_records")
def form_records_query(req: FormRecordQueryRequest):
    return query_form_records(req)


@app.post("/tools/query_pending_actions")
def pending_actions_query(req: PendingActionQueryRequest):
    return query_pending_actions(req)


@app.post("/tools/get_dashboard_metrics")
def dashboard_metrics(req: DashboardMetricsRequest):
    return get_dashboard_metrics(req)


@app.post("/tools/export_safety_data")
def safety_data_export(req: SafetyDataExportRequest):
    return export_safety_data(req)


@app.post("/tools/list_whatsapp_groups")
def whatsapp_groups_list(req: WhatsAppGroupListRequest):
    return list_whatsapp_groups(req)


@app.post("/tools/draft_group_message")
def group_message_draft(req: GroupMessageDraftRequest):
    return draft_group_message(req)


@app.post("/tools/send_group_message_with_confirm")
def group_message_send_confirm(req: ConfirmedSendRequest):
    return send_group_message_with_confirm(req)


@app.post("/tools/archive_sent_notification")
def sent_notification_archive(req: NotificationArchiveRequest):
    return archive_sent_notification(req)


@app.post("/tools/extract_hazards_from_recent_chats")
def recent_chats_hazard_extract(req: RecentChatHazardRequest):
    return extract_hazards_from_recent_chats(req)


@app.post("/tools/summarize_chat_group_daily")
def chat_group_daily_summary(req: ChatGroupDailySummaryRequest):
    return summarize_chat_group_daily(req)


@app.post("/tools/capture_camera_snapshot")
def camera_snapshot_capture(req: CameraSnapshotRequest):
    return capture_camera_snapshot(req)


@app.post("/tools/run_vlm_detection_batch")
def vlm_detection_batch(req: VlmBatchRequest):
    return run_vlm_detection_batch(req)


@app.post("/tools/secureeye_analyze_crop")
async def secureeye_crop_analyze(req: SecureEyeCropAnalyzeRequest):
    return await analyze_crop(req)


@app.post("/tools/secureeye_analyze_batch")
async def secureeye_batch_analyze(req: SecureEyeBatchAnalyzeRequest):
    return await analyze_batch(req)


@app.post("/tools/secureeye_merge_results")
def secureeye_results_merge(req: SecureEyeMergeRequest):
    return merge_results(req)


@app.post("/tools/classify_vlm_hazard")
def vlm_hazard_classify(req: VlmHazardClassifyRequest):
    return classify_vlm_hazard(req)


@app.post("/tools/create_case_from_vlm")
def case_from_vlm_create(req: VlmCaseCreateRequest):
    return create_case_from_vlm(req)


@app.post("/tools/compare_vlm_before_after")
def vlm_before_after_compare(req: VlmBeforeAfterCompareRequest):
    return compare_vlm_before_after(req)


@app.post("/tools/schedule_camera_patrol")
def camera_patrol_schedule(req: CameraPatrolScheduleRequest):
    return schedule_camera_patrol(req)


@app.post("/tools/ocr_document_or_image")
def document_or_image_ocr(req: OcrDocumentRequest):
    return ocr_document_or_image(req)


@app.post("/tools/extract_tables_from_document")
def document_tables_extract(req: TableExtractionRequest):
    return extract_tables_from_document(req)


@app.post("/tools/classify_document_type")
def document_type_classify(req: DocumentTypeClassifyRequest):
    return classify_document_type(req)


@app.post("/tools/extract_certificate_fields")
def certificate_fields_extract(req: CertificateFieldExtractRequest):
    return extract_certificate_fields(req)


@app.post("/tools/check_certificate_expiry")
def certificate_expiry_check(req: CertificateExpiryCheckRequest):
    return check_certificate_expiry(req)


@app.post("/tools/summarize_policy_document")
def policy_document_summarize(req: PolicyDocumentSummarizeRequest):
    return summarize_policy_document(req)


@app.post("/tools/search_policy_clauses")
def policy_clauses_search(req: PolicyClauseSearchRequest):
    return search_policy_clauses(req)


@app.post("/tools/record_tool_audit")
def tool_audit_record(req: ToolAuditRecordRequest):
    return record_tool_audit(req)


@app.post("/tools/record_llm_audit")
def llm_audit_record(req: LlmAuditRecordRequest):
    return record_llm_audit(req)


@app.post("/tools/list_audit_logs")
def audit_logs_list(req: AuditLogQueryRequest):
    return list_audit_logs(req)


@app.post("/tools/manage_user_roles")
def user_roles_manage(req: UserRoleManageRequest):
    return manage_user_roles(req)


@app.post("/tools/check_action_permission")
def action_permission_check(req: ActionPermissionCheckRequest):
    return check_action_permission(req)


@app.post("/tools/list_prompt_templates")
def prompt_templates_list(req: PromptTemplateListRequest):
    return list_prompt_templates(req)


@app.post("/tools/render_prompt_template")
def prompt_template_render(req: PromptTemplateRenderRequest):
    return render_prompt_template(req)


@app.post("/tools/list_reference_adapters")
def reference_adapters_list(req: ReferenceAdapterListRequest):
    return list_reference_adapters(req)


@app.post("/tools/map_mcp_construction_tool")
def mcp_construction_tool_map(req: ConstructionToolMapRequest):
    return map_mcp_construction_tool(req)


@app.post("/tools/normalize_visual_safety_event")
def visual_safety_event_normalize(req: VisualSafetyEventNormalizeRequest):
    return normalize_visual_safety_event(req)


@app.post("/tools/evaluate_hazard_zone_rules")
def hazard_zone_rules_evaluate(req: HazardZoneRuleRequest):
    return evaluate_hazard_zone_rules(req)


@app.post("/tools/recommend_visual_safety_pipeline")
def visual_safety_pipeline_recommend(req: VisualPipelineRecommendRequest):
    return recommend_visual_safety_pipeline(req)


@app.post("/tools/draft_safety_report_from_events")
def safety_report_from_events_draft(req: SafetyReportFromEventsRequest):
    return draft_safety_report_from_events(req)


@app.post("/tools/init_safety_database")
def safety_database_init(req: SafetyDatabaseInitRequest):
    return init_safety_database(req)


@app.post("/tools/ai_archive_classifier")
def archive_classifier(req: AIArchiveClassifyRequest):
    return ai_archive_classifier(req)


@app.post("/tools/ingest_chat_hazards")
def chat_hazards(req: ChatHazardIngestRequest):
    return ingest_chat_hazards(req)


@app.post("/tools/ingest_vlm_hazards")
def vlm_hazards(req: VlmHazardIngestRequest):
    return ingest_vlm_hazards(req)


@app.post("/tools/dedupe_and_link_hazards")
def hazard_dedupe(req: HazardDedupeRequest):
    return dedupe_and_link_hazards(req)


@app.post("/tools/connect_hazard_actions")
def hazard_actions(req: SafetyActionConnectRequest):
    return connect_hazard_actions(req)


@app.post("/tools/record_classification_feedback")
def classification_feedback(req: ClassificationFeedbackRequest):
    return record_classification_feedback(req)


# ── Workflow / confirmation tools ───────────────────────────────

@app.post("/tools/init_workflow_confirmation_schema")
def workflow_schema_init(req: WorkflowSchemaInitRequest):
    return init_workflow_confirmation_schema(req)


@app.post("/tools/create_workflow_run")
def workflow_run_create(req: WorkflowRunCreateRequest):
    return create_workflow_run(req)


@app.post("/tools/append_workflow_step")
def workflow_step_append(req: WorkflowStepAppendRequest):
    return append_workflow_step(req)


@app.post("/tools/update_workflow_step")
def workflow_step_update(req: WorkflowStepUpdateRequest):
    return update_workflow_step(req)


@app.post("/tools/create_pending_confirmation")
def pending_confirmation_create(req: PendingConfirmationCreateRequest):
    return create_pending_confirmation(req)


@app.post("/tools/query_pending_confirmations")
def pending_confirmation_query(req: PendingConfirmationQueryRequest):
    return query_pending_confirmations(req)


@app.post("/tools/resolve_pending_confirmation")
def pending_confirmation_resolve(req: PendingConfirmationResolveRequest):
    return resolve_pending_confirmation(req)


@app.post("/tools/record_workflow_artifact")
def workflow_artifact_record(req: WorkflowArtifactRecordRequest):
    return record_workflow_artifact(req)


@app.post("/tools/link_workflow_event")
def workflow_event_link(req: WorkflowEventLinkRequest):
    return link_workflow_event(req)


@app.post("/tools/feishu_parse_message_event")
def feishu_message_parse(req: FeishuMessageParseRequest):
    return feishu_parse_message_event(req)


@app.post("/tools/feishu_parse_card_action")
def feishu_card_action_parse(req: FeishuCardActionParseRequest):
    return feishu_parse_card_action(req)


@app.post("/tools/feishu_event_to_platform_message")
def feishu_platform_message(req: FeishuPlatformMessageRequest):
    return feishu_event_to_platform_message(req)


@app.post("/tools/feishu_build_center_route_payload")
def feishu_center_route_payload(req: FeishuCenterRoutePayloadRequest):
    return feishu_build_center_route_payload(req)


# ── DocMate .docx 工具端点 ────────────────────────────────────

@app.post("/tools/docmate_read_docx")
async def docmate_read_docx_endpoint(req: ReadDocxRequest):
    return await tool_docmate_read_docx(req)


@app.post("/tools/docmate_generate_changeset")
async def docmate_generate_changeset_endpoint(req: GenerateChangesetRequest):
    return await tool_docmate_generate_changeset(req)


@app.post("/tools/docmate_preview_changeset")
async def docmate_preview_changeset_endpoint(req: PreviewChangesetRequest):
    return await tool_docmate_preview_changeset(req)


@app.post("/tools/docmate_apply_changeset")
async def docmate_apply_changeset_endpoint(req: ApplyChangesetRequest):
    return await tool_docmate_apply_changeset(req)


# ── Yaoyao (structured input / OCR) tool endpoints ──────────────


class YaoyaoRenderPdfPagesRequest(BaseModel):
    file_path: str
    page_index: int = 0
    render_width: int = 2000
    render_height: int = 2800


class YaoyaoDetectRegionsRequest(BaseModel):
    file_path: str
    page_index: int = 0
    render_width: int = 2000
    render_height: int = 2800


class YaoyaoRecognizeRegionsRequest(BaseModel):
    file_path: str
    regions: list[dict[str, Any]] = Field(default_factory=list)
    page_index: int | None = None
    template_id: str | None = None
    render_width: int = 2000
    render_height: int = 2800
    case_id: int | None = None


class YaoyaoSaveTemplateRequest(BaseModel):
    regions: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    name: str | None = None
    template_id: str | None = None


class YaoyaoLoadTemplateRequest(BaseModel):
    template_id: str


class YaoyaoStructuredExtractRequest(BaseModel):
    file_path: str
    regions: list[dict[str, Any]] | None = None
    page_index: int | None = None
    template_id: str | None = None
    case_id: int | None = None
    render_width: int = 2000
    render_height: int = 2800


@app.post("/tools/yaoyao_render_pdf_pages")
def yaoyao_render_pdf_pages(req: YaoyaoRenderPdfPagesRequest):
    """Render a single PDF page to a preview image."""
    try:
        service = get_pdf_render_service()
        import tempfile
        from pathlib import Path

        out_dir = Path(tempfile.mkdtemp(prefix="yaoyao_preview_"))
        out_path = service.render_page_to_file(
            req.file_path, req.page_index, out_dir / "preview.jpg",
            req.render_width, req.render_height,
        )
        return {"ok": True, "preview_image_path": out_path, "page_index": req.page_index}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_detect_regions")
def yaoyao_detect_regions(req: YaoyaoDetectRegionsRequest):
    """Auto-detect text regions on a PDF page using full-page OCR.

    Returns raw OCR boxes that can be used as region candidates.
    """
    try:
        import tempfile
        from pathlib import Path
        from PIL import Image

        service = get_pdf_render_service()
        page_data = service.render_page(
            req.file_path, req.page_index, req.render_width, req.render_height,
        )
        tmp = Path(tempfile.mktemp(suffix=".png"))
        page_data.image.save(tmp, "PNG")

        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()
            result, _ = engine(str(tmp))

            regions = []
            if result:
                for item in result:
                    box = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = item[1] if len(item) >= 2 else ""
                    score = float(item[2]) if len(item) >= 3 else 0.0

                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    regions.append({
                        "name": text[:20] if text else f"region_{len(regions)}",
                        "x": min(xs),
                        "y": min(ys),
                        "width": max(xs) - min(xs),
                        "height": max(ys) - min(ys),
                        "angle": 0,
                        "text": text,
                        "score": score,
                    })

            return {
                "ok": True,
                "regions": regions,
                "page_count": page_data.page_count,
                "page_index": req.page_index,
            }
        finally:
            if tmp.exists():
                tmp.unlink()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_recognize_regions")
def yaoyao_recognize_regions(req: YaoyaoRecognizeRegionsRequest):
    """Recognize text in specified regions of a document."""
    try:
        workflow = get_workflow_service()
        result = workflow.structured_extract(
            file_path=req.file_path,
            regions=req.regions,
            page_index=req.page_index,
            template_id=req.template_id,
            case_id=req.case_id,
            render_width=req.render_width,
            render_height=req.render_height,
        )
        return {
            "ok": True,
            "draft_id": result.draft_id,
            "pages": [
                {"page_number": p.page_number, "values": p.values}
                for p in result.pages
            ],
            "field_candidates": [
                {
                    "field_name": fc.field_name,
                    "value": fc.value,
                    "confidence": fc.confidence,
                    "source_region": fc.source_region,
                    "page_number": fc.page_number,
                }
                for fc in result.field_candidates
            ],
            "page_count": result.page_count,
            "elapsed_seconds": result.elapsed_seconds,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_save_template")
def yaoyao_save_template(req: YaoyaoSaveTemplateRequest):
    """Save an OCR recognition template."""
    try:
        store = get_template_store()
        result = store.save(
            regions=req.regions,
            rows=req.rows,
            name=req.name,
            template_id=req.template_id,
        )
        return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_load_template")
def yaoyao_load_template(req: YaoyaoLoadTemplateRequest):
    """Load an OCR recognition template by ID."""
    try:
        store = get_template_store()
        template = store.load(req.template_id)
        return {"ok": True, "template": template}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_list_templates")
def yaoyao_list_templates():
    """List all saved OCR recognition templates."""
    try:
        store = get_template_store()
        return {"ok": True, "items": store.list_templates()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/tools/yaoyao_structured_extract")
def yaoyao_structured_extract(req: YaoyaoStructuredExtractRequest):
    """Full structured extraction: render + OCR + field mapping."""
    try:
        workflow = get_workflow_service()

        # If a template is specified, load its regions.
        regions = req.regions
        if req.template_id and not regions:
            store = get_template_store()
            template = store.load(req.template_id)
            regions = template.get("regions", [])

        result = workflow.structured_extract(
            file_path=req.file_path,
            regions=regions,
            page_index=req.page_index,
            template_id=req.template_id,
            case_id=req.case_id,
            render_width=req.render_width,
            render_height=req.render_height,
        )
        return {
            "ok": True,
            "draft_id": result.draft_id,
            "preview_image_path": result.preview_image_path,
            "pages": [
                {"page_number": p.page_number, "values": p.values}
                for p in result.pages
            ],
            "field_candidates": [
                {
                    "field_name": fc.field_name,
                    "value": fc.value,
                    "confidence": fc.confidence,
                    "source_region": fc.source_region,
                    "page_number": fc.page_number,
                }
                for fc in result.field_candidates
            ],
            "page_count": result.page_count,
            "elapsed_seconds": result.elapsed_seconds,
            "requires_acceptance": True,
            "confirm_payload": {
                "draft_id": result.draft_id,
                "template_id": req.template_id,
                "case_id": req.case_id,
            },
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

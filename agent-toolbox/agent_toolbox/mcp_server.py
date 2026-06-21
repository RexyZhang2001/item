from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from .registry import tool_specs
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
    ExternalRiskFormLinkRequest,
    ExternalRiskPersistRequest,
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
from .tools.future_operations import FUTURE_TOOL_MODELS, call_future_tool
from .workflow_tools import WORKFLOW_TOOL_MODELS, call_workflow_tool
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


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "rtmp_snapshot":
        return run_rtmp_snapshot(RtmpSnapshotRequest(**arguments)).model_dump()
    if name == "vlm_detect":
        return run_vlm_detect(VlmDetectRequest(**arguments)).model_dump()
    if name == "whatsapp_search":
        return search_messages(WhatsAppSearchRequest(**arguments)).model_dump()
    if name == "whatsapp_download_media":
        return download_media(WhatsAppDownloadMediaRequest(**arguments)).model_dump()
    if name == "whatsapp_auth_start":
        return start_auth(WhatsAppAuthStartRequest(**arguments)).model_dump()
    if name == "whatsapp_auth_status":
        return auth_status(WhatsAppAuthStatusRequest(**arguments)).model_dump()
    if name == "whatsapp_auth_stop":
        return stop_auth(WhatsAppAuthStopRequest(**arguments)).model_dump()
    if name == "whatsapp_auth_logout":
        return logout_auth(WhatsAppAuthLogoutRequest(**arguments)).model_dump()
    if name == "whatsapp_groups_wacli":
        return list_groups_wacli(WhatsAppWacliGroupsRequest(**arguments)).model_dump()
    if name == "whatsapp_groups_refresh":
        return refresh_groups_wacli(WhatsAppGroupsRefreshRequest(**arguments)).model_dump()
    if name == "whatsapp_send_text_confirmed":
        return send_text_confirmed(WhatsAppSendTextRequest(**arguments)).model_dump()
    if name == "generate_report":
        return generate_report(GenerateReportRequest(**arguments)).model_dump()
    if name == "notify_feishu":
        return notify_feishu(FeishuNotifyRequest(**arguments)).model_dump()
    if name == "feishu_get_tenant_access_token":
        return feishu_get_tenant_access_token(FeishuTenantTokenRequest(**arguments)).model_dump()
    if name == "feishu_send_text_message":
        return feishu_send_text_message(FeishuSendMessageRequest(**arguments)).model_dump()
    if name == "feishu_send_interactive_card":
        return feishu_send_interactive_card(FeishuSendCardRequest(**arguments)).model_dump()
    if name == "feishu_build_safety_review_card":
        return feishu_build_safety_review_card(FeishuSafetyCardRequest(**arguments)).model_dump()
    if name == "feishu_handle_event_callback":
        return feishu_handle_event_callback(FeishuEventCallbackRequest(**arguments)).model_dump()
    if name == "feishu_list_chats":
        return feishu_list_chats(FeishuChatListRequest(**arguments)).model_dump()
    if name == "feishu_archive_event":
        return feishu_archive_event(FeishuEventArchiveRequest(**arguments)).model_dump()
    if name == "feishu_event_to_platform_event":
        return feishu_event_to_platform_event(FeishuEventToPlatformEventRequest(**arguments)).model_dump()
    if name == "fetch_hko_weather":
        return fetch_hko_weather(HkoWeatherFetchRequest(**arguments)).model_dump()
    if name == "fetch_hk_safety_updates":
        return fetch_hk_safety_updates(ExternalRiskFetchRequest(**arguments)).model_dump()
    if name == "fetch_hk_industrial_news":
        return fetch_hk_industrial_news(ExternalRiskFetchRequest(**arguments)).model_dump()
    if name == "persist_external_risk_items":
        return persist_external_risk_items(ExternalRiskPersistRequest(**arguments)).model_dump()
    if name == "summarize_external_risks":
        return summarize_external_risks(ExternalRiskSummarizeRequest(**arguments)).model_dump()
    if name == "draft_daily_risk_briefing":
        return draft_daily_risk_briefing(DailyRiskBriefingRequest(**arguments)).model_dump()
    if name == "link_external_risk_to_forms":
        return link_external_risk_to_forms(ExternalRiskFormLinkRequest(**arguments)).model_dump()
    if name == "search_form_templates":
        return search_form_templates(FormTemplateSearchRequest(**arguments)).model_dump()
    if name == "get_form_template_detail":
        return get_form_template_detail(FormTemplateDetailRequest(**arguments)).model_dump()
    if name == "suggest_forms_for_case":
        return suggest_forms_for_case(FormSuggestionRequest(**arguments)).model_dump()
    if name == "prefill_form_fields":
        return prefill_form_fields(FormPrefillRequest(**arguments)).model_dump()
    if name == "generate_docx_from_template":
        return generate_docx_from_template(DocxGenerateFromTemplateRequest(**arguments)).model_dump()
    if name == "export_form_record":
        return export_form_record(FormRecordExportRequest(**arguments)).model_dump()
    if name == "create_safety_case":
        return create_safety_case(SafetyCaseCreateRequest(**arguments)).model_dump()
    if name == "update_safety_case_status":
        return update_safety_case_status(SafetyCaseStatusRequest(**arguments)).model_dump()
    if name == "assign_safety_case":
        return assign_safety_case(SafetyCaseAssignRequest(**arguments)).model_dump()
    if name == "add_case_evidence":
        return add_case_evidence(CaseEvidenceRequest(**arguments)).model_dump()
    if name == "generate_rectification_notice":
        return generate_rectification_notice(CaseDraftRequest(**arguments)).model_dump()
    if name == "generate_warning_letter":
        return generate_warning_letter(CaseDraftRequest(**arguments)).model_dump()
    if name == "close_case_with_review":
        return close_case_with_review(CaseCloseReviewRequest(**arguments)).model_dump()
    if name == "query_safety_cases":
        return query_safety_cases(SafetyCaseQueryRequest(**arguments)).model_dump()
    if name == "query_external_risks":
        return query_external_risks(ExternalRiskQueryRequest(**arguments)).model_dump()
    if name == "query_form_records":
        return query_form_records(FormRecordQueryRequest(**arguments)).model_dump()
    if name == "query_pending_actions":
        return query_pending_actions(PendingActionQueryRequest(**arguments)).model_dump()
    if name == "get_dashboard_metrics":
        return get_dashboard_metrics(DashboardMetricsRequest(**arguments)).model_dump()
    if name == "export_safety_data":
        return export_safety_data(SafetyDataExportRequest(**arguments)).model_dump()
    if name == "list_whatsapp_groups":
        return list_whatsapp_groups(WhatsAppGroupListRequest(**arguments)).model_dump()
    if name == "draft_group_message":
        return draft_group_message(GroupMessageDraftRequest(**arguments)).model_dump()
    if name == "send_group_message_with_confirm":
        return send_group_message_with_confirm(ConfirmedSendRequest(**arguments)).model_dump()
    if name == "archive_sent_notification":
        return archive_sent_notification(NotificationArchiveRequest(**arguments)).model_dump()
    if name == "extract_hazards_from_recent_chats":
        return extract_hazards_from_recent_chats(RecentChatHazardRequest(**arguments)).model_dump()
    if name == "summarize_chat_group_daily":
        return summarize_chat_group_daily(ChatGroupDailySummaryRequest(**arguments)).model_dump()
    if name == "capture_camera_snapshot":
        return capture_camera_snapshot(CameraSnapshotRequest(**arguments)).model_dump()
    if name == "run_vlm_detection_batch":
        return run_vlm_detection_batch(VlmBatchRequest(**arguments)).model_dump()
    if name == "classify_vlm_hazard":
        return classify_vlm_hazard(VlmHazardClassifyRequest(**arguments)).model_dump()
    if name == "create_case_from_vlm":
        return create_case_from_vlm(VlmCaseCreateRequest(**arguments)).model_dump()
    if name == "compare_vlm_before_after":
        return compare_vlm_before_after(VlmBeforeAfterCompareRequest(**arguments)).model_dump()
    if name == "schedule_camera_patrol":
        return schedule_camera_patrol(CameraPatrolScheduleRequest(**arguments)).model_dump()
    if name == "ocr_document_or_image":
        return ocr_document_or_image(OcrDocumentRequest(**arguments)).model_dump()
    if name == "extract_tables_from_document":
        return extract_tables_from_document(TableExtractionRequest(**arguments)).model_dump()
    if name == "classify_document_type":
        return classify_document_type(DocumentTypeClassifyRequest(**arguments)).model_dump()
    if name == "extract_certificate_fields":
        return extract_certificate_fields(CertificateFieldExtractRequest(**arguments)).model_dump()
    if name == "check_certificate_expiry":
        return check_certificate_expiry(CertificateExpiryCheckRequest(**arguments)).model_dump()
    if name == "summarize_policy_document":
        return summarize_policy_document(PolicyDocumentSummarizeRequest(**arguments)).model_dump()
    if name == "search_policy_clauses":
        return search_policy_clauses(PolicyClauseSearchRequest(**arguments)).model_dump()
    if name == "record_tool_audit":
        return record_tool_audit(ToolAuditRecordRequest(**arguments)).model_dump()
    if name == "record_llm_audit":
        return record_llm_audit(LlmAuditRecordRequest(**arguments)).model_dump()
    if name == "list_audit_logs":
        return list_audit_logs(AuditLogQueryRequest(**arguments)).model_dump()
    if name == "manage_user_roles":
        return manage_user_roles(UserRoleManageRequest(**arguments)).model_dump()
    if name == "check_action_permission":
        return check_action_permission(ActionPermissionCheckRequest(**arguments)).model_dump()
    if name == "list_prompt_templates":
        return list_prompt_templates(PromptTemplateListRequest(**arguments)).model_dump()
    if name == "render_prompt_template":
        return render_prompt_template(PromptTemplateRenderRequest(**arguments)).model_dump()
    if name == "list_reference_adapters":
        return list_reference_adapters(ReferenceAdapterListRequest(**arguments)).model_dump()
    if name == "map_mcp_construction_tool":
        return map_mcp_construction_tool(ConstructionToolMapRequest(**arguments)).model_dump()
    if name == "normalize_visual_safety_event":
        return normalize_visual_safety_event(VisualSafetyEventNormalizeRequest(**arguments)).model_dump()
    if name == "evaluate_hazard_zone_rules":
        return evaluate_hazard_zone_rules(HazardZoneRuleRequest(**arguments)).model_dump()
    if name == "recommend_visual_safety_pipeline":
        return recommend_visual_safety_pipeline(VisualPipelineRecommendRequest(**arguments)).model_dump()
    if name == "draft_safety_report_from_events":
        return draft_safety_report_from_events(SafetyReportFromEventsRequest(**arguments)).model_dump()
    if name == "init_safety_database":
        return init_safety_database(SafetyDatabaseInitRequest(**arguments)).model_dump()
    if name == "ai_archive_classifier":
        return ai_archive_classifier(AIArchiveClassifyRequest(**arguments)).model_dump()
    if name == "ingest_chat_hazards":
        return ingest_chat_hazards(ChatHazardIngestRequest(**arguments)).model_dump()
    if name == "ingest_vlm_hazards":
        return ingest_vlm_hazards(VlmHazardIngestRequest(**arguments)).model_dump()
    if name == "dedupe_and_link_hazards":
        return dedupe_and_link_hazards(HazardDedupeRequest(**arguments)).model_dump()
    if name == "connect_hazard_actions":
        return connect_hazard_actions(SafetyActionConnectRequest(**arguments)).model_dump()
    if name == "record_classification_feedback":
        return record_classification_feedback(ClassificationFeedbackRequest(**arguments)).model_dump()
    if name == "init_workflow_confirmation_schema":
        return init_workflow_confirmation_schema(WorkflowSchemaInitRequest(**arguments)).model_dump()
    if name == "create_workflow_run":
        return create_workflow_run(WorkflowRunCreateRequest(**arguments)).model_dump()
    if name == "append_workflow_step":
        return append_workflow_step(WorkflowStepAppendRequest(**arguments)).model_dump()
    if name == "update_workflow_step":
        return update_workflow_step(WorkflowStepUpdateRequest(**arguments)).model_dump()
    if name == "create_pending_confirmation":
        return create_pending_confirmation(PendingConfirmationCreateRequest(**arguments)).model_dump()
    if name == "query_pending_confirmations":
        return query_pending_confirmations(PendingConfirmationQueryRequest(**arguments)).model_dump()
    if name == "resolve_pending_confirmation":
        return resolve_pending_confirmation(PendingConfirmationResolveRequest(**arguments)).model_dump()
    if name == "record_workflow_artifact":
        return record_workflow_artifact(WorkflowArtifactRecordRequest(**arguments)).model_dump()
    if name == "link_workflow_event":
        return link_workflow_event(WorkflowEventLinkRequest(**arguments)).model_dump()
    if name == "feishu_parse_message_event":
        return feishu_parse_message_event(FeishuMessageParseRequest(**arguments)).model_dump()
    if name == "feishu_parse_card_action":
        return feishu_parse_card_action(FeishuCardActionParseRequest(**arguments)).model_dump()
    if name == "feishu_event_to_platform_message":
        return feishu_event_to_platform_message(FeishuPlatformMessageRequest(**arguments)).model_dump()
    if name == "feishu_build_center_route_payload":
        return feishu_build_center_route_payload(FeishuCenterRoutePayloadRequest(**arguments)).model_dump()
    if name in WORKFLOW_TOOL_MODELS:
        return call_workflow_tool(name, arguments).model_dump()
    if name in FUTURE_TOOL_MODELS:
        return call_future_tool(name, arguments).model_dump()
    raise ValueError(f"Unknown tool: {name}")


async def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "AgentToolbox", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _result(
            request_id,
            {
                "tools": [
                    {
                        "name": spec.name,
                        "description": spec.description,
                        "inputSchema": spec.input_schema,
                    }
                    for spec in tool_specs()
                ]
            },
        )

    if method == "tools/call":
        try:
            name = params["name"]
            arguments = params.get("arguments") or {}
            payload = _call_tool(name, arguments)
            return _result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(payload, ensure_ascii=False, indent=2),
                        }
                    ],
                    "isError": not payload.get("ok", False),
                },
            )
        except Exception as exc:
            return _error(request_id, -32000, str(exc))

    return _error(request_id, -32601, f"Method not found: {method}")


async def main() -> None:
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            break
        try:
            message = json.loads(line)
            response = await handle_message(message)
        except Exception as exc:
            response = _error(None, -32700, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

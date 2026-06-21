import type {
  AppConfig,
  CenterChatResponse,
  ChatResponse,
  ConnectorSettingsStatus,
  DocmateApplyResult,
  DocmateGenerateResult,
  DocmatePreviewResult,
  DocmateReadResult,
  DocumentRevisionPreview,
  GeneratedReport,
  HybridPlan,
  LlmTestResult,
  LlmSettingsStatus,
  RuntimeStatus,
  SafetyCaseRecord,
  SmartFormDraft,
  SmartFormTemplate,
  SkillDetail,
  SkillInfo,
  VisualPatrolDraft,
  PatrolRunReport,
  PatrolRunSummary,
  PendingConfirmation,
  RagDocument,
  RagQueryMatch,
  RagStats,
  TableMappingExtractResult,
  TableMappingForm,
  TableMappingRunResult,
  WorkbenchSummary,
  WorkflowDetail,
  WorkflowInfo,
  WorkflowTemplateInfo,
  YaoyaoConfirmResult,
  YaoyaoRegion,
  YaoyaoStructuredDraft,
  YaoyaoTemplateListItem,
  YaoyaoTemplate,
} from '../types/domain'

const CENTER_BASE_URL =
  import.meta.env.VITE_CHITUNG_CENTER_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8999'

async function ensureOk(response: Response, message: string) {
  if (response.ok) return
  let detail = ''
  try {
    const data = await response.json()
    detail = String(data.message || data.detail || data.error || '')
  } catch {
    detail = await response.text().catch(() => '')
  }
  throw new Error(detail ? `${message}: ${detail}` : `${message}: ${response.status}`)
}

export interface SendMessageRequest {
  message: string
  channel?: 'local_chat' | 'feishu'
  context?: Record<string, unknown>
}

export async function sendChatMessage(request: SendMessageRequest): Promise<ChatResponse> {
  const response = await fetch(`${CENTER_BASE_URL}/api/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      channel: request.channel ?? 'local_chat',
      message: request.message,
      metadata: request.context ?? {},
    }),
  })

  await ensureOk(response, 'Chitung Center request failed')

  const data = (await response.json()) as CenterChatResponse
  return {
    type: data.cards?.length ? 'review_card' : 'reply',
    message: data.reply,
    payload: {
      intent: data.intent,
      cards: data.cards ?? [],
      toolResults: data.tool_results ?? [],
      auditId: data.audit_id,
    },
  }
}

export async function getSkills(): Promise<SkillInfo[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/skills`)
  await ensureOk(response, 'Skills list failed')
  const data = (await response.json()) as { items?: SkillInfo[] }
  return data.items ?? []
}

export async function getSkillDetail(name: string): Promise<SkillDetail> {
  const response = await fetch(`${CENTER_BASE_URL}/api/skills/${encodeURIComponent(name)}`)
  await ensureOk(response, 'Skill detail failed')
  return response.json() as Promise<SkillDetail>
}

export async function toggleSkill(name: string, enabled: boolean): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/skills/${encodeURIComponent(name)}/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
  await ensureOk(response, 'Skill toggle failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function importSkill(name: string, content: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/skills/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  })
  await ensureOk(response, 'Skill import failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function deleteSkill(name: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/skills/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  await ensureOk(response, 'Skill delete failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getWorkflows(): Promise<WorkflowInfo[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows`)
  await ensureOk(response, 'Workflows list failed')
  const data = (await response.json()) as { items?: WorkflowInfo[] }
  return data.items ?? []
}

export async function getWorkflowDetail(name: string): Promise<WorkflowDetail> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/${encodeURIComponent(name)}`)
  await ensureOk(response, 'Workflow detail failed')
  return response.json() as Promise<WorkflowDetail>
}

export async function toggleWorkflow(name: string, enabled: boolean): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/${encodeURIComponent(name)}/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
  await ensureOk(response, 'Workflow toggle failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function importWorkflow(name: string, content: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  })
  await ensureOk(response, 'Workflow import failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function deleteWorkflow(name: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  await ensureOk(response, 'Workflow delete failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getWorkflowTemplates(): Promise<WorkflowTemplateInfo[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/templates`)
  await ensureOk(response, 'Workflow templates failed')
  const data = (await response.json()) as { items?: WorkflowTemplateInfo[] }
  return data.items ?? []
}

export async function runWorkflowTemplate(request: {
  workflowName: string
  message?: string
  channel?: string
  userId?: string
  metadata?: Record<string, unknown>
}): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workflows/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_name: request.workflowName,
      message: request.message ?? '从赤瞳工作流库手动运行',
      channel: request.channel ?? 'local_web',
      user_id: request.userId ?? 'local_user',
      metadata: request.metadata ?? {},
    }),
  })
  await ensureOk(response, 'Workflow run failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function uploadRagDocument(file: File, collection = 'default'): Promise<{
  ok: boolean
  doc_id: string
  chunk_count: number
  file_name: string
}> {
  const form = new FormData()
  form.append('file', file)
  form.append('collection', collection)
  const response = await fetch(`${CENTER_BASE_URL}/api/rag/documents/upload`, {
    method: 'POST',
    body: form,
  })
  await ensureOk(response, 'RAG document upload failed')
  return response.json() as Promise<{ ok: boolean; doc_id: string; chunk_count: number; file_name: string }>
}

export async function listRagDocuments(): Promise<RagDocument[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/rag/documents`)
  await ensureOk(response, 'RAG documents list failed')
  const data = (await response.json()) as { items?: RagDocument[] }
  return data.items ?? []
}

export async function deleteRagDocument(docId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/rag/documents/${encodeURIComponent(docId)}`, {
    method: 'DELETE',
  })
  await ensureOk(response, 'RAG document delete failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function queryRag(request: {
  query: string
  topK?: number
  collection?: string
}): Promise<RagQueryMatch[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: request.query,
      top_k: request.topK ?? 5,
      collection: request.collection || undefined,
    }),
  })
  await ensureOk(response, 'RAG query failed')
  const data = (await response.json()) as { items?: RagQueryMatch[] }
  return data.items ?? []
}

export async function getRagStats(): Promise<RagStats> {
  const response = await fetch(`${CENTER_BASE_URL}/api/rag/stats`)
  await ensureOk(response, 'RAG stats failed')
  return response.json() as Promise<RagStats>
}

export async function getHealth(): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/health`)
  await ensureOk(response, 'Health check failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getWorkbenchSummary(): Promise<WorkbenchSummary> {
  const response = await fetch(`${CENTER_BASE_URL}/api/workbench/summary`)
  await ensureOk(response, 'Workbench summary failed')
  return response.json() as Promise<WorkbenchSummary>
}

export async function getPendingConfirmations(params?: {
  status?: string
  actionType?: string
  sourceChannel?: string
  limit?: number
}): Promise<PendingConfirmation[]> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.actionType) query.set('action_type', params.actionType)
  if (params?.sourceChannel) query.set('source_channel', params.sourceChannel)
  if (params?.limit) query.set('limit', String(params.limit))
  const suffix = query.toString() ? `?${query.toString()}` : ''
  const response = await fetch(`${CENTER_BASE_URL}/api/confirmations${suffix}`)
  await ensureOk(response, 'Pending confirmations failed')
  const data = (await response.json()) as { items?: PendingConfirmation[] }
  return data.items ?? []
}

export async function resolvePendingConfirmation(request: {
  confirmationId: string
  decision: 'approve' | 'reject'
  userId?: string
  notes?: string
}): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/confirmations/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      confirmation_id: request.confirmationId,
      decision: request.decision,
      user_id: request.userId ?? 'local_user',
      notes: request.notes,
    }),
  })
  await ensureOk(response, 'Resolve confirmation failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function sendCardAction(request: {
  actionId: string
  cardData?: Record<string, unknown>
  userId?: string
  channel?: string
}): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/chat/card-action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_id: request.actionId,
      card_data: request.cardData ?? {},
      user_id: request.userId ?? 'local_user',
      channel: request.channel ?? 'local_web',
    }),
  })
  await ensureOk(response, 'Card action failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getRuntimeStatus(): Promise<RuntimeStatus> {
  const response = await fetch(`${CENTER_BASE_URL}/api/runtime/status`)
  await ensureOk(response, 'Runtime status failed')
  return response.json() as Promise<RuntimeStatus>
}

export async function getAppConfig(): Promise<AppConfig> {
  const response = await fetch(`${CENTER_BASE_URL}/api/config/app`)
  await ensureOk(response, 'App config failed')
  return response.json() as Promise<AppConfig>
}

export async function saveAppConfig(config: AppConfig): Promise<{ ok: boolean; config: AppConfig }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/config/app`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  await ensureOk(response, 'App config save failed')
  return response.json() as Promise<{ ok: boolean; config: AppConfig }>
}

export async function getLlmSettings(): Promise<LlmSettingsStatus> {
  const response = await fetch(`${CENTER_BASE_URL}/api/settings/llm`)
  await ensureOk(response, 'LLM settings status failed')
  return response.json() as Promise<LlmSettingsStatus>
}

export async function saveLlmSettings(request: {
  baseUrl: string
  apiKey: string
  model: string
}): Promise<{ ok: boolean; message: string; status: LlmSettingsStatus }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/settings/llm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      base_url: request.baseUrl,
      api_key: request.apiKey,
      model: request.model,
    }),
  })
  await ensureOk(response, 'LLM settings save failed')
  return response.json() as Promise<{ ok: boolean; message: string; status: LlmSettingsStatus }>
}

export async function testLlmSettings(): Promise<LlmTestResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/settings/llm/test`, {
    method: 'POST',
  })
  await ensureOk(response, 'LLM settings test failed')
  return response.json() as Promise<LlmTestResult>
}

export async function getConnectorSettings(): Promise<ConnectorSettingsStatus> {
  const response = await fetch(`${CENTER_BASE_URL}/api/settings/connectors`)
  await ensureOk(response, 'Connector settings status failed')
  return response.json() as Promise<ConnectorSettingsStatus>
}

export async function saveConnectorSettings(request: {
  whatsappArchiveBaseUrl: string
  feishuWebhookUrl: string
  feishuWebhookSecret: string
  feishuAppId: string
  feishuAppSecret: string
  feishuVerificationToken: string
  feishuEncryptKey: string
  feishuApiBaseUrl: string
}): Promise<{ ok: boolean; message: string; status: ConnectorSettingsStatus }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/settings/connectors`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      whatsapp_archive_base_url: request.whatsappArchiveBaseUrl,
      feishu_webhook_url: request.feishuWebhookUrl,
      feishu_webhook_secret: request.feishuWebhookSecret,
      feishu_app_id: request.feishuAppId,
      feishu_app_secret: request.feishuAppSecret,
      feishu_verification_token: request.feishuVerificationToken,
      feishu_encrypt_key: request.feishuEncryptKey,
      feishu_api_base_url: request.feishuApiBaseUrl,
    }),
  })
  await ensureOk(response, 'Connector settings save failed')
  return response.json() as Promise<{ ok: boolean; message: string; status: ConnectorSettingsStatus }>
}

export async function updateHazardStatus(caseId: string, status = 'confirmed'): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/hazards/${encodeURIComponent(caseId)}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status,
      notes: 'Confirmed from Chitung desktop workbench.',
    }),
  })
  await ensureOk(response, 'Hazard status update failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getHazards(status?: string): Promise<SafetyCaseRecord[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  params.set('limit', '100')
  const response = await fetch(`${CENTER_BASE_URL}/api/hazards?${params.toString()}`)
  await ensureOk(response, 'Hazard list failed')
  const data = (await response.json()) as { items?: SafetyCaseRecord[] }
  return data.items ?? []
}

export async function draftDocumentRevision(request: {
  title: string
  source: string
  instruction: string
  originalText: string
  revisedText?: string
}): Promise<DocumentRevisionPreview> {
  const response = await fetch(`${CENTER_BASE_URL}/api/documents/revision-preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: request.title,
      source: request.source,
      instruction: request.instruction,
      original_text: request.originalText,
      revised_text: request.revisedText,
    }),
  })
  await ensureOk(response, 'Document revision preview failed')
  return response.json() as Promise<DocumentRevisionPreview>
}

export async function draftSmartForm(request: {
  query: string
  sourceText: string
  templateId?: string
  caseId?: number
  knownFields?: Record<string, unknown>
  instruction?: string
}): Promise<SmartFormDraft> {
  const response = await fetch(`${CENTER_BASE_URL}/api/forms/smart-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: request.query,
      source_text: request.sourceText,
      template_id: request.templateId,
      case_id: request.caseId,
      known_fields: request.knownFields ?? {},
      instruction: request.instruction ?? '???????????????????',
    }),
  })
  await ensureOk(response, 'Smart form draft failed')
  return response.json() as Promise<SmartFormDraft>
}

export async function searchFormTemplates(query = ''): Promise<SmartFormTemplate[]> {
  const params = new URLSearchParams()
  if (query.trim()) params.set('query', query.trim())
  params.set('limit', '20')
  const response = await fetch(`${CENTER_BASE_URL}/api/forms/templates?${params.toString()}`)
  await ensureOk(response, 'Form template search failed')
  const data = (await response.json()) as { items?: SmartFormTemplate[] }
  return data.items ?? []
}

export async function acceptSmartFormDraft(draft: SmartFormDraft): Promise<Record<string, unknown>> {
  if (!draft.accept_payload) {
    throw new Error('Smart form draft has no accept payload')
  }

  const response = await fetch(`${CENTER_BASE_URL}/api/forms/accept-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      template_id: draft.accept_payload.template_id,
      fields: draft.accept_payload.fields,
      output_path: draft.accept_payload.output_path,
      case_id: draft.accept_payload.case_id,
      notes: 'Accepted from Chitung desktop document diff panel.',
    }),
  })
  await ensureOk(response, 'Smart form accept failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function draftVisualPatrol(request: {
  cameraId?: string
  cameraUrl?: string
  source?: string
  area?: string
  contractor?: string
  count?: number
  analysisMode?: 'yolo_only' | 'hybrid'
  vlmEnabled?: boolean
  yoloConfThreshold?: number
  useGuardianPipeline?: boolean
}): Promise<VisualPatrolDraft> {
  const response = await fetch(`${CENTER_BASE_URL}/api/visual/patrol-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      camera_id: request.cameraId,
      camera_url: request.cameraUrl,
      source: request.source,
      area: request.area,
      contractor: request.contractor,
      count: request.count ?? 1,
      analysis_mode: request.analysisMode ?? 'hybrid',
      vlm_enabled: request.vlmEnabled ?? true,
      yolo_conf_threshold: request.yoloConfThreshold ?? 0.45,
      use_guardian_pipeline: request.useGuardianPipeline ?? true,
    }),
  })
  await ensureOk(response, 'Visual patrol draft failed')
  return response.json() as Promise<VisualPatrolDraft>
}

export async function runVisualPatrolBatch(request?: {
  cameraId?: string
  vlmEnabled?: boolean
  yoloOnly?: boolean
}): Promise<{ ok: boolean; report?: PatrolRunReport; error?: string; audit_id?: string }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/visual/patrol-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      camera_id: request?.cameraId,
      vlm_enabled: request?.vlmEnabled ?? true,
      yolo_only: request?.yoloOnly ?? false,
    }),
  })
  await ensureOk(response, 'Visual patrol batch failed')
  return response.json() as Promise<{ ok: boolean; report?: PatrolRunReport; error?: string; audit_id?: string }>
}

export async function listVisualPatrolRuns(limit = 20): Promise<PatrolRunSummary[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/visual/patrol-runs?limit=${limit}`)
  await ensureOk(response, 'Visual patrol runs failed')
  const data = (await response.json()) as { items?: PatrolRunSummary[] }
  return data.items ?? []
}

export async function getVisualPatrolRun(patrolId: string): Promise<PatrolRunReport> {
  const response = await fetch(`${CENTER_BASE_URL}/api/visual/patrol-runs/${encodeURIComponent(patrolId)}`)
  await ensureOk(response, 'Visual patrol run detail failed')
  const data = (await response.json()) as { report?: PatrolRunReport }
  if (!data.report) throw new Error('Patrol report missing')
  return data.report
}

export function visualPatrolAssetUrl(path?: string | null): string | undefined {
  if (!path) return undefined
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (path.startsWith('/api/visual/patrol-files/')) {
    return `${CENTER_BASE_URL}${path}`
  }
  return undefined
}

export async function confirmVisualPatrolCandidate(draft: VisualPatrolDraft): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/visual/confirm-candidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(draft.confirm_payload ?? {}),
  })
  await ensureOk(response, 'Visual patrol confirm failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function runCaseWorkflow(
  action: 'rectification-notice' | 'contractor-confirm' | 'close-review',
  request: {
    caseId: string
    contractor?: string
    dueDate?: string
    notes?: string
    reviewer?: string
    evidencePaths?: string[]
  },
): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/cases/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      case_id: Number(request.caseId),
      contractor: request.contractor,
      due_date: request.dueDate,
      notes: request.notes,
      reviewer: request.reviewer,
      evidence_paths: request.evidencePaths ?? [],
    }),
  })
  await ensureOk(response, 'Case workflow failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function generateReport(request: {
  reportType: 'community' | 'daily_safety' | 'rectification'
  caseId?: number
  title?: string
}): Promise<GeneratedReport> {
  const response = await fetch(`${CENTER_BASE_URL}/api/reports/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report_type: request.reportType,
      case_id: request.caseId,
      title: request.title,
    }),
  })
  await ensureOk(response, 'Report generation failed')
  return response.json() as Promise<GeneratedReport>
}

export async function sendCaseNotification(request: {
  caseId: string
  text: string
  contractor?: string
  channel: 'feishu' | 'whatsapp'
}): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/cases/send-notification`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      case_id: Number(request.caseId),
      text: request.text,
      contractor: request.contractor,
      channel: request.channel,
      confirmed_by: 'desktop_user',
    }),
  })
  await ensureOk(response, 'Notification send failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function searchWhatsAppMessages(request: {
  q: string
  chat?: string
  limit?: number
}): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/whatsapp/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      q: request.q,
      chat: request.chat,
      limit: request.limit ?? 20,
    }),
  })
  await ensureOk(response, 'WhatsApp search failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function getWhatsAppGroups(includeArchived = false): Promise<Record<string, unknown>> {
  const response = await fetch(`${CENTER_BASE_URL}/api/whatsapp/groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ include_archived: includeArchived }),
  })
  await ensureOk(response, 'WhatsApp groups query failed')
  return response.json() as Promise<Record<string, unknown>>
}

export async function createHybridPlan(request: {
  sessionId: string
  userInput: string
  preferCodex: boolean
  metadata?: Record<string, unknown>
}): Promise<{ ok: boolean; audit_id: string; plan: HybridPlan }> {
  const response = await fetch(`${CENTER_BASE_URL}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: request.sessionId,
      user_input: request.userInput,
      prefer_codex: request.preferCodex,
      metadata: request.metadata ?? {},
    }),
  })
  await ensureOk(response, 'Create hybrid plan failed')
  return response.json() as Promise<{ ok: boolean; audit_id: string; plan: HybridPlan }>
}

export async function confirmHybridPlan(request: {
  sessionId: string
  planId: string
  actionIds: string[]
  confirmedBy: string
  notes?: string
}): Promise<{ ok: boolean; audit_id: string; plan: HybridPlan }> {
  const response = await fetch(`${CENTER_BASE_URL}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: request.sessionId,
      plan_id: request.planId,
      action_ids: request.actionIds,
      confirmed_by: request.confirmedBy,
      notes: request.notes,
    }),
  })
  await ensureOk(response, 'Confirm hybrid plan failed')
  return response.json() as Promise<{ ok: boolean; audit_id: string; plan: HybridPlan }>
}

export async function executeHybridPlan(request: {
  sessionId: string
  planId: string
  idempotencyKey?: string
  retryFailedOnly?: boolean
  dryRun?: boolean
}): Promise<{ ok: boolean; audit_id: string; plan: HybridPlan; action_results: Array<Record<string, unknown>> }> {
  const response = await fetch(`${CENTER_BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: request.sessionId,
      plan_id: request.planId,
      idempotency_key: request.idempotencyKey,
      retry_failed_only: request.retryFailedOnly ?? true,
      dry_run: request.dryRun ?? false,
    }),
  })
  await ensureOk(response, 'Execute hybrid plan failed')
  return response.json() as Promise<{ ok: boolean; audit_id: string; plan: HybridPlan; action_results: Array<Record<string, unknown>> }>
}

export async function createAuditEvent(request: {
  eventType: string
  payload?: Record<string, unknown>
  sessionId?: string
  planId?: string
  actionId?: string
  status?: string
}): Promise<{ ok: boolean; audit_id: string }> {
  const response = await fetch(`${CENTER_BASE_URL}/audit/event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_type: request.eventType,
      payload: request.payload ?? {},
      session_id: request.sessionId,
      plan_id: request.planId,
      action_id: request.actionId,
      status: request.status,
    }),
  })
  await ensureOk(response, 'Create audit event failed')
  return response.json() as Promise<{ ok: boolean; audit_id: string }>
}

// ?? DocMate (????) API ?????????????????????????????????????

export async function docmateRead(filePath: string): Promise<DocmateReadResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/read`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath }),
  })
  await ensureOk(response, 'Docmate read failed')
  return response.json() as Promise<DocmateReadResult>
}

export async function docmateGenerate(payload: {
  docId: string
  instruction: string
  context?: string
}): Promise<DocmateGenerateResult> {
  const body: Record<string, unknown> = {
    doc_id: payload.docId,
    instruction: payload.instruction,
  }
  if (payload.context) {
    body.context = payload.context
  }
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  await ensureOk(response, 'Docmate generate failed')
  return response.json() as Promise<DocmateGenerateResult>
}

export async function docmatePreview(changesetId: string): Promise<DocmatePreviewResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ changeset_id: changesetId }),
  })
  await ensureOk(response, 'Docmate preview failed')
  return response.json() as Promise<DocmatePreviewResult>
}

export async function docmateApply(payload: {
  changesetId: string
  acceptedChangeIds: string[]
  saveAs?: string
}): Promise<DocmateApplyResult> {
  const body: Record<string, unknown> = {
    changeset_id: payload.changesetId,
    accepted_change_ids: payload.acceptedChangeIds,
  }
  if (payload.saveAs?.trim()) {
    body.save_as = payload.saveAs.trim()
  }
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  await ensureOk(response, 'Docmate apply failed')
  return response.json() as Promise<DocmateApplyResult>
}

export async function listTableMappingForms(): Promise<{
  scriptAvailable: boolean
  scriptDir: string
  items: TableMappingForm[]
}> {
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/table-mapping/forms`)
  await ensureOk(response, 'Table mapping forms failed')
  const data = (await response.json()) as {
    script_available?: boolean
    script_dir?: string
    items?: TableMappingForm[]
  }
  return {
    scriptAvailable: Boolean(data.script_available),
    scriptDir: data.script_dir ?? '',
    items: data.items ?? [],
  }
}

export async function extractTableMappingFields(request: {
  filePath: string
  formId: string
}): Promise<TableMappingExtractResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/table-mapping/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_path: request.filePath,
      form_id: request.formId,
    }),
  })
  await ensureOk(response, 'Table mapping extract failed')
  return response.json() as Promise<TableMappingExtractResult>
}

export async function runTableMappingFill(request: {
  filePath: string
  formId: string
  fields?: Record<string, string>
  action?: 'draft' | 'save_draft'
  screenshot?: boolean
  dryRun?: boolean
}): Promise<TableMappingRunResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/docmate/table-mapping/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_path: request.filePath,
      form_id: request.formId,
      fields: request.fields,
      action: request.action ?? 'draft',
      screenshot: request.screenshot ?? true,
      dry_run: request.dryRun ?? false,
    }),
  })
  await ensureOk(response, 'Table mapping run failed')
  return response.json() as Promise<TableMappingRunResult>
}

// ?? Yaoyao (structured input / OCR) API ????????????????????????

export async function createYaoyaoStructuredDraft(request: {
  filePath: string
  pageIndex?: number
  regions?: YaoyaoRegion[]
  templateId?: string
  caseId?: number
  renderWidth?: number
  renderHeight?: number
}): Promise<YaoyaoStructuredDraft> {
  const response = await fetch(`${CENTER_BASE_URL}/api/yaoyao/structured/draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_path: request.filePath,
      page_index: request.pageIndex,
      regions: request.regions ?? [],
      template_id: request.templateId,
      case_id: request.caseId,
      render_width: request.renderWidth ?? 2000,
      render_height: request.renderHeight ?? 2800,
    }),
  })
  await ensureOk(response, 'Yaoyao structured draft failed')
  return response.json() as Promise<YaoyaoStructuredDraft>
}

export async function confirmYaoyaoStructuredDraft(request: {
  draftId: string
  fields: Record<string, unknown>
  templateId?: string
  caseId?: number
  notes?: string
}): Promise<YaoyaoConfirmResult> {
  const response = await fetch(`${CENTER_BASE_URL}/api/yaoyao/structured/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      draft_id: request.draftId,
      fields: request.fields,
      template_id: request.templateId,
      case_id: request.caseId,
      notes: request.notes,
    }),
  })
  await ensureOk(response, 'Yaoyao structured confirm failed')
  return response.json() as Promise<YaoyaoConfirmResult>
}

export async function saveYaoyaoTemplate(request: {
  regions: YaoyaoRegion[]
  rows?: Array<Record<string, unknown>>
  name?: string
  templateId?: string
}): Promise<{ ok: boolean; template_id: string; name: string; path: string }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/yaoyao/template/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      regions: request.regions,
      rows: request.rows ?? [],
      name: request.name,
      template_id: request.templateId,
    }),
  })
  await ensureOk(response, 'Yaoyao template save failed')
  return response.json() as Promise<{ ok: boolean; template_id: string; name: string; path: string }>
}

export async function getYaoyaoTemplate(templateId: string): Promise<{ ok: boolean; template: YaoyaoTemplate }> {
  const response = await fetch(`${CENTER_BASE_URL}/api/yaoyao/template/${encodeURIComponent(templateId)}`)
  await ensureOk(response, 'Yaoyao template load failed')
  return response.json() as Promise<{ ok: boolean; template: YaoyaoTemplate }>
}

export async function listYaoyaoTemplates(): Promise<YaoyaoTemplateListItem[]> {
  const response = await fetch(`${CENTER_BASE_URL}/api/yaoyao/template/list`)
  await ensureOk(response, 'Yaoyao template list failed')
  const data = (await response.json()) as { items?: YaoyaoTemplateListItem[] }
  return data.items ?? []
}

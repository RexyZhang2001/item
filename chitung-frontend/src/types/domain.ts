export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface StatusMetric {
  id: string
  label: string
  value: string | number
  tone: 'red' | 'orange' | 'green' | 'blue' | 'gray'
  helper: string
}

export interface HazardCase {
  id: string
  title: string
  area: string
  riskLevel: RiskLevel
  status: string
  dueText: string
}

export interface SafetyCaseRecord {
  id: number
  status?: string
  source_type?: string
  scene?: string
  risk_level?: RiskLevel | string
  area?: string
  contractor?: string
  description?: string
  recommended_action?: string
  created_at?: string
  updated_at?: string
}

export interface WorkflowStep {
  id: string
  label: string
  status: 'done' | 'active' | 'pending'
}

export interface ActivityItem {
  id: string
  time: string
  title: string
  description: string
  actionLabel?: string
}

export interface WorkbenchStatus {
  center_ok: boolean
  toolbox_ok: boolean
  toolbox_base_url: string
  llm_configured: boolean
}

export interface WorkbenchSummary {
  status: WorkbenchStatus
  metrics: StatusMetric[]
  hazards: HazardCase[]
  activities: ActivityItem[]
  workflow_steps: WorkflowStep[]
}

export interface PendingConfirmation {
  confirmation_id: string
  action_type: string
  title: string
  summary?: string
  status: string
  risk_level?: RiskLevel | string
  source_channel?: string
  source_user_id?: string
  payload?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface ChatResponse {
  type: 'reply' | 'review_card' | 'workflow'
  message: string
  workflowId?: string
  payload?: Record<string, unknown>
}

export interface CenterChatResponse {
  reply: string
  intent?: {
    intent: string
    confidence: number
    reason: string
    suggested_tools?: string[]
  }
  cards?: Array<Record<string, unknown>>
  tool_results?: Array<Record<string, unknown>>
  audit_id?: string
}

export type DocumentDiffLineType = 'context' | 'added' | 'removed'

export interface DocumentDiffLine {
  id: string
  type: DocumentDiffLineType
  text: string
}

export interface DocumentRevisionPreview {
  id: string
  title: string
  source: string
  instruction: string
  additions: number
  deletions: number
  status: 'draft' | 'accepted' | 'rejected'
  llm?: Record<string, unknown>
  lines: DocumentDiffLine[]
}

export interface SmartFormTemplate {
  id: string
  title?: string
  policy_context?: string
  docx_path?: string
}

export interface SmartFormDraft {
  ok: boolean
  message: string
  requires_acceptance: boolean
  templates: SmartFormTemplate[]
  selected_template?: SmartFormTemplate
  prefill?: {
    fields: Record<string, unknown>
  }
  docx_draft?: {
    output_path?: string
    payload_path?: string
    files?: Array<Record<string, unknown>>
  }
  revision_preview?: DocumentRevisionPreview
  accept_payload?: {
    template_id: string
    fields: Record<string, unknown>
    output_path?: string
    case_id?: number | null
  }
}

export interface VisualPatrolCandidate {
  id: string
  title: string
  risk_level: RiskLevel
  area: string
  description: string
  labels: string[]
  task_id?: string
  source_mix?: string
  severity?: string
  suggested_action?: string
  detection_details?: Array<{
    bbox: number[]
    label: string
    confidence: number
    source: string
    description?: string
    severity?: string
    suggested_action?: string
  }>
}

export interface VisualPatrolDraft {
  ok: boolean
  message: string
  requires_confirmation: boolean
  source?: string
  patrol_id?: string
  camera_id?: string
  camera_name?: string
  snapshot_url?: string
  annotated_url?: string
  snapshot?: Record<string, unknown> | null
  vlm?: Record<string, unknown> | null
  candidates: VisualPatrolCandidate[]
  confirm_payload?: Record<string, unknown>
  analysis_mode?: string
  report?: PatrolRunReport
}

export interface PatrolRunSummary {
  patrol_id: string
  timestamp?: string
  camera_count?: number
  success_count?: number
  total_detections?: number
  high_risk_count?: number
  hybrid_cameras?: number
  vlm_enabled?: boolean
}

export interface PatrolCameraResult {
  camera_id: string
  camera_name: string
  area: string
  success: boolean
  snapshot_path?: string | null
  annotated_path?: string | null
  snapshot_url?: string
  annotated_url?: string
  detection_count?: number
  detections?: Array<Record<string, unknown>>
  error?: string
  yolo_time_ms?: number
  vlm_time_ms?: number
  source_mix?: string
}

export interface PatrolRunReport {
  patrol_id: string
  timestamp?: string
  camera_count?: number
  success_count?: number
  fail_count?: number
  total_detections?: number
  hybrid_cameras?: number
  high_risk_count?: number
  vlm_enabled?: boolean
  cameras?: PatrolCameraResult[]
  output_dir?: string
}

export interface LlmSettingsStatus {
  configured: boolean
  base_url: string
  model: string
  api_key_masked: string
}

export interface LlmTestResult {
  ok: boolean
  message: string
  model: string
  raw_keys?: string[]
}

export interface ConnectorSettingsStatus {
  whatsapp: {
    configured: boolean
    archive_base_url: string
  }
  feishu: {
    configured: boolean
    webhook_configured: boolean
    app_id: string
    app_secret_masked: string
    webhook_url: string
    webhook_secret_masked: string
    verification_token_masked: string
    encrypt_key_masked: string
    api_base_url: string
  }
  requires_toolbox_restart: boolean
}

export interface RuntimeComponentStatus {
  name: string
  ok: boolean
  path?: string
  url?: string
  configured?: boolean
  error?: string
}

export interface RuntimeStatus {
  center: {
    ok: boolean
    service: string
    url: string
  }
  llm: LlmSettingsStatus
  toolbox: {
    ok: boolean
    base_url: string
    raw_ok: boolean
    required: RuntimeComponentStatus[]
    optional: RuntimeComponentStatus[]
  }
  ready: boolean
}

export interface CameraConfig {
  id: string
  name: string
  area: string
  rtmp_url?: string | null
  enabled: boolean
}

export interface ContractorConfig {
  id: string
  name: string
  contact?: string | null
  channel?: string | null
  default_due_days: number
}

export interface AppConfig {
  project: {
    name: string
    default_area: string
    location: string
  }
  cameras: CameraConfig[]
  contractors: ContractorConfig[]
}

export interface NotificationDraft {
  caseId: string
  contractor: string
  contact?: string | null
  channel?: string | null
  draftText: string
  status: 'draft' | 'confirmed'
}

export interface ExternalRiskBriefing {
  title: string
  summary: string
  items: string[]
}

export interface GeneratedOutputItem {
  id: string
  title: string
  kind: 'docx' | 'payload' | 'image' | 'report' | 'notification' | 'other'
  path?: string
  content?: string
  createdAt: string
}

export interface GeneratedReport {
  ok: boolean
  message: string
  report_type: 'community' | 'daily_safety' | 'rectification'
  output_path?: string
  files?: Array<Record<string, unknown>>
}

export interface HybridAction {
  action_id: string
  sequence_no: number
  tool_name: string
  payload: Record<string, unknown>
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  requires_confirmation: boolean
  status: string
  retry_count: number
  max_retries: number
  result?: Record<string, unknown>
  last_error?: string | null
}

export interface HybridPlan {
  plan_id: string
  session_id: string
  user_input: string
  workflow: string
  planner_mode: string
  status: string
  fallback_used: boolean
  fallback_reason?: string | null
  selected_action_ids: string[]
  idempotency_key?: string | null
  result?: Record<string, unknown>
  last_error?: string | null
  actions: HybridAction[]
}

// ── DocMate (闪闪文档) 类型 ──────────────────────────────────────

export interface DocmateDocumentStructure {
  doc_id?: string
  source_path?: string
  filename?: string
  stats: {
    paragraph_count: number
    table_count: number
    image_count: number
    total_chars?: number
  }
  structure: {
    paragraphs: Array<{
      index: number
      text: string
      style: string
      type: string
    }>
    tables: Array<{
      index: number
      rows: number
      cols: number
      data: string[][]
      type: string
    }>
  }
}

export interface DocmateChange {
  change_id: string
  type: string
  target: string
  replacement?: string
  paragraph_index?: number
  context_before?: string
  occurrences?: number
  risk_level: RiskLevel
  confidence: number
  status?: string
}

export interface DocmatePreviewCard {
  change_id: string
  title: string
  before: string
  after: string
  type: string
  risk_level: RiskLevel
  confidence: number
}

export interface DocmateReadResult {
  ok: boolean
  tool?: string
  task_id?: string
  summary?: string
  data: DocmateDocumentStructure
  error?: string
}

export interface DocmateGenerateResult {
  ok: boolean
  tool?: string
  task_id?: string
  summary?: string
  data: {
    changeset_id: string
    doc_id?: string
    instruction?: string
    changes: DocmateChange[]
    preview_cards: DocmatePreviewCard[]
    total_changes: number
  }
  error?: string
}

export interface DocmatePreviewResult {
  ok: boolean
  tool?: string
  task_id?: string
  summary?: string
  data: {
    changeset_id: string
    instruction?: string
    preview_cards: DocmatePreviewCard[]
    total_changes: number
  }
  error?: string
}

export interface DocmateApplyResult {
  ok: boolean
  tool?: string
  task_id?: string
  summary?: string
  data: {
    applied: number
    rejected: number
    errors: string[]
    output_path: string
    backup_path: string
    source_path?: string
  }
  error?: string
}

export interface DocmateSessionState {
  step: 'idle' | 'loaded' | 'generated' | 'previewed' | 'applied'
  docId: string
  sourcePath: string
  structure: DocmateDocumentStructure | null
  changesetId: string
  changes: DocmateChange[]
  previewCards: DocmatePreviewCard[]
  instruction: string
  outputPath: string
  error: string | null
}

export interface TableMappingFieldDef {
  name: string
  type?: string
  required?: boolean
}

export interface TableMappingForm {
  id: string
  name: string
  category?: string
  fields: TableMappingFieldDef[]
}

export interface TableMappingExtractedField {
  value: string
  source: string
  confidence: number
}

export interface TableMappingExtractResult {
  ok: boolean
  form: TableMappingForm
  source_path: string
  fields: Record<string, TableMappingExtractedField>
  matched_count: number
  document_preview: string
  script_available: boolean
}

export interface TableMappingRunResult {
  ok: boolean
  job_id: string
  dry_run: boolean
  form: TableMappingForm
  source_path: string
  fields: Record<string, string>
  extracted: Record<string, TableMappingExtractedField>
  command: string[]
  exit_code?: number
  duration_ms?: number
  stdout?: string
  stderr?: string
}

// ── Yaoyao (structured input / OCR) types ──────────────────────

export interface YaoyaoRegion {
  name: string
  x: number
  y: number
  width: number
  height: number
  angle: number
}

export interface YaoyaoFieldCandidate {
  field_name: string
  value: string
  confidence: number
  source_region: string
  page_number: number
}

export interface YaoyaoStructuredDraft {
  ok: boolean
  message: string
  draft_id: string
  preview_image_path?: string | null
  pages: Array<{
    page_number: number
    values: Record<string, string>
  }>
  field_candidates: YaoyaoFieldCandidate[]
  page_count: number
  elapsed_seconds: number
  requires_acceptance: boolean
  confirm_payload: {
    draft_id: string
    template_id?: string | null
    case_id?: number | null
  }
}

export interface YaoyaoConfirmResult {
  ok: boolean
  message: string
  record_id: string | number
  output_path: string
  audit_id: string
}

export interface YaoyaoTemplate {
  id: string
  name: string
  created_at: string
  regions: YaoyaoRegion[]
  rows: Array<{
    page: number
    values: Record<string, string>
  }>
}

export interface YaoyaoTemplateListItem {
  id: string
  name: string
  created_at: string
  region_count: number
  row_count: number
}

export interface SkillInfo {
  name: string
  path: string
  summary: string
  enabled?: boolean
  category?: string
  status?: 'done' | 'ready' | 'dep' | 'later'
  phase?: string
  tools?: string[]
  workflow?: string
}

export interface SkillDetail {
  name: string
  content: string
}

export interface WorkflowTemplateInfo {
  workflow_name: string
  title: string
  description: string
  intent: string
  step_count: number
}

export interface WorkflowInfo {
  name: string
  path: string
  summary: string
  enabled: boolean
  category: string
  status: string
  phase: string
  priority?: string
  triggers?: string
  agents?: string
  steps?: Array<Record<string, unknown>>
  existing_tools?: string[]
  pending_tools?: string[]
}

export interface WorkflowDetail {
  name: string
  content: string
  meta?: WorkflowInfo | null
}

export interface RagDocument {
  doc_id: string
  file_name: string
  file_type: string
  chunk_count: number
  collection?: string
  created_at: string
}

export interface RagQueryMatch {
  text: string
  source_file_name: string
  doc_id: string
  chunk_index: number
  collection: string
  score?: number | null
}

export interface RagStats {
  ok: boolean
  document_count: number
  chunk_count: number
  vector_count: number
  chroma_dir?: string
}

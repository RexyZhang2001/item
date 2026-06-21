<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ActiveHazards from '../components/cards/ActiveHazards.vue'
import ActivityFeed from '../components/cards/ActivityFeed.vue'
import ActionReviewCards from '../components/cards/ActionReviewCards.vue'
import CameraGrid from '../components/cards/CameraGrid.vue'
import DocumentDiffPanel from '../components/documents/DocumentDiffPanel.vue'
import FormTemplateBrowserPanel from '../components/forms/FormTemplateBrowserPanel.vue'
import HazardLedgerPanel from '../components/hazards/HazardLedgerPanel.vue'
import SystemSettingsPanel from '../components/system/SystemSettingsPanel.vue'
import HybridOrchestrationPanel from '../components/system/HybridOrchestrationPanel.vue'
import StatusStrip from '../components/cards/StatusStrip.vue'
import CommandBar from '../components/layout/CommandBar.vue'
import ProgressChain from '../components/workflow/ProgressChain.vue'
import { useAppNavigation } from '../composables/useAppNavigation'
import {
  acceptSmartFormDraft,
  confirmVisualPatrolCandidate,
  confirmHybridPlan,
  createAuditEvent,
  createHybridPlan,
  draftVisualPatrol,
  draftSmartForm,
  executeHybridPlan,
  generateReport,
  getAppConfig,
  getConnectorSettings,
  getHazards,
  getHealth,
  getLlmSettings,
  getRuntimeStatus,
  getWorkbenchSummary,
  runCaseWorkflow,
  saveAppConfig,
  saveConnectorSettings,
  saveLlmSettings,
  searchFormTemplates,
  sendCaseNotification,
  sendCardAction,
  sendChatMessage,
  testLlmSettings,
  updateHazardStatus,
} from '../services/chitungApi'
import type {
  ActivityItem,
  AppConfig,
  ConnectorSettingsStatus,
  DocumentRevisionPreview,
  ExternalRiskBriefing,
  GeneratedOutputItem,
  HazardCase,
  LlmSettingsStatus,
  NotificationDraft,
  RuntimeStatus,
  SafetyCaseRecord,
  HybridPlan,
  SmartFormDraft,
  SmartFormTemplate,
  StatusMetric,
  VisualPatrolDraft,
  WorkflowStep,
} from '../types/domain'

type ReviewCard = {
  card_type?: string
  title: string
  summary: string
  actions?: Array<{ id: string; label: string }>
  data?: Record<string, unknown>
}

const { goTo, goToPendingConfirmations } = useAppNavigation()

const metrics = ref<StatusMetric[]>([])
const hazards = ref<HazardCase[]>([])
const hazardRecords = ref<SafetyCaseRecord[]>([])

const workflowSteps = ref<WorkflowStep[]>([
  { id: 'intent', label: '识别意图', status: 'pending' },
  { id: 'tool', label: '调用工具', status: 'pending' },
  { id: 'confirm', label: '等待确认', status: 'pending' },
])

const activities = ref<ActivityItem[]>([])
const summaryLoadError = ref('')

const documentRevision = ref<DocumentRevisionPreview | null>(null)
const smartFormDraft = ref<SmartFormDraft | null>(null)
const formTemplates = ref<SmartFormTemplate[]>([])
const notificationDraft = ref<NotificationDraft | null>(null)
const externalRiskBriefing = ref<ExternalRiskBriefing | null>(null)
const generatedOutputs = ref<GeneratedOutputItem[]>([])
const isLoadingBriefing = ref(false)
const isGeneratingReport = ref(false)

const aiMessages = ref<string[]>([
  '工作台已就绪。你可以输入“检查 B2 摄像头”“生成今日简报”或“帮我填 T006”。',
])
const reviewCards = ref<ReviewCard[]>([])
const isCardActionBusy = ref(false)
const isSending = ref(false)
const isPatrolling = ref(false)
const isLoadingHazards = ref(false)
const isSearchingTemplates = ref(false)
const isSavingLlmSettings = ref(false)
const isTestingLlm = ref(false)
const isSavingConnectors = ref(false)
const isSavingAppConfig = ref(false)
const isRestartingServices = ref(false)
const centerHealth = ref<Record<string, unknown> | null>(null)
const llmSettings = ref<LlmSettingsStatus | null>(null)
const connectorSettings = ref<ConnectorSettingsStatus | null>(null)
const runtimeStatus = ref<RuntimeStatus | null>(null)
const appConfig = ref<AppConfig | null>(null)
const runtime = ref<ChitungDesktopRuntime | null>(null)
const visualPatrolDraft = ref<VisualPatrolDraft | null>(null)
const hybridPanelRef = ref<{ syncPlan: (plan: HybridPlan) => void; pushLog: (line: string) => void } | null>(null)

const centerStatusText = computed(() => {
  if (!centerHealth.value) {
    return '中台未连接 · 工具层待启动'
  }

  const llmText = centerHealth.value.llm_configured ? 'LLM 已接入' : 'LLM 未配置'
  return `中台已连接 · ${llmText}`
})

async function refreshWorkbenchSummary() {
  summaryLoadError.value = ''
  try {
    const summary = await getWorkbenchSummary()
    metrics.value = summary.metrics
    hazards.value = summary.hazards
    activities.value = summary.activities
    workflowSteps.value = summary.workflow_steps
  } catch (error) {
    summaryLoadError.value = error instanceof Error ? error.message : String(error)
    metrics.value = []
    hazards.value = []
    activities.value = []
  }
}

async function refreshHazardRecords() {
  isLoadingHazards.value = true
  try {
    hazardRecords.value = await getHazards()
  } finally {
    isLoadingHazards.value = false
  }
}

async function handleSearchTemplates(query: string) {
  isSearchingTemplates.value = true
  try {
    formTemplates.value = await searchFormTemplates(query)
    aiMessages.value.unshift(`赤瞳：已找到 ${formTemplates.value.length} 个表格模板候选。`)
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：模板搜索失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isSearchingTemplates.value = false
  }
}

async function refreshSystemStatus() {
  centerHealth.value = await getHealth()
  llmSettings.value = await getLlmSettings()
  connectorSettings.value = await getConnectorSettings()
  runtimeStatus.value = await getRuntimeStatus()
  appConfig.value = await getAppConfig()
}

onMounted(async () => {
  try {
    await refreshSystemStatus()
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
    await handleSearchTemplates('临边 整改')
  } catch (error) {
    centerHealth.value = null
    aiMessages.value.unshift(`赤瞳：后端连接失败：${error instanceof Error ? error.message : String(error)}`)
  }

  if (window.chitungDesktop) {
    runtime.value = await window.chitungDesktop.getRuntime()
  }
})

async function handleSaveLlmSettings(payload: { baseUrl: string; apiKey: string; model: string }) {
  isSavingLlmSettings.value = true
  try {
    const result = await saveLlmSettings(payload)
    llmSettings.value = result.status
    await refreshSystemStatus()
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
    aiMessages.value.unshift('赤瞳：统一大模型 API 已保存，后续 AI 文档改写会走中台 LLM Gateway。')
  } catch {
    aiMessages.value.unshift('赤瞳：模型配置保存失败，请检查中台是否运行。')
  } finally {
    isSavingLlmSettings.value = false
  }
}

async function handleTestLlmSettings() {
  isTestingLlm.value = true
  try {
    const result = await testLlmSettings()
    const tone = result.ok ? '连接成功' : '连接失败'
    aiMessages.value.unshift(`赤瞳：LLM ${tone}：${result.message}`)
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：LLM 测试失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isTestingLlm.value = false
  }
}

async function handleSaveAppConfig(payload: AppConfig) {
  isSavingAppConfig.value = true
  try {
    const result = await saveAppConfig(payload)
    appConfig.value = result.config
    aiMessages.value.unshift('赤瞳：项目、摄像头和分包商配置已保存。')
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：项目配置保存失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isSavingAppConfig.value = false
  }
}

async function handleSaveConnectors(payload: {
  whatsappArchiveBaseUrl: string
  feishuWebhookUrl: string
  feishuWebhookSecret: string
  feishuAppId: string
  feishuAppSecret: string
  feishuVerificationToken: string
  feishuEncryptKey: string
  feishuApiBaseUrl: string
}) {
  isSavingConnectors.value = true
  try {
    const result = await saveConnectorSettings(payload)
    connectorSettings.value = result.status
    await refreshSystemStatus()
    aiMessages.value.unshift('赤瞳：WhatsApp / 飞书连接器配置已保存，重启工具层后运行中服务会重新加载。')
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：连接器配置保存失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isSavingConnectors.value = false
  }
}

function openServiceLogDir() {
  if (!runtime.value?.logDir) {
    aiMessages.value.unshift('赤瞳：当前无法获取桌面服务日志目录。')
    return
  }
  showLocalFile(runtime.value.logDir)
}

async function restartDesktopServices() {
  if (!window.chitungDesktop) {
    aiMessages.value.unshift('赤瞳：当前不是桌面环境，请在终端重启 chitung-center 和 agent-toolbox。')
    return
  }
  isRestartingServices.value = true
  try {
    const result = await window.chitungDesktop.restartServices()
    if (!result.ok) {
      aiMessages.value.unshift(`赤瞳：本地服务重启失败：${result.error || '未知错误'}`)
      return
    }
    aiMessages.value.unshift('赤瞳：已请求重启桌面托管的本地服务，正在刷新状态。')
    await refreshSystemStatus()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：本地服务重启失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isRestartingServices.value = false
  }
}

async function openLocalFile(path?: string) {
  if (!path) {
    aiMessages.value.unshift('赤瞳：没有可打开的文件路径。')
    return
  }
  if (!window.chitungDesktop) {
    aiMessages.value.unshift(`赤瞳：当前不是桌面环境，文件路径为：${path}`)
    return
  }
  const result = await window.chitungDesktop.openPath(path)
  if (!result.ok) {
    aiMessages.value.unshift(`赤瞳：打开文件失败：${result.error || path}`)
  }
}

async function showLocalFile(path?: string) {
  if (!path) {
    aiMessages.value.unshift('赤瞳：没有可定位的文件路径。')
    return
  }
  if (!window.chitungDesktop) {
    aiMessages.value.unshift(`赤瞳：当前不是桌面环境，文件路径为：${path}`)
    return
  }
  const result = await window.chitungDesktop.showInFolder(path)
  if (!result.ok) {
    aiMessages.value.unshift(`赤瞳：定位文件失败：${result.error || path}`)
  }
}

const smartFormOutputPath = computed(() => smartFormDraft.value?.docx_draft?.output_path)
const smartFormPayloadPath = computed(() => smartFormDraft.value?.docx_draft?.payload_path)

function recordGeneratedOutput(item: Omit<GeneratedOutputItem, 'id' | 'createdAt'>) {
  const duplicateKey = item.path || `${item.kind}:${item.title}:${item.content}`
  generatedOutputs.value = [
    {
      ...item,
      id: `${item.kind}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      createdAt: new Date().toLocaleString(),
    },
    ...generatedOutputs.value.filter((existing) => (existing.path || `${existing.kind}:${existing.title}:${existing.content}`) !== duplicateKey),
  ].slice(0, 12)
}

function recordVisualEvidence(draft: VisualPatrolDraft) {
  const paths = [
    draft.source,
    String(draft.confirm_payload?.image_path || ''),
    ...((draft.snapshot?.files as Array<Record<string, unknown>> | undefined)?.map((file) => String(file.path || '')) ?? []),
    ...((draft.vlm?.files as Array<Record<string, unknown>> | undefined)?.map((file) => String(file.path || '')) ?? []),
  ].filter((path): path is string => Boolean(path))
  for (const path of [...new Set(paths)]) {
    recordGeneratedOutput({
      title: path.match(/\.(jpg|jpeg|png|webp)$/i) ? '视觉巡检截图/证据' : '视觉巡检输出文件',
      kind: path.match(/\.(jpg|jpeg|png|webp)$/i) ? 'image' : 'other',
      path,
    })
  }
}

async function handleCommand(message: string) {
  aiMessages.value.unshift(`你：${message}`)
  isSending.value = true
  workflowSteps.value = [
    { id: 'intent', label: '识别意图', status: 'active' },
    { id: 'tool', label: '调用工具', status: 'pending' },
    { id: 'confirm', label: '等待确认', status: 'pending' },
  ]

  try {
    const response = await sendChatMessage({
      message,
      context: {
        current_area: 'B2',
        entry: 'workbench_command_bar',
      },
    })
    aiMessages.value.unshift(`赤瞳：${response.message}`)
    reviewCards.value = ((response.payload?.cards as ReviewCard[] | undefined) ?? []).map((card) => ({
      card_type: card.card_type,
      title: card.title,
      summary: card.summary,
      actions: card.actions,
      data: card.data,
    }))
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
    workflowSteps.value = [
      { id: 'intent', label: '识别意图', status: 'done' },
      { id: 'tool', label: '调用工具', status: 'done' },
      { id: 'confirm', label: '等待确认', status: response.type === 'review_card' ? 'active' : 'pending' },
    ]
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：暂时无法连接中台：${error instanceof Error ? error.message : String(error)}`)
    workflowSteps.value = [
      { id: 'intent', label: '识别意图', status: 'done' },
      { id: 'tool', label: '调用工具', status: 'active' },
      { id: 'confirm', label: '等待确认', status: 'pending' },
    ]
  } finally {
    isSending.value = false
  }
}

async function handleReviewCardAction(actionId: string, card: ReviewCard) {
  isCardActionBusy.value = true
  try {
    const result = await sendCardAction({
      actionId,
      cardData: card.data ?? {},
    })
    const message = typeof result.message === 'string' ? result.message : '卡片动作已提交。'
    aiMessages.value.unshift(`赤瞳：${message}`)
    const navigateTo = typeof result.navigate_to === 'string' ? result.navigate_to : ''
    if (navigateTo === 'pending-confirmations' || result.confirmation) {
      goToPendingConfirmations()
    } else if (navigateTo === 'visual-patrol') {
      goTo('visual-patrol')
    } else if (navigateTo === 'shanshan-doc' || actionId === 'open_shanshan_doc') {
      goTo('shanshan-doc')
    } else if (navigateTo === 'smart-form') {
      goTo('smart-form')
    }
    await refreshWorkbenchSummary()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：卡片动作失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isCardActionBusy.value = false
  }
}

async function handleConfirmHazard(caseId: string) {
  if (!/^\d+$/.test(caseId)) {
    aiMessages.value.unshift('赤瞳：当前为演示隐患，启动中台和工具层后可执行确认。')
    return
  }

  try {
    await updateHazardStatus(caseId, 'confirmed')
    aiMessages.value.unshift(`赤瞳：已确认隐患 #${caseId}，台账已刷新。`)
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：隐患确认失败：${error instanceof Error ? error.message : String(error)}`)
  }
}

async function handleVisualPatrol(cameraId?: string) {
  isPatrolling.value = true
  workflowSteps.value = [
    { id: 'snapshot', label: 'RTMP 截图', status: 'active' },
    { id: 'vlm', label: 'VLM 检测', status: 'pending' },
    { id: 'confirm', label: '人工确认', status: 'pending' },
  ]

  try {
    const camera =
      appConfig.value?.cameras.find((item) => item.id === cameraId) ??
      appConfig.value?.cameras.find((item) => item.enabled) ??
      appConfig.value?.cameras[0]
    visualPatrolDraft.value = await draftVisualPatrol({
      area: camera?.area ?? appConfig.value?.project.default_area ?? 'B2',
      cameraUrl: camera?.rtmp_url ?? undefined,
      count: 1,
    })
    recordVisualEvidence(visualPatrolDraft.value)
    workflowSteps.value = [
      { id: 'snapshot', label: 'RTMP 截图', status: 'done' },
      { id: 'vlm', label: 'VLM 检测', status: 'done' },
      { id: 'confirm', label: '人工确认', status: 'active' },
    ]
    aiMessages.value.unshift('赤瞳：视觉巡检已生成隐患候选，请人工确认后入库。')
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：视觉巡检失败：${error instanceof Error ? error.message : String(error)}`)
    workflowSteps.value = [
      { id: 'snapshot', label: 'RTMP 截图', status: 'active' },
      { id: 'vlm', label: 'VLM 检测', status: 'pending' },
      { id: 'confirm', label: '人工确认', status: 'pending' },
    ]
  } finally {
    isPatrolling.value = false
  }
}

async function handleConfirmVisualCandidate() {
  if (!visualPatrolDraft.value) return

  try {
    await confirmVisualPatrolCandidate(visualPatrolDraft.value)
    aiMessages.value.unshift('赤瞳：视觉巡检候选已确认入库，隐患台账已刷新。')
    visualPatrolDraft.value = null
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：视觉候选入库失败：${error instanceof Error ? error.message : String(error)}`)
  }
}

async function handleCaseWorkflow(action: 'rectification-notice' | 'contractor-confirm' | 'close-review', caseId: string) {
  if (!/^\d+$/.test(caseId)) {
    aiMessages.value.unshift('赤瞳：当前为演示隐患，真实台账记录才可执行闭环动作。')
    return
  }

  try {
    const result = await runCaseWorkflow(action, {
      caseId,
      contractor: appConfig.value?.contractors[0]?.name ?? '待确认分包商',
      dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
      notes: 'Confirmed from Chitung desktop workbench.',
      reviewer: '安全主任',
    })
    if (action === 'rectification-notice') {
      const contractor = appConfig.value?.contractors[0]
      notificationDraft.value = {
        caseId,
        contractor: contractor?.name ?? '待确认分包商',
        contact: contractor?.contact,
        channel: contractor?.channel,
        draftText: String((result.notice as Record<string, unknown> | undefined)?.draft_text || result.message || '整改通知草稿已生成。'),
        status: 'draft',
      }
      recordGeneratedOutput({
        title: `整改通知草稿 #${caseId}`,
        kind: 'notification',
        content: notificationDraft.value.draftText,
      })
    }
    aiMessages.value.unshift(`赤瞳：${String(result.message || '隐患闭环动作已完成')}`)
    await refreshWorkbenchSummary()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：隐患闭环动作失败：${error instanceof Error ? error.message : String(error)}`)
  }
}

async function confirmNotificationDraft() {
  if (!notificationDraft.value) return
  try {
    const channel = notificationDraft.value.channel?.toLowerCase().includes('whatsapp') ? 'whatsapp' : 'feishu'
    const sendResult = await sendCaseNotification({
      caseId: notificationDraft.value.caseId,
      text: notificationDraft.value.draftText,
      contractor: notificationDraft.value.contractor,
      channel,
    })
    await runCaseWorkflow('contractor-confirm', {
      caseId: notificationDraft.value.caseId,
      contractor: notificationDraft.value.contractor,
      dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
      notes: `Notification draft confirmed for ${notificationDraft.value.contractor}.`,
    })
    notificationDraft.value = { ...notificationDraft.value, status: 'confirmed' }
    aiMessages.value.unshift(`赤瞳：整改通知已确认：${String(sendResult.message || '发送结果已回写。')}`)
    await refreshWorkbenchSummary()
    await refreshHazardRecords()
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：整改通知确认失败：${error instanceof Error ? error.message : String(error)}`)
  }
}

async function generateDailyBriefing() {
  isLoadingBriefing.value = true
  try {
    const response = await sendChatMessage({
      message: '生成今日香港天气和施工安全新闻风险简报',
      context: { entry: 'daily_briefing_button' },
    })
    const toolResults = (response.payload?.toolResults as Array<Record<string, unknown>> | undefined) ?? []
    externalRiskBriefing.value = {
      title: '今日外部风险简报',
      summary: response.message,
      items: toolResults.map((item) => String(item.summary || item.tool_name || item.tool || '外部风险工具已执行')).slice(0, 5),
    }
    aiMessages.value.unshift(`赤瞳：${response.message}`)
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：每日简报生成失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isLoadingBriefing.value = false
  }
}

async function handleGenerateReport(reportType: 'community' | 'daily_safety' | 'rectification') {
  isGeneratingReport.value = true
  try {
    const report = await generateReport({
      reportType,
      title: reportType === 'community' ? '社区建设报告' : reportType === 'rectification' ? '整改报告' : '每日安全日报',
    })
    if (report.output_path) {
      recordGeneratedOutput({
        title: report.message,
        kind: report.output_path.endsWith('.docx') ? 'docx' : 'report',
        path: report.output_path,
      })
    }
    aiMessages.value.unshift(`赤瞳：${report.message}`)
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：报告生成失败：${error instanceof Error ? error.message : String(error)}`)
  } finally {
    isGeneratingReport.value = false
  }
}

async function handleAcceptDocumentRevision() {
  if (!documentRevision.value) return
  try {
    if (smartFormDraft.value?.accept_payload) {
      await acceptSmartFormDraft(smartFormDraft.value)
      aiMessages.value.unshift('赤瞳：已采纳智能填表草稿，并写入表单记录。')
      await refreshWorkbenchSummary()
    } else {
      aiMessages.value.unshift(`赤瞳：已采纳 ${documentRevision.value.title} 的 AI 修改预览。`)
    }
    documentRevision.value = { ...documentRevision.value, status: 'accepted' }
  } catch (error) {
    aiMessages.value.unshift(`赤瞳：采纳失败：${error instanceof Error ? error.message : String(error)}`)
  }
}

function handleRejectDocumentRevision() {
  if (!documentRevision.value) return
  documentRevision.value = { ...documentRevision.value, status: 'rejected' }
  aiMessages.value.unshift(`赤瞳：已拒绝 ${documentRevision.value.title} 的 AI 修改预览。`)
}

function handleRegenerateDocumentRevision() {
  if (!documentRevision.value) return
  documentRevision.value = {
    ...documentRevision.value,
    status: 'draft',
    additions: documentRevision.value.additions + 1,
    lines: [
      ...documentRevision.value.lines,
      {
        id: `regen-${Date.now()}`,
        type: 'added',
        text: '重新生成版本将进一步压缩措辞，并保留人工确认入口。',
      },
    ],
  }
  aiMessages.value.unshift('赤瞳：已重新生成文档修改预览，请再次确认差异。')
}

async function openSmartFormRevision(templateId?: string) {
  workflowSteps.value = [
    { id: 'intent', label: '识别意图', status: 'done' },
    { id: 'tool', label: '生成文档 Diff', status: 'active' },
    { id: 'confirm', label: '等待采纳', status: 'pending' },
  ]

  try {
    const draft = await draftSmartForm({
      query: '临边 高处 整改 T006',
      templateId,
      sourceText: [
        '关于 B2 区临边防护隐患的整改通知',
        '现场有些护栏没弄好，需要尽快处理。',
        '后面安全员再看一下。',
      ].join('\n'),
      instruction: documentRevision.value?.instruction ?? '生成安全表格草稿，并保留人工采纳确认。',
    })
    smartFormDraft.value = draft
    if (draft.docx_draft?.output_path) {
      recordGeneratedOutput({ title: '智能填表 DOCX 草稿', kind: 'docx', path: draft.docx_draft.output_path })
    }
    if (draft.docx_draft?.payload_path) {
      recordGeneratedOutput({ title: '智能填表 payload', kind: 'payload', path: draft.docx_draft.payload_path })
    }
    if (draft.revision_preview) {
      documentRevision.value = draft.revision_preview
    }
    workflowSteps.value = [
      { id: 'intent', label: '识别意图', status: 'done' },
      { id: 'tool', label: '生成文档 Diff', status: 'done' },
      { id: 'confirm', label: '等待采纳', status: 'active' },
    ]
    aiMessages.value.unshift('赤瞳：已完成模板搜索、字段预填和 DOCX 草稿生成，点击采纳后才写入表单记录。')
  } catch (error) {
    smartFormDraft.value = null
    if (documentRevision.value) {
      documentRevision.value = { ...documentRevision.value, status: 'draft' }
    }
    workflowSteps.value = [
      { id: 'intent', label: '识别意图', status: 'done' },
      { id: 'tool', label: '生成文档 Diff', status: 'done' },
      { id: 'confirm', label: '等待采纳', status: 'active' },
    ]
    aiMessages.value.unshift(`赤瞳：智能填表接口暂不可用，已展示本地文档 diff 示例：${error instanceof Error ? error.message : String(error)}`)
  }
}

async function handleHybridCreatePlan(payload: {
  sessionId: string
  userInput: string
  preferCodex: boolean
  dryRun: boolean
  metadata: Record<string, unknown>
}) {
  try {
    const planned = await createHybridPlan({
      sessionId: payload.sessionId,
      userInput: payload.userInput,
      preferCodex: payload.preferCodex,
      metadata: payload.metadata,
    })
    hybridPanelRef.value?.syncPlan(planned.plan)
    hybridPanelRef.value?.pushLog(`计划创建成功：${planned.plan.plan_id} · ${planned.plan.status}`)
    aiMessages.value.unshift(`赤瞳：混合编排计划已创建 ${planned.plan.plan_id}，请先确认再执行。`)
    await createAuditEvent({
      eventType: 'frontend_hybrid_plan_created',
      sessionId: payload.sessionId,
      planId: planned.plan.plan_id,
      status: planned.plan.status,
      payload: { dry_run: payload.dryRun, action_count: planned.plan.actions.length },
    })
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    hybridPanelRef.value?.pushLog(`混合编排失败：${reason}`)
    aiMessages.value.unshift(`赤瞳：混合编排链路执行失败：${reason}`)
  }
}

async function handleHybridConfirmPlan(payload: { sessionId: string; planId: string; actionIds: string[]; notes?: string }) {
  try {
    const confirmed = await confirmHybridPlan({
      sessionId: payload.sessionId,
      planId: payload.planId,
      actionIds: payload.actionIds,
      confirmedBy: 'workbench_user',
      notes: payload.notes,
    })
    hybridPanelRef.value?.syncPlan(confirmed.plan)
    hybridPanelRef.value?.pushLog(`计划确认完成：${confirmed.plan.status} · actions=${payload.actionIds.length}`)
    aiMessages.value.unshift(`赤瞳：计划 ${payload.planId} 已确认，可执行。`)
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    hybridPanelRef.value?.pushLog(`确认失败：${reason}`)
    aiMessages.value.unshift(`赤瞳：计划确认失败：${reason}`)
  }
}

async function handleHybridExecutePlan(payload: { sessionId: string; planId: string; idempotencyKey: string; dryRun: boolean }) {
  try {
    const executed = await executeHybridPlan({
      sessionId: payload.sessionId,
      planId: payload.planId,
      idempotencyKey: payload.idempotencyKey,
      retryFailedOnly: true,
      dryRun: payload.dryRun,
    })
    hybridPanelRef.value?.syncPlan(executed.plan)
    hybridPanelRef.value?.pushLog(`执行完成：${executed.plan.status} · ok=${executed.ok}`)
    aiMessages.value.unshift(`赤瞳：混合编排执行完成，状态 ${executed.plan.status}。`)
    await createAuditEvent({
      eventType: 'frontend_hybrid_execute_finished',
      sessionId: payload.sessionId,
      planId: payload.planId,
      status: executed.plan.status,
      payload: { dry_run: payload.dryRun, action_count: executed.action_results.length, ok: executed.ok },
    })
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    hybridPanelRef.value?.pushLog(`执行失败：${reason}`)
    aiMessages.value.unshift(`赤瞳：计划执行失败：${reason}`)
  }
}
</script>

<template>
  <main class="workbench">
    <section class="hero-panel">
      <div>
        <p class="eyebrow">Chitung Workbench</p>
        <h1>赤瞳安全智能平台</h1>
        <p>用一个工作台连接隐患、视频、聊天、表格、外部风险和 AI 确认闭环。</p>
      </div>
      <div class="hero-panel__status">
        <span
          class="status-dot"
          :class="centerHealth ? 'status-dot--green' : 'status-dot--orange'"
        />
        {{ centerStatusText }}
        <small v-if="runtime">· {{ runtime.centerUrl }}</small>
      </div>
    </section>

    <CommandBar @submit="handleCommand" />

    <ActionReviewCards
      :cards="reviewCards"
      :busy="isCardActionBusy"
      @action="handleReviewCardAction"
    />

    <HybridOrchestrationPanel
      ref="hybridPanelRef"
      @save-llm="handleSaveLlmSettings"
      @create-plan="handleHybridCreatePlan"
      @confirm-plan="handleHybridConfirmPlan"
      @execute-plan="handleHybridExecutePlan"
    />

    <SystemSettingsPanel
      :health="centerHealth"
      :llm-settings="llmSettings"
      :connector-settings="connectorSettings"
      :runtime-status="runtimeStatus"
      :app-config="appConfig"
      :log-dir="runtime?.logDir"
      :is-saving="isSavingLlmSettings"
      :is-testing-llm="isTestingLlm"
      :is-saving-connectors="isSavingConnectors"
      :is-saving-config="isSavingAppConfig"
      :is-restarting-services="isRestartingServices"
      @save-llm="handleSaveLlmSettings"
      @test-llm="handleTestLlmSettings"
      @save-connectors="handleSaveConnectors"
      @save-config="handleSaveAppConfig"
      @open-log-dir="openServiceLogDir"
      @restart-services="restartDesktopServices"
      @refresh="refreshSystemStatus"
    />

    <StatusStrip :metrics="metrics" />

    <section class="workbench-grid">
      <CameraGrid
        :patrol-draft="visualPatrolDraft"
        :is-patrolling="isPatrolling"
        :cameras="appConfig?.cameras"
        @patrol="handleVisualPatrol"
        @confirm-candidate="handleConfirmVisualCandidate"
        @open-evidence="openLocalFile"
      />
      <ActiveHazards
        :hazards="hazards"
        @confirm="handleConfirmHazard"
        @workflow="handleCaseWorkflow"
      />
      <section class="panel">
        <div class="panel__header">
          <div>
            <h2>AI 执行进度</h2>
            <p>{{ isSending ? '正在等待中台响应' : '展示最近一次工具链状态' }}</p>
          </div>
        </div>
        <ProgressChain :steps="workflowSteps" />
        <div class="ai-message-list">
          <p v-for="msg in aiMessages.slice(0, 3)" :key="msg">{{ msg }}</p>
        </div>
      </section>
      <section class="panel">
        <div class="panel__header">
          <div>
            <h2>快捷工作流</h2>
            <p>竞赛演示优先闭环</p>
          </div>
        </div>
        <div class="workflow-shortcuts">
          <button>隐患录入</button>
          <button>视觉巡检</button>
          <button @click="openSmartFormRevision()">智能填表</button>
          <button @click="generateDailyBriefing">{{ isLoadingBriefing ? '生成中' : '每日简报' }}</button>
        </div>
      </section>
      <section class="panel report-generator-panel">
        <div class="panel__header">
          <div>
            <h2>报告生成</h2>
            <p>安全日报、整改报告、社区报告生成后可在最近文件打开</p>
          </div>
        </div>
        <div class="workflow-shortcuts">
          <button :disabled="isGeneratingReport" @click="handleGenerateReport('daily_safety')">安全日报</button>
          <button :disabled="isGeneratingReport" @click="handleGenerateReport('rectification')">整改报告</button>
          <button :disabled="isGeneratingReport" @click="handleGenerateReport('community')">社区报告 DOCX</button>
        </div>
      </section>
      <section v-if="externalRiskBriefing" class="panel external-risk-panel">
        <div class="panel__header">
          <div>
            <h2>{{ externalRiskBriefing.title }}</h2>
            <p>{{ externalRiskBriefing.summary }}</p>
          </div>
        </div>
        <ul class="external-risk-list">
          <li v-for="item in externalRiskBriefing.items" :key="item">{{ item }}</li>
        </ul>
      </section>
      <section v-if="notificationDraft" class="panel notification-draft-panel">
        <div class="panel__header">
          <div>
            <h2>整改通知确认卡</h2>
            <p>{{ notificationDraft.contractor }} · {{ notificationDraft.channel || notificationDraft.contact || '待补充联系方式' }}</p>
          </div>
          <span class="diff-status" :class="`diff-status--${notificationDraft.status === 'confirmed' ? 'accepted' : 'draft'}`">
            {{ notificationDraft.status === 'confirmed' ? '已确认' : '待人工确认' }}
          </span>
        </div>
        <pre class="notification-draft-text">{{ notificationDraft.draftText }}</pre>
        <div class="file-actions-bar">
          <button class="mini-button" @click="notificationDraft = null">取消</button>
          <button class="primary-soft-button" @click="confirmNotificationDraft">确认通知</button>
        </div>
      </section>
      <DocumentDiffPanel
        v-if="documentRevision"
        :revision="documentRevision"
        @accept="handleAcceptDocumentRevision"
        @reject="handleRejectDocumentRevision"
        @regenerate="handleRegenerateDocumentRevision"
      />
      <section class="panel smart-form-panel">
        <div class="panel__header">
          <div>
            <h2>智能填表草稿</h2>
            <p>模板搜索、字段预填、DOCX 草稿和人工采纳状态</p>
          </div>
        </div>
        <div v-if="smartFormDraft?.ok" class="smart-form-summary">
          <div>
            <span>选中模板</span>
            <strong>{{ smartFormDraft.selected_template?.id }} · {{ smartFormDraft.selected_template?.title }}</strong>
          </div>
          <div>
            <span>候选模板</span>
            <strong>{{ smartFormDraft.templates.length }} 个</strong>
          </div>
          <div>
            <span>预填字段</span>
            <strong>{{ Object.keys(smartFormDraft.prefill?.fields ?? {}).length }} 个</strong>
          </div>
          <div>
            <span>DOCX 草稿</span>
            <strong>{{ smartFormDraft.docx_draft?.output_path || '待生成' }}</strong>
          </div>
        </div>
        <div v-if="smartFormDraft?.ok" class="file-actions-bar">
          <button class="mini-button" @click="openLocalFile(smartFormOutputPath)">打开 DOCX</button>
          <button class="mini-button" @click="openLocalFile(smartFormPayloadPath)">打开 payload</button>
          <button class="mini-button" @click="showLocalFile(smartFormOutputPath || smartFormPayloadPath)">在文件夹中显示</button>
        </div>
        <p v-else class="smart-form-empty">
          点击“智能填表”后，中台会搜索模板、预填字段、生成 DOCX 草稿；正式记录只在采纳后写入。
        </p>
      </section>
      <section class="panel output-history-panel">
        <div class="panel__header">
          <div>
            <h2>最近生成文件</h2>
            <p>DOCX、payload、巡检截图、通知草稿可再次打开</p>
          </div>
        </div>
        <div class="output-history-list">
          <article v-for="item in generatedOutputs" :key="item.id" class="output-history-row">
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.path || item.content || '暂无路径' }}</p>
              <small>{{ item.kind }} · {{ item.createdAt }}</small>
            </div>
            <div class="output-history-actions">
              <button v-if="item.path" class="mini-button" @click="openLocalFile(item.path)">打开</button>
              <button v-if="item.path" class="mini-button" @click="showLocalFile(item.path)">定位</button>
            </div>
          </article>
          <p v-if="!generatedOutputs.length" class="smart-form-empty">暂无生成文件。生成表格、巡检或报告后会自动出现在这里。</p>
        </div>
      </section>
    </section>

    <ActivityFeed :items="activities" @open-confirmations="goToPendingConfirmations" />

    <HazardLedgerPanel
      :records="hazardRecords"
      :is-loading="isLoadingHazards"
      @refresh="refreshHazardRecords"
      @workflow="handleCaseWorkflow"
    />

    <FormTemplateBrowserPanel
      :templates="formTemplates"
      :is-loading="isSearchingTemplates"
      @search="handleSearchTemplates"
      @use-template="openSmartFormRevision"
    />
  </main>
</template>

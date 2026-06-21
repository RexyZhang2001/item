<script setup lang="ts">
import { onMounted, ref } from 'vue'
import SystemSettingsPanel from '../components/system/SystemSettingsPanel.vue'
import {
  getAppConfig,
  getConnectorSettings,
  getHealth,
  getLlmSettings,
  getRuntimeStatus,
  saveAppConfig,
  saveConnectorSettings,
  saveLlmSettings,
  testLlmSettings,
} from '../services/chitungApi'
import type { AppConfig, ConnectorSettingsStatus, LlmSettingsStatus, RuntimeStatus } from '../types/domain'

const centerHealth = ref<Record<string, unknown> | null>(null)
const llmSettings = ref<LlmSettingsStatus | null>(null)
const connectorSettings = ref<ConnectorSettingsStatus | null>(null)
const runtimeStatus = ref<RuntimeStatus | null>(null)
const appConfig = ref<AppConfig | null>(null)
const logDir = ref<string | null>(null)
const isSaving = ref(false)
const isTestingLlm = ref(false)
const isSavingConnectors = ref(false)
const isSavingConfig = ref(false)
const isRestartingServices = ref(false)

async function refreshSystemStatus() {
  try {
    centerHealth.value = await getHealth()
    llmSettings.value = await getLlmSettings()
    connectorSettings.value = await getConnectorSettings()
    runtimeStatus.value = await getRuntimeStatus()
    appConfig.value = await getAppConfig()
    if (window.chitungDesktop) {
      const runtime = await window.chitungDesktop.getRuntime()
      logDir.value = runtime.logDir || null
    }
  } catch {
    centerHealth.value = null
  }
}

async function handleSaveLlm(payload: { baseUrl: string; apiKey: string; model: string }) {
  isSaving.value = true
  try {
    const result = await saveLlmSettings(payload)
    llmSettings.value = result.status
  } finally {
    isSaving.value = false
  }
}

async function handleTestLlm() {
  isTestingLlm.value = true
  try {
    await testLlmSettings()
  } finally {
    isTestingLlm.value = false
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
  } finally {
    isSavingConnectors.value = false
  }
}

async function handleSaveAppConfig(payload: AppConfig) {
  isSavingConfig.value = true
  try {
    const result = await saveAppConfig(payload)
    appConfig.value = result.config
  } finally {
    isSavingConfig.value = false
  }
}

async function restartDesktopServices() {
  if (!window.chitungDesktop) return
  isRestartingServices.value = true
  try {
    const result = await window.chitungDesktop.restartServices()
    if (result.ok) await refreshSystemStatus()
  } finally {
    isRestartingServices.value = false
  }
}

function openLogDir() {
  if (logDir.value && window.chitungDesktop) {
    window.chitungDesktop.showInFolder(logDir.value)
  }
}

onMounted(refreshSystemStatus)
</script>

<template>
  <main class="workbench">
    <section class="hero-panel">
      <div>
        <p class="eyebrow">Chitung Center</p>
        <h1>系统设置</h1>
        <p>统一管理 LLM、中台、工具箱、连接器和项目配置。</p>
      </div>
    </section>

    <SystemSettingsPanel
      :health="centerHealth"
      :llm-settings="llmSettings"
      :connector-settings="connectorSettings"
      :runtime-status="runtimeStatus"
      :app-config="appConfig"
      :log-dir="logDir"
      :is-saving="isSaving"
      :is-testing-llm="isTestingLlm"
      :is-saving-connectors="isSavingConnectors"
      :is-saving-config="isSavingConfig"
      :is-restarting-services="isRestartingServices"
      @save-llm="handleSaveLlm"
      @test-llm="handleTestLlm"
      @save-connectors="handleSaveConnectors"
      @save-config="handleSaveAppConfig"
      @open-log-dir="openLogDir"
      @restart-services="restartDesktopServices"
      @refresh="refreshSystemStatus"
    />
  </main>
</template>

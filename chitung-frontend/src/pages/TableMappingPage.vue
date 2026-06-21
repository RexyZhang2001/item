<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  extractTableMappingFields,
  listTableMappingForms,
  runTableMappingFill,
} from '../services/chitungApi'
import type {
  TableMappingExtractResult,
  TableMappingForm,
  TableMappingRunResult,
} from '../types/domain'

type Step = 'idle' | 'loadingForms' | 'extracting' | 'extracted' | 'running' | 'completed' | 'error'

const step = ref<Step>('idle')
const forms = ref<TableMappingForm[]>([])
const filePath = ref('')
const selectedFormId = ref('')
const scriptAvailable = ref(false)
const scriptDir = ref('')
const extractResult = ref<TableMappingExtractResult | null>(null)
const runResult = ref<TableMappingRunResult | null>(null)
const fieldValues = ref<Record<string, string>>({})
const errorMsg = ref('')
const screenshot = ref(true)
const dryRun = ref(false)

const selectedForm = computed(() => forms.value.find((item) => item.id === selectedFormId.value) ?? null)

const groupedForms = computed(() => {
  const groups: Record<string, TableMappingForm[]> = {}
  for (const form of forms.value) {
    const key = form.category || '未分类'
    if (!groups[key]) groups[key] = []
    groups[key].push(form)
  }
  return groups
})

const editableFields = computed(() => selectedForm.value?.fields ?? [])
const matchedCount = computed(() => Object.values(fieldValues.value).filter((value) => value.trim()).length)
const canExtract = computed(() => Boolean(filePath.value.trim() && selectedFormId.value && step.value !== 'extracting'))
const canRun = computed(() => Boolean(canExtract.value && matchedCount.value > 0 && step.value !== 'running'))

onMounted(loadForms)

async function loadForms() {
  step.value = 'loadingForms'
  errorMsg.value = ''
  try {
    const result = await listTableMappingForms()
    forms.value = result.items
    scriptAvailable.value = result.scriptAvailable
    scriptDir.value = result.scriptDir
    if (!selectedFormId.value && result.items.length) {
      selectedFormId.value = result.items[0].id
    }
    seedFields()
    step.value = 'idle'
  } catch (error) {
    errorMsg.value = error instanceof Error ? error.message : '加载表单清单失败'
    step.value = 'error'
  }
}

function seedFields() {
  const next: Record<string, string> = {}
  for (const field of editableFields.value) {
    next[field.name] = fieldValues.value[field.name] ?? ''
  }
  fieldValues.value = next
}

function handleFormChange() {
  extractResult.value = null
  runResult.value = null
  seedFields()
}

async function handleExtract() {
  if (!canExtract.value) return
  step.value = 'extracting'
  errorMsg.value = ''
  runResult.value = null
  try {
    const result = await extractTableMappingFields({
      filePath: filePath.value.trim(),
      formId: selectedFormId.value,
    })
    extractResult.value = result
    const next: Record<string, string> = {}
    for (const field of result.form.fields) {
      next[field.name] = result.fields[field.name]?.value ?? ''
    }
    fieldValues.value = next
    step.value = 'extracted'
  } catch (error) {
    errorMsg.value = error instanceof Error ? error.message : '字段抽取失败'
    step.value = 'error'
  }
}

async function handleRun() {
  if (!canRun.value) return
  step.value = 'running'
  errorMsg.value = ''
  runResult.value = null
  try {
    const result = await runTableMappingFill({
      filePath: filePath.value.trim(),
      formId: selectedFormId.value,
      fields: fieldValues.value,
      action: 'draft',
      screenshot: screenshot.value,
      dryRun: dryRun.value,
    })
    runResult.value = result
    step.value = result.ok ? 'completed' : 'error'
    if (!result.ok) {
      errorMsg.value = `脚本执行失败，退出码 ${result.exit_code ?? 'unknown'}`
    }
  } catch (error) {
    errorMsg.value = error instanceof Error ? error.message : '保存草稿失败'
    step.value = 'error'
  }
}

function fillSample() {
  if (!selectedForm.value) return
  for (const field of selectedForm.value.fields.slice(0, 6)) {
    if (!fieldValues.value[field.name]) {
      fieldValues.value[field.name] = field.name.includes('日期') ? new Date().toISOString().slice(0, 10) : '测试值'
    }
  }
}
</script>

<template>
  <div class="table-mapping-page">
    <section class="mapping-card mapping-card--setup">
      <div class="mapping-card__header">
        <div>
          <p class="eyebrow">闪闪文档 · 表格映射</p>
          <h2>C-SMART 自动填表</h2>
        </div>
        <span class="status-pill" :class="{ 'status-pill--ok': scriptAvailable }">
          {{ scriptAvailable ? '脚本已连接' : '脚本未找到' }}
        </span>
      </div>

      <label class="field">
        <span>DOCX 文档路径</span>
        <input
          v-model="filePath"
          class="input"
          type="text"
          placeholder="E:\path\to\source.docx"
        />
      </label>

      <label class="field">
        <span>目标表单</span>
        <select v-model="selectedFormId" class="input" @change="handleFormChange">
          <optgroup v-for="(items, category) in groupedForms" :key="category" :label="category">
            <option v-for="form in items" :key="form.id" :value="form.id">
              {{ form.id }} · {{ form.name }}
            </option>
          </optgroup>
        </select>
      </label>

      <div v-if="selectedForm" class="form-summary">
        <strong>{{ selectedForm.name }}</strong>
        <span>{{ selectedForm.category || '未分类' }} · {{ selectedForm.fields.length }} 个字段</span>
      </div>

      <div class="actions">
        <button class="btn btn--primary" :disabled="!canExtract" @click="handleExtract">
          {{ step === 'extracting' ? '抽取中...' : '从文档抽取字段' }}
        </button>
        <button class="btn" :disabled="!selectedForm" @click="fillSample">填入测试值</button>
      </div>

      <div class="options">
        <label><input v-model="screenshot" type="checkbox" /> 保存执行截图</label>
        <label><input v-model="dryRun" type="checkbox" /> 只预览，不真正填表</label>
      </div>

      <p class="hint">
        脚本目录：{{ scriptDir || '未配置' }}
      </p>
    </section>

    <section class="mapping-card mapping-card--fields">
      <div class="mapping-card__header">
        <div>
          <p class="eyebrow">字段确认</p>
          <h2>文档字段 → 系统字段</h2>
        </div>
        <span class="counter">{{ matchedCount }}/{{ editableFields.length }}</span>
      </div>

      <div v-if="!selectedForm" class="empty-state">正在加载表单...</div>
      <div v-else class="field-list">
        <label v-for="field in editableFields" :key="field.name" class="mapping-row">
          <span class="mapping-row__name">{{ field.name }}</span>
          <input v-model="fieldValues[field.name]" class="input" type="text" placeholder="未抽取到，可手动填写" />
          <span class="mapping-row__source">
            {{ extractResult?.fields[field.name]?.source || 'manual' }}
          </span>
        </label>
      </div>
    </section>

    <section class="mapping-card mapping-card--run">
      <div class="mapping-card__header">
        <div>
          <p class="eyebrow">执行</p>
          <h2>保存到系统草稿</h2>
        </div>
      </div>

      <button class="btn btn--accent" :disabled="!canRun" @click="handleRun">
        {{ step === 'running' ? '正在打开系统并保存...' : dryRun ? '预览执行命令' : '保存到系统草稿' }}
      </button>

      <div v-if="extractResult?.document_preview" class="preview-box">
        <strong>文档预览</strong>
        <p>{{ extractResult.document_preview }}</p>
      </div>

      <div v-if="runResult" class="result-box" :class="{ 'result-box--ok': runResult.ok }">
        <strong>{{ runResult.ok ? '执行成功' : '执行失败' }}</strong>
        <p>Job: {{ runResult.job_id }}</p>
        <p v-if="runResult.duration_ms">耗时：{{ Math.round(runResult.duration_ms / 1000) }} 秒</p>
        <p>命令：{{ runResult.command.join(' ') }}</p>
      </div>

      <pre v-if="runResult?.stdout" class="log-box">{{ runResult.stdout }}</pre>
      <pre v-if="runResult?.stderr" class="log-box log-box--error">{{ runResult.stderr }}</pre>

      <div v-if="errorMsg" class="error-card">{{ errorMsg }}</div>
    </section>
  </div>
</template>

<style scoped>
.table-mapping-page {
  background: #0f1117;
  color: #d6deeb;
  display: grid;
  gap: 14px;
  grid-template-columns: 300px minmax(360px, 1fr) 360px;
  height: 100%;
  overflow: hidden;
  padding: 16px;
}

.mapping-card {
  background: #171b22;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px;
}

.mapping-card__header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.mapping-card__header h2 {
  color: #f8fafc;
  font-size: 18px;
  margin: 2px 0 0;
}

.eyebrow {
  color: #60a5fa;
  font-size: 12px;
  letter-spacing: 0.08em;
  margin: 0;
  text-transform: uppercase;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 14px;
}

.field span,
.hint,
.mapping-row__source {
  color: #8b949e;
  font-size: 12px;
}

.input {
  background: #0f131a;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 8px;
  color: #e5e7eb;
  min-height: 36px;
  padding: 8px 10px;
}

.input:focus {
  border-color: #60a5fa;
  outline: none;
}

.form-summary,
.preview-box,
.result-box,
.error-card {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 14px;
  padding: 12px;
}

.form-summary span,
.preview-box p,
.result-box p {
  color: #94a3b8;
  font-size: 12px;
  margin: 0;
}

.actions,
.options {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.options {
  color: #94a3b8;
  flex-direction: column;
  font-size: 12px;
}

.btn {
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 8px;
  color: #dbeafe;
  cursor: pointer;
  padding: 9px 12px;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.btn--primary {
  background: rgba(37, 99, 235, 0.85);
  border-color: rgba(96, 165, 250, 0.45);
}

.btn--accent {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  border: 0;
  font-weight: 700;
  width: 100%;
}

.status-pill,
.counter {
  border: 1px solid rgba(248, 113, 113, 0.4);
  border-radius: 999px;
  color: #fca5a5;
  font-size: 12px;
  padding: 4px 8px;
  white-space: nowrap;
}

.status-pill--ok {
  border-color: rgba(34, 197, 94, 0.4);
  color: #86efac;
}

.counter {
  border-color: rgba(96, 165, 250, 0.38);
  color: #93c5fd;
}

.field-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.mapping-row {
  align-items: center;
  display: grid;
  gap: 8px;
  grid-template-columns: 130px minmax(160px, 1fr) 58px;
}

.mapping-row__name {
  color: #cbd5e1;
  font-size: 13px;
}

.preview-box {
  margin-top: 14px;
}

.preview-box p {
  line-height: 1.6;
  max-height: 160px;
  overflow: auto;
}

.result-box--ok {
  border: 1px solid rgba(34, 197, 94, 0.35);
}

.log-box {
  background: #090b10;
  border-radius: 10px;
  color: #cbd5e1;
  flex: 1;
  font-size: 12px;
  line-height: 1.5;
  min-height: 0;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
}

.log-box--error,
.error-card {
  color: #fca5a5;
}

.empty-state {
  color: #64748b;
  margin: auto;
}
</style>

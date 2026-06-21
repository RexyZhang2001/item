<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  deleteWorkflow,
  getWorkflowDetail,
  getWorkflows,
  importWorkflow,
  runWorkflowTemplate,
  toggleWorkflow,
} from '../services/chitungApi'
import type { WorkflowDetail, WorkflowInfo } from '../types/domain'

const workflows = ref<WorkflowInfo[]>([])
const loading = ref(false)
const runningName = ref('')
const result = ref<Record<string, unknown> | null>(null)
const selected = ref<WorkflowDetail | null>(null)
const error = ref('')
const importName = ref('')
const importContent = ref('')

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    workflows.value = await getWorkflows()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

async function runWorkflow(workflow: WorkflowInfo) {
  runningName.value = workflow.name
  result.value = null
  error.value = ''
  try {
    result.value = await runWorkflowTemplate({
      workflowName: workflow.name,
      message: `运行工作流：${workflow.name}`,
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    runningName.value = ''
  }
}

async function openWorkflow(name: string) {
  try {
    selected.value = await getWorkflowDetail(name)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleToggle(workflow: WorkflowInfo) {
  try {
    await toggleWorkflow(workflow.name, !workflow.enabled)
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleImport() {
  try {
    await importWorkflow(importName.value, importContent.value)
    importName.value = ''
    importContent.value = ''
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleDelete(workflow: WorkflowInfo) {
  try {
    await deleteWorkflow(workflow.name)
    if (selected.value?.name === workflow.name) selected.value = null
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

onMounted(refresh)
</script>

<template>
  <main class="workbench">
    <section class="hero-panel">
      <div>
        <p class="eyebrow">Workflow Library</p>
        <h1>Workflow 工作流</h1>
        <p>管理中台 Workflow：列表、详情、启停、导入、外部项删除，并可运行已注册模板。</p>
      </div>
      <button class="primary-soft-button" :disabled="loading" @click="refresh">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2>已注册工作流</h2>
          <p>{{ workflows.length }} 个模板</p>
        </div>
      </div>
      <p v-if="error" class="workflow-error">{{ error }}</p>
      <div class="workflow-grid">
        <article v-for="workflow in workflows" :key="workflow.name" class="workflow-card">
          <div>
            <strong>{{ workflow.name }}</strong>
            <p>{{ workflow.summary }}</p>
            <small>{{ workflow.name }} · {{ workflow.category }} · {{ workflow.steps?.length ?? 0 }} 步</small>
          </div>
          <div class="workflow-actions">
            <button class="mini-button" @click="openWorkflow(workflow.name)">详情</button>
            <button class="mini-button" @click="handleToggle(workflow)">
              {{ workflow.enabled === false ? '启用' : '禁用' }}
            </button>
            <button class="mini-button" :disabled="!!runningName || !workflow.name.startsWith('workflow_')" @click="runWorkflow(workflow)">
              {{ runningName === workflow.name ? '运行中...' : '运行' }}
            </button>
            <button class="mini-button" :disabled="workflow.category !== 'external'" @click="handleDelete(workflow)">删除</button>
          </div>
        </article>
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2>导入外部 Workflow</h2>
          <p>会写入 `workflows/{name}/WORKFLOW.md`，category 标记为 external。</p>
        </div>
      </div>
      <div class="workflow-import">
        <input v-model="importName" placeholder="workflow-name" />
        <textarea v-model="importContent" rows="8" placeholder="# Workflow Name&#10;&#10;Workflow content..." />
        <button class="primary-soft-button" :disabled="!importName.trim() || !importContent.trim()" @click="handleImport">
          导入 Workflow
        </button>
      </div>
    </section>

    <section v-if="result" class="panel">
      <div class="panel__header">
        <div>
          <h2>运行结果</h2>
          <p>来自 `/api/workflows/run`</p>
        </div>
        <button class="mini-button" @click="result = null">关闭</button>
      </div>
      <pre class="workflow-result">{{ JSON.stringify(result, null, 2) }}</pre>
    </section>

    <section v-if="selected" class="panel">
      <div class="panel__header">
        <div>
          <h2>{{ selected.name }}</h2>
          <p>WORKFLOW.md 详情</p>
        </div>
        <button class="mini-button" @click="selected = null">关闭</button>
      </div>
      <pre class="workflow-result">{{ selected.content }}</pre>
    </section>
  </main>
</template>

<style scoped>
.workflow-error {
  color: var(--color-error);
  margin-bottom: 12px;
}

.workflow-grid {
  display: grid;
  gap: 12px;
}

.workflow-card {
  align-items: center;
  border: 1px solid var(--border-light);
  border-left: 4px solid var(--brand-cyan);
  border-radius: 10px;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 14px;
}

.workflow-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.workflow-import {
  display: grid;
  gap: 10px;
}

.workflow-import input,
.workflow-import textarea {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 10px;
}

.workflow-card p {
  color: var(--text-secondary);
  margin: 6px 0;
}

.workflow-card small {
  color: var(--text-muted);
}

.workflow-result {
  background: #0f172a;
  border-radius: 10px;
  color: #dbeafe;
  max-height: 420px;
  overflow: auto;
  padding: 16px;
}
</style>

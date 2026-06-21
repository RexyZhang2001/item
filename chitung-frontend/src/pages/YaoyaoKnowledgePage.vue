<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  deleteRagDocument,
  getRagStats,
  listRagDocuments,
  queryRag,
  uploadRagDocument,
} from '../services/chitungApi'
import type { RagDocument, RagQueryMatch, RagStats } from '../types/domain'

const documents = ref<RagDocument[]>([])
const results = ref<RagQueryMatch[]>([])
const stats = ref<RagStats | null>(null)
const queryText = ref('')
const isDragging = ref(false)
const isUploading = ref(false)
const isSearching = ref(false)
const deletingId = ref('')
const error = ref('')
const lastMessage = ref('')

const isFeedMode = computed(() => location.hash.includes('/feed'))
const mode = computed(() => (isFeedMode.value ? '舆情规范知识库' : 'RAG 知识库'))

async function refresh() {
  error.value = ''
  try {
    const [docItems, statResult] = await Promise.all([listRagDocuments(), getRagStats()])
    documents.value = docItems
    stats.value = statResult
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function uploadFiles(files: FileList | File[]) {
  const accepted = Array.from(files).filter((file) => /\.(pdf|docx|txt|md|markdown|html?)$/i.test(file.name))
  if (!accepted.length) {
    error.value = '请选择 PDF、Word、TXT、Markdown 或 HTML 文件。'
    return
  }
  isUploading.value = true
  error.value = ''
  lastMessage.value = ''
  try {
    let totalChunks = 0
    for (const file of accepted) {
      const result = await uploadRagDocument(file, isFeedMode.value ? 'feed' : 'default')
      totalChunks += result.chunk_count
    }
    lastMessage.value = `已上传 ${accepted.length} 个文件，新增 ${totalChunks} 个分块。`
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    isUploading.value = false
    isDragging.value = false
  }
}

async function handleInput(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) await uploadFiles(input.files)
  input.value = ''
}

async function handleDrop(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer?.files) await uploadFiles(event.dataTransfer.files)
}

async function removeDocument(docId: string) {
  deletingId.value = docId
  error.value = ''
  try {
    await deleteRagDocument(docId)
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    deletingId.value = ''
  }
}

async function search() {
  const value = queryText.value.trim()
  if (!value || isSearching.value) return
  isSearching.value = true
  error.value = ''
  results.value = []
  try {
    results.value = await queryRag({
      query: value,
      topK: 5,
      collection: isFeedMode.value ? 'feed' : undefined,
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    isSearching.value = false
  }
}

function formatDate(value: string) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

onMounted(refresh)
</script>

<template>
  <main class="workbench">
    <section class="hero-panel">
      <div>
        <p class="eyebrow">Yaoyao Knowledge</p>
        <h1>{{ mode }}</h1>
        <p>上传制度、规范、报告或外部风险资料，使用本地 ChromaDB 做语义检索。</p>
      </div>
      <button class="primary-soft-button" @click="refresh">刷新</button>
    </section>

    <section class="rag-stats">
      <article class="status-card status-card--blue">
        <span>文档数</span>
        <strong>{{ stats?.document_count ?? 0 }}</strong>
        <small>已入库文件</small>
      </article>
      <article class="status-card status-card--green">
        <span>分块数</span>
        <strong>{{ stats?.chunk_count ?? 0 }}</strong>
        <small>可检索文本片段</small>
      </article>
      <article class="status-card status-card--orange">
        <span>向量数</span>
        <strong>{{ stats?.vector_count ?? 0 }}</strong>
        <small>ChromaDB 本地向量</small>
      </article>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2>上传资料</h2>
          <p>支持 PDF、Word、TXT、Markdown、HTML。上传后自动解析、分块和向量化。</p>
        </div>
      </div>
      <label
        class="rag-dropzone"
        :class="{ 'rag-dropzone--active': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop="handleDrop"
      >
        <input type="file" multiple accept=".pdf,.docx,.txt,.md,.markdown,.html,.htm" @change="handleInput" />
        <span>{{ isUploading ? '正在上传并向量化...' : '拖拽文件到这里，或点击选择文件' }}</span>
      </label>
      <p v-if="lastMessage" class="rag-success">{{ lastMessage }}</p>
      <p v-if="error" class="knowledge-error">{{ error }}</p>
    </section>

    <section class="workbench-grid">
      <section class="panel">
        <div class="panel__header">
          <div>
            <h2>已上传文档</h2>
            <p>{{ documents.length }} 个文件</p>
          </div>
        </div>
        <div class="rag-document-list">
          <article v-for="doc in documents" :key="doc.doc_id" class="rag-document-row">
            <div>
              <strong>{{ doc.file_name }}</strong>
              <p>{{ doc.file_type }} · {{ doc.chunk_count }} 个分块 · {{ formatDate(doc.created_at) }}</p>
            </div>
            <button class="mini-button" :disabled="deletingId === doc.doc_id" @click="removeDocument(doc.doc_id)">
              {{ deletingId === doc.doc_id ? '删除中...' : '删除' }}
            </button>
          </article>
          <p v-if="!documents.length" class="smart-form-empty">暂无文档。上传制度文件后会显示在这里。</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel__header">
          <div>
            <h2>语义检索</h2>
            <p>返回最相关的文本片段和来源文件。</p>
          </div>
        </div>
        <div class="knowledge-box">
          <textarea
            v-model="queryText"
            rows="4"
            placeholder="例如：临边作业护栏高度和整改闭环要求是什么？"
            @keydown.ctrl.enter="search"
          />
          <button class="primary-soft-button" :disabled="isSearching || !queryText.trim()" @click="search">
            {{ isSearching ? '检索中...' : '检索' }}
          </button>
        </div>
        <div class="rag-results">
          <article v-for="(item, index) in results" :key="`${item.doc_id}-${item.chunk_index}-${index}`" class="rag-result-card">
            <div class="rag-result-card__meta">
              <strong>{{ item.source_file_name || '未知来源' }}</strong>
              <span>chunk {{ item.chunk_index }}</span>
            </div>
            <p>{{ item.text }}</p>
          </article>
          <p v-if="!results.length && queryText" class="smart-form-empty">暂无结果。</p>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.rag-stats {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 16px;
}

.rag-dropzone {
  align-items: center;
  background: linear-gradient(135deg, #111827, #1f2937);
  border: 1px dashed rgba(96, 165, 250, 0.5);
  border-radius: 14px;
  color: #dbeafe;
  display: flex;
  justify-content: center;
  min-height: 150px;
  padding: 24px;
  text-align: center;
}

.rag-dropzone input {
  display: none;
}

.rag-dropzone--active {
  border-color: #60a5fa;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.15);
}

.rag-success {
  color: var(--color-success);
  margin-top: 10px;
}

.knowledge-box {
  display: grid;
  gap: 10px;
}

.knowledge-box textarea {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 12px;
  resize: vertical;
}

.rag-document-list,
.rag-results {
  display: grid;
  gap: 10px;
}

.rag-document-row,
.rag-result-card {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 12px;
}

.rag-document-row {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.rag-document-row p {
  color: var(--text-secondary);
}

.rag-result-card {
  background: var(--bg-subtle);
}

.rag-result-card__meta {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.rag-result-card__meta span {
  color: var(--text-muted);
  font-size: 12px;
}

.knowledge-error {
  color: var(--color-error);
  margin-top: 12px;
}

@media (max-width: 900px) {
  .rag-stats {
    grid-template-columns: 1fr;
  }
}
</style>

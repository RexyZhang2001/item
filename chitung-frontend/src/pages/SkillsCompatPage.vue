<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { deleteSkill, getSkillDetail, getSkills, importSkill, toggleSkill } from '../services/chitungApi'
import type { SkillDetail, SkillInfo } from '../types/domain'

const skills = ref<SkillInfo[]>([])
const selected = ref<SkillDetail | null>(null)
const loading = ref(false)
const query = ref('')
const error = ref('')
const importName = ref('')
const importContent = ref('')

const filteredSkills = computed(() => {
  const value = query.value.trim().toLowerCase()
  if (!value) return skills.value
  return skills.value.filter((skill) => {
    return skill.name.toLowerCase().includes(value) || skill.summary.toLowerCase().includes(value)
  })
})

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    skills.value = await getSkills()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

async function openSkill(name: string) {
  try {
    selected.value = await getSkillDetail(name)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleToggle(skill: SkillInfo) {
  try {
    await toggleSkill(skill.name, !skill.enabled)
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleImport() {
  try {
    await importSkill(importName.value, importContent.value)
    importName.value = ''
    importContent.value = ''
    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function handleDelete(skill: SkillInfo) {
  try {
    await deleteSkill(skill.name)
    if (selected.value?.name === skill.name) selected.value = null
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
        <p class="eyebrow">Skill Market</p>
        <h1>Skill 技能</h1>
        <p>管理中台 Skill.md：列表、详情、启停、导入和外部 Skill 删除。</p>
      </div>
      <button class="primary-soft-button" :disabled="loading" @click="refresh">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2>已接入技能</h2>
          <p>{{ filteredSkills.length }} / {{ skills.length }} 个 Skill.md</p>
        </div>
        <input v-model="query" class="compat-search" placeholder="搜索技能名称或摘要" />
      </div>
      <p v-if="error" class="compat-error">{{ error }}</p>
      <div class="compat-card-grid">
        <article v-for="skill in filteredSkills" :key="skill.name" class="compat-card">
          <strong @click="openSkill(skill.name)">{{ skill.name }}</strong>
          <p>{{ skill.summary }}</p>
          <div class="compat-actions">
            <button class="mini-button" @click="openSkill(skill.name)">详情</button>
            <button class="mini-button" @click="handleToggle(skill)">
              {{ skill.enabled === false ? '启用' : '禁用' }}
            </button>
            <button
              class="mini-button"
              :disabled="skill.category !== 'external'"
              @click="handleDelete(skill)"
            >
              删除
            </button>
          </div>
          <small>{{ skill.path }}</small>
        </article>
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <div>
          <h2>导入外部 Skill</h2>
          <p>会写入 `skills/{name}/SKILL.md`，category 标记为 external。</p>
        </div>
      </div>
      <div class="compat-import">
        <input v-model="importName" placeholder="skill-name" />
        <textarea v-model="importContent" rows="8" placeholder="# Skill Name&#10;&#10;Skill content..." />
        <button class="primary-soft-button" :disabled="!importName.trim() || !importContent.trim()" @click="handleImport">
          导入 Skill
        </button>
      </div>
    </section>

    <section v-if="selected" class="panel">
      <div class="panel__header">
        <div>
          <h2>{{ selected.name }}</h2>
          <p>SKILL.md 详情</p>
        </div>
        <button class="mini-button" @click="selected = null">关闭</button>
      </div>
      <pre class="compat-markdown">{{ selected.content }}</pre>
    </section>
  </main>
</template>

<style scoped>
.compat-search {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  min-width: 240px;
  padding: 8px 10px;
}

.compat-error {
  color: var(--color-error);
  margin-bottom: 12px;
}

.compat-card-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}

.compat-card {
  border: 1px solid var(--border-light);
  border-left: 4px solid var(--brand-green);
  border-radius: 10px;
  cursor: pointer;
  padding: 14px;
}

.compat-actions {
  display: flex;
  gap: 8px;
  margin: 10px 0;
}

.compat-import {
  display: grid;
  gap: 10px;
}

.compat-import input,
.compat-import textarea {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 10px;
}

.compat-card:hover {
  box-shadow: var(--shadow-md);
}

.compat-card p {
  color: var(--text-secondary);
  margin: 6px 0;
}

.compat-card small {
  color: var(--text-muted);
  word-break: break-all;
}

.compat-markdown {
  background: #0f172a;
  border-radius: 10px;
  color: #dbeafe;
  max-height: 520px;
  overflow: auto;
  padding: 16px;
  white-space: pre-wrap;
}
</style>

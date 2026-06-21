<script setup lang="ts">
defineProps<{
  activePanel: string
}>()

const emit = defineEmits<{
  select: [panel: string]
}>()

const panels = [
  { id: 'guardian', icon: '🛡️', label: '望风险' },
  { id: 'docmate', icon: '📄', label: '书文稿' },
  { id: 'lingxun', icon: '💬', label: '闻动态' },
  { id: 'center', icon: '🧩', label: '统全局' },
  { id: 'yaoyao', icon: '📚', label: '问制度' },
]
</script>

<template>
  <div class="activity-bar">
    <div class="activity-bar__top">
      <button
        v-for="panel in panels"
        :key="panel.id"
        class="activity-bar__item"
        :class="{ 'activity-bar__item--active': activePanel === panel.id }"
        :title="panel.label"
        @click="emit('select', panel.id)"
      >
        <span class="activity-bar__emoji">{{ panel.icon }}</span>
      </button>
    </div>
    <div class="activity-bar__bottom">
      <button class="activity-bar__item" title="AI 助手" @click="emit('select', 'chatbot')">
        <span class="activity-bar__emoji">🤖</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.activity-bar {
  align-items: center;
  background: #16181d;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 100%;
  justify-content: space-between;
  padding: 8px 0;
  width: 48px;
}

.activity-bar__top,
.activity-bar__bottom {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-bar__item {
  align-items: center;
  background: transparent;
  border: 0;
  color: #8b949e;
  display: flex;
  height: 48px;
  justify-content: center;
  position: relative;
  transition: color 0.15s, background 0.15s;
  width: 48px;
}

.activity-bar__item:hover,
.activity-bar__item--active {
  color: #e2e8f0;
}

.activity-bar__item--active::before {
  background: #60a5fa;
  border-radius: 0 2px 2px 0;
  bottom: 8px;
  content: '';
  left: 0;
  position: absolute;
  top: 8px;
  width: 2px;
}

.activity-bar__emoji {
  font-size: 20px;
  opacity: 0.78;
  transition: opacity 0.15s, transform 0.15s;
}

.activity-bar__item:hover .activity-bar__emoji,
.activity-bar__item--active .activity-bar__emoji {
  opacity: 1;
  transform: scale(1.08);
}
</style>

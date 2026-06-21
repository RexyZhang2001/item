<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { sendChatMessage } from '../../services/chitungApi'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    content: '你好，我是赤瞳 AI 助手。可以帮你处理隐患、巡检、填表、制度查询和工作流编排。',
  },
])
const inputText = ref('')
const isTyping = ref(false)
const messagesEl = ref<HTMLElement | null>(null)
let nextId = 2

const quickActions = [
  { label: '隐患排查', prompt: '帮我分析最近的安全隐患' },
  { label: '生成通知', prompt: '生成一份高处作业安全隐患整改通知' },
  { label: '每日简报', prompt: '生成今日外部风险简报' },
  { label: '制度查询', prompt: '查询临边作业安全管理要求' },
]

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return
  messages.value.push({ id: nextId++, role: 'user', content: text })
  inputText.value = ''
  isTyping.value = true
  scrollToBottom()
  try {
    const response = await sendChatMessage({ message: text, channel: 'local_chat' })
    messages.value.push({ id: nextId++, role: 'assistant', content: response.message })
  } catch (error) {
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: `请求失败：${error instanceof Error ? error.message : String(error)}`,
    })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

function handleQuickAction(prompt: string) {
  inputText.value = prompt
  sendMessage()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <aside class="chatbot-panel" :class="{ 'chatbot-panel--hidden': !visible }">
    <div class="chatbot-panel__header">
      <div>
        <strong>赤瞳 AI</strong>
        <span>中台编排助手</span>
      </div>
      <button class="chatbot-panel__close" title="关闭" @click="emit('toggle')">×</button>
    </div>
    <div ref="messagesEl" class="chatbot-panel__messages">
      <article
        v-for="message in messages"
        :key="message.id"
        class="chatbot-message"
        :class="`chatbot-message--${message.role}`"
      >
        {{ message.content }}
      </article>
      <article v-if="isTyping" class="chatbot-message chatbot-message--assistant">正在处理中...</article>
    </div>
    <div class="chatbot-panel__quick">
      <button v-for="action in quickActions" :key="action.label" @click="handleQuickAction(action.prompt)">
        {{ action.label }}
      </button>
    </div>
    <div class="chatbot-panel__input-area">
      <textarea
        v-model="inputText"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
        rows="2"
        @keydown="handleKeydown"
      />
      <button :disabled="!inputText.trim() || isTyping" @click="sendMessage">发送</button>
    </div>
  </aside>
</template>

<style scoped>
.chatbot-panel {
  background: #1a1d23;
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  color: #c9d1d9;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  transition: width 0.2s ease, opacity 0.2s ease;
  width: 360px;
}

.chatbot-panel--hidden {
  border-left: 0;
  opacity: 0;
  width: 0;
}

.chatbot-panel__header {
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  min-width: 360px;
  padding: 12px 14px;
}

.chatbot-panel__header span {
  color: #6b7280;
  display: block;
  font-size: 11px;
}

.chatbot-panel__close {
  background: transparent;
  border: 0;
  color: #8b949e;
  font-size: 22px;
}

.chatbot-panel__messages {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
  min-width: 360px;
  overflow-y: auto;
  padding: 12px;
}

.chatbot-message {
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.55;
  max-width: 88%;
  padding: 9px 11px;
  white-space: pre-wrap;
}

.chatbot-message--assistant {
  background: rgba(255, 255, 255, 0.05);
}

.chatbot-message--user {
  align-self: flex-end;
  background: rgba(59, 130, 246, 0.16);
  color: #93c5fd;
}

.chatbot-panel__quick {
  display: flex;
  gap: 6px;
  min-width: 360px;
  overflow-x: auto;
  padding: 8px 12px;
}

.chatbot-panel__quick button {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  color: #8b949e;
  padding: 5px 10px;
  white-space: nowrap;
}

.chatbot-panel__input-area {
  align-items: flex-end;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  gap: 8px;
  min-width: 360px;
  padding: 10px 12px;
}

.chatbot-panel__input-area textarea {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #c9d1d9;
  flex: 1;
  outline: none;
  padding: 8px 10px;
  resize: none;
}

.chatbot-panel__input-area button {
  background: #3b82f6;
  border: 0;
  border-radius: 8px;
  color: white;
  padding: 8px 12px;
}

.chatbot-panel__input-area button:disabled {
  cursor: not-allowed;
  opacity: 0.35;
}
</style>

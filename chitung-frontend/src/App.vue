<script setup lang="ts">
import { provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ActivityBar from './components/layout/ActivityBar.vue'
import ChatbotPanel from './components/layout/ChatbotPanel.vue'
import PanelSidebar from './components/layout/PanelSidebar.vue'
import TopBar from './components/layout/TopBar.vue'
import { confirmationsRefreshKey, navigateKey, type AppPage } from './composables/useAppNavigation'

const route = useRoute()
const router = useRouter()

function deducePanel(path: string): string {
  if (path.startsWith('/guardian')) return 'guardian'
  if (path.startsWith('/docmate')) return 'docmate'
  if (path.startsWith('/lingxun')) return 'lingxun'
  if (path.startsWith('/center')) return 'center'
  if (path.startsWith('/yaoyao')) return 'yaoyao'
  return 'guardian'
}

const activePanel = ref(deducePanel(route.path))
const chatbotVisible = ref(false)
const confirmationsRefreshTick = ref(0)

const firstPaths: Record<string, string> = {
  guardian: '/guardian/dashboard',
  docmate: '/docmate/documents',
  lingxun: '/lingxun/whatsapp',
  center: '/center/settings',
  yaoyao: '/yaoyao/structured',
}

watch(
  () => route.path,
  (path) => {
    activePanel.value = deducePanel(path)
  },
)

function handlePanelSelect(panel: string) {
  if (panel === 'chatbot') {
    chatbotVisible.value = !chatbotVisible.value
    return
  }
  activePanel.value = panel
  router.push(firstPaths[panel] || firstPaths.guardian)
}

function handleLegacyNavigate(page: AppPage) {
  const routes: Record<AppPage, string> = {
    workbench: '/guardian/dashboard',
    'pending-confirmations': '/guardian/confirmations',
    'hazard-ledger': '/guardian/hazards',
    'visual-patrol': '/guardian/patrol',
    'smart-form': '/docmate/forms',
    'shanshan-doc': '/docmate/documents',
    'yaoyao-structured-input': '/yaoyao/structured',
  }
  router.push(routes[page] || firstPaths.guardian)
}

provide(navigateKey, handleLegacyNavigate)
provide(confirmationsRefreshKey, confirmationsRefreshTick)
</script>

<template>
  <div class="app-shell">
    <TopBar />
    <div class="app-shell__body">
      <ActivityBar :active-panel="activePanel" @select="handlePanelSelect" />
      <PanelSidebar :active-panel="activePanel" />
      <main class="app-content">
        <router-view />
      </main>
      <ChatbotPanel :visible="chatbotVisible" @toggle="chatbotVisible = !chatbotVisible" />
    </div>
  </div>
</template>

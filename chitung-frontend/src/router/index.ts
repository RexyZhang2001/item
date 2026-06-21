import { h } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { RouterView } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const RouteLayout = { render: () => h(RouterView) }

const routes: RouteRecordRaw[] = [
  {
    path: '/guardian',
    redirect: '/guardian/dashboard',
    component: RouteLayout,
    children: [
      { path: 'dashboard', name: 'guardian-dashboard', component: () => import('../pages/WorkbenchPage.vue') },
      { path: 'confirmations', name: 'guardian-confirmations', component: () => import('../pages/PendingConfirmationsPage.vue') },
      { path: 'hazards', name: 'guardian-hazards', component: () => import('../pages/HazardLedgerPage.vue') },
      { path: 'patrol', name: 'guardian-patrol', component: () => import('../pages/VisualPatrolPage.vue') },
    ],
  },
  {
    path: '/docmate',
    redirect: '/docmate/documents',
    component: RouteLayout,
    children: [
      { path: 'documents', name: 'docmate-documents', component: () => import('../pages/ShanshanDocPage.vue') },
      { path: 'forms', name: 'docmate-forms', component: () => import('../pages/SmartFormPage.vue') },
      { path: 'table-mapping', name: 'docmate-table-mapping', component: () => import('../pages/TableMappingPage.vue') },
      { path: 'reports', name: 'docmate-reports', component: () => import('../pages/WorkbenchPage.vue') },
    ],
  },
  {
    path: '/lingxun',
    redirect: '/lingxun/whatsapp',
    component: RouteLayout,
    children: [
      { path: 'whatsapp', name: 'lingxun-whatsapp', component: () => import('../pages/WhatsAppOpsPage.vue') },
    ],
  },
  {
    path: '/center',
    redirect: '/center/settings',
    component: RouteLayout,
    children: [
      { path: 'settings', name: 'center-settings', component: () => import('../pages/SystemSettingsPage.vue') },
      { path: 'assistant', name: 'center-assistant', component: () => import('../pages/AIAssistantPage.vue') },
      { path: 'skills', name: 'center-skills', component: () => import('../pages/SkillsCompatPage.vue') },
      { path: 'workflows', name: 'center-workflows', component: () => import('../pages/WorkflowsCompatPage.vue') },
    ],
  },
  {
    path: '/yaoyao',
    redirect: '/yaoyao/structured',
    component: RouteLayout,
    children: [
      { path: 'structured', name: 'yaoyao-structured', component: () => import('../pages/YaoyaoStructuredInputPage.vue') },
      { path: 'rag', name: 'yaoyao-rag', component: () => import('../pages/YaoyaoKnowledgePage.vue') },
      { path: 'feed', name: 'yaoyao-feed', component: () => import('../pages/YaoyaoKnowledgePage.vue') },
    ],
  },
  { path: '/', redirect: '/guardian/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/guardian/dashboard' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router

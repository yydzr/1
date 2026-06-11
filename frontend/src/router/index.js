import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', icon: 'HomeFilled', requiresAuth: true },
      },
      {
        path: 'notes',
        name: 'Notes',
        component: () => import('@/views/Notes.vue'),
        meta: { title: '我的笔记', icon: 'Document', requiresAuth: true },
      },
      {
        path: 'notes/:id',
        name: 'NoteDetail',
        component: () => import('@/views/NoteDetail.vue'),
        meta: { title: '笔记详情', icon: 'Document', requiresAuth: true },
      },
      {
        path: 'todos',
        name: 'Todos',
        component: () => import('@/views/Todos.vue'),
        meta: { title: '待办任务', icon: 'List', requiresAuth: true },
      },
      {
        path: 'schedules',
        name: 'Schedules',
        component: () => import('@/views/Schedules.vue'),
        meta: { title: '日程安排', icon: 'Calendar', requiresAuth: true },
      },
      {
        path: 'focus',
        name: 'Focus',
        component: () => import('@/views/Focus.vue'),
        meta: { title: '番茄专注', icon: 'Timer', requiresAuth: true },
      },
      {
        path: 'goals',
        name: 'Goals',
        component: () => import('@/views/Goals.vue'),
        meta: { title: '目标管理', icon: 'Aim', requiresAuth: true },
      },
      {
        path: 'collections',
        name: 'Collections',
        component: () => import('@/views/Collections.vue'),
        meta: { title: '知识收藏', icon: 'Collection', requiresAuth: true },
      },
      {
        path: 'achievements',
        name: 'Achievements',
        component: () => import('@/views/Achievements.vue'),
        meta: { title: '成就系统', icon: 'Trophy', requiresAuth: true },
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('@/views/Search.vue'),
        meta: { title: '全局搜索', icon: 'Search', requiresAuth: true },
      },
      {
        path: 'ai-assistant',
        name: 'AIAssistant',
        component: () => import('@/views/AIAssistant.vue'),
        meta: { title: 'AI 助手', icon: 'MagicStick', requiresAuth: true },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', icon: 'User', requiresAuth: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫 — 已登录用户访问登录/注册页重定向到首页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

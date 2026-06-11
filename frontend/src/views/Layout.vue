<template>
  <div class="layout-shell">
    <!-- 顶部栏 -->
    <header class="topbar" :class="{ scrolled: scrolled }">
      <div class="topbar-left">
        <button class="menu-btn" :class="{ open: drawerOpen }" @click="toggleDrawer" :title="drawerOpen ? '收起菜单' : '展开菜单'">
          <span></span>
          <span></span>
          <span></span>
        </button>
        <div class="brand" @click="goHome">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <defs>
              <linearGradient id="brandGrad" x1="2" y1="2" x2="22" y2="22">
                <stop offset="0%" stop-color="#4f6ef7"/>
                <stop offset="100%" stop-color="#7c5cfc"/>
              </linearGradient>
            </defs>
            <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#brandGrad)"/>
            <path d="M2 17l10 5 10-5" fill="#6b84f9"/>
            <path d="M2 12l10 5 10-5" fill="#8ba0fb"/>
          </svg>
          <span class="brand-text">效率管理</span>
        </div>
      </div>

      <div class="topbar-center">
        <el-input
          ref="searchInputRef"
          v-model="searchText"
          placeholder="搜索笔记、待办、日程..."
          :prefix-icon="Search"
          clearable
          class="topbar-search"
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <kbd class="search-kbd">⌘K</kbd>
          </template>
        </el-input>
      </div>

      <div class="topbar-right">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click">
            <el-avatar :size="34" class="user-avatar" :style="{ background: 'linear-gradient(135deg, var(--color-primary), #7c5cfc)' }">
              {{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() || 'U' }}
            </el-avatar>
            <template #dropdown>
              <el-dropdown-menu>
                <div class="user-dropdown-header">
                  <span class="user-name">{{ userStore.userInfo?.username }}</span>
                  <span class="user-email">{{ userStore.userInfo?.email }}</span>
                </div>
                <el-dropdown-item @click="$router.push('/profile')">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <span style="color: var(--color-danger)">退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <el-button v-else type="primary" size="small" round @click="handleSignIn">
          登录
        </el-button>
      </div>
    </header>

    <!-- 抽屉遮罩 -->
    <div class="drawer-overlay" :class="{ visible: drawerOpen }" @click="drawerOpen = false"></div>

    <!-- 侧边栏（桌面端常驻 + 移动端抽屉） -->
    <aside class="drawer" :class="{ open: drawerOpen }">
      <div class="drawer-gradient"></div>
      <div class="drawer-brand" @click="goHome">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <defs>
            <linearGradient id="drawerBrandGrad" x1="2" y1="2" x2="22" y2="22">
              <stop offset="0%" stop-color="#4f6ef7"/>
              <stop offset="100%" stop-color="#7c5cfc"/>
            </linearGradient>
          </defs>
          <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#drawerBrandGrad)"/>
          <path d="M2 17l10 5 10-5" fill="#6b84f9"/>
          <path d="M2 12l10 5 10-5" fill="#8ba0fb"/>
        </svg>
        <span>效率管理</span>
      </div>

      <nav class="drawer-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="onNavClick"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="drawer-footer">
        <span class="drawer-version">v1.0.0</span>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="main-content" ref="mainContentRef" @scroll="onMainScroll">
      <router-view v-slot="{ Component, route }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Search, HomeFilled, Document, List, Calendar, Timer, Aim, Collection, MagicStick, User, Trophy } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const drawerOpen = ref(false)
const searchText = ref('')
const searchInputRef = ref(null)
const mainContentRef = ref(null)
const scrolled = ref(false)

const menuItems = [
  { path: '/dashboard', label: '首页', icon: HomeFilled },
  { path: '/notes', label: '我的笔记', icon: Document },
  { path: '/todos', label: '待办任务', icon: List },
  { path: '/schedules', label: '日程安排', icon: Calendar },
  { path: '/focus', label: '番茄专注', icon: Timer },
  { path: '/goals', label: '目标管理', icon: Aim },
  { path: '/collections', label: '知识收藏', icon: Collection },
  { path: '/achievements', label: '成就系统', icon: Trophy },
  { path: '/search', label: '全局搜索', icon: Search },
  { path: '/ai-assistant', label: 'AI 助手', icon: MagicStick },
  { path: '/profile', label: '个人中心', icon: User },
]

function isActive(path) {
  const cur = route.path
  if (path === '/notes') return cur.startsWith('/notes')
  if (path === '/dashboard') return cur === '/dashboard'
  return cur === path
}

function goHome() {
  router.push('/dashboard')
}

function toggleDrawer() {
  drawerOpen.value = !drawerOpen.value
}

function onNavClick() {
  if (window.innerWidth < 1024) {
    drawerOpen.value = false
  }
}

function handleSearch() {
  if (searchText.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchText.value.trim())}`)
  }
}

function onMainScroll(e) {
  scrolled.value = e.target.scrollTop > 0
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    userStore.logout()
    router.replace('/login')
  } catch {}
}

function handleSignIn() {
  userStore.openAuthDialog('login')
}

// Ctrl+K 聚焦搜索
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchInputRef.value?.focus()
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.layout-shell {
  display: flex;
  height: 100vh;
  background: var(--color-bg);
  overflow: hidden;
}

/* === Topbar === */
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--topbar-height);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid transparent;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 16px;
  flex-shrink: 0;
  z-index: 200;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.topbar.scrolled {
  border-bottom-color: var(--color-border-light);
  box-shadow: var(--shadow-sm);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* Animated Hamburger */
.menu-btn {
  width: 36px;
  height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  padding: 0;
  transition: background var(--transition-fast);
}

.menu-btn:hover {
  background: var(--color-border-light);
}

.menu-btn span {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--color-text-secondary);
  border-radius: 2px;
  transition: all var(--transition-normal);
  transform-origin: center;
}

.menu-btn.open span:nth-child(1) {
  transform: rotate(45deg) translate(2.5px, 2.5px);
}

.menu-btn.open span:nth-child(2) {
  opacity: 0;
  transform: scaleX(0);
}

.menu-btn.open span:nth-child(3) {
  transform: rotate(-45deg) translate(2.5px, -2.5px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.brand-text {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.topbar-center {
  flex: 1;
  max-width: 520px;
  margin: 0 auto;
}

.topbar-search :deep(.el-input__wrapper) {
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  border: none;
  box-shadow: none;
  transition: all var(--transition-fast);
}

.topbar-search :deep(.el-input__wrapper:hover) {
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.topbar-search :deep(.el-input__wrapper.is-focus) {
  background: var(--color-surface);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  border: 1px solid var(--color-primary);
}

.search-kbd {
  font-size: 11px;
  font-family: var(--font-sans);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  padding: 1px 6px;
  color: var(--color-text-tertiary);
  letter-spacing: 0.02em;
  pointer-events: none;
}

.topbar-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.user-avatar {
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  font-weight: var(--font-semibold);
  color: #fff;
  font-size: var(--text-sm);
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}

/* User dropdown header */
.user-dropdown-header {
  padding: 10px 16px 12px;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: 4px;
}

.user-name {
  display: block;
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
}

.user-email {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* === Drawer Overlay === */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 300;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-normal);
}

.drawer-overlay.visible {
  opacity: 1;
  pointer-events: auto;
}

/* === Sidebar (Glass Morphism) === */
.drawer {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur) var(--glass-saturate);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturate);
  z-index: 400;
  transform: translateX(-100%);
  transition: transform var(--transition-normal);
  box-shadow: var(--glass-shadow);
  border-right: 1px solid var(--glass-border);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer.open {
  transform: translateX(0);
}

.drawer-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: linear-gradient(180deg, rgba(79, 110, 247, 0.06) 0%, transparent 100%);
  pointer-events: none;
}

.drawer-brand {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  flex-shrink: 0;
  position: relative;
}

.drawer-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
  position: relative;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 42px;
  padding: 0 16px;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  margin: 2px 12px 2px 0;
  position: relative;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  background: var(--color-border-light);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-primary-50);
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 22px;
  background: var(--color-primary);
  border-radius: 0 3px 3px 0;
  transition: transform var(--transition-spring);
}

.nav-item.active::before {
  transform: translateY(-50%) scaleY(1);
}

.drawer-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.drawer-version {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

/* === Main Content === */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 84px 32px 32px;
  max-width: var(--content-max-width);
  margin: 0 auto;
  width: 100%;
}

/* === Desktop: Persistent Sidebar === */
@media (min-width: 1024px) {
  .topbar-left .menu-btn {
    display: none;
  }

  .drawer {
    transform: translateX(0);
    position: relative;
    top: 0;
    height: 100%;
    border-radius: 0;
    border-right: 1px solid var(--color-border-light);
    background: var(--glass-bg);
    flex-shrink: 0;
    z-index: 10;
    box-shadow: none;
  }

  .drawer-overlay {
    display: none;
  }

  .topbar {
    padding-left: calc(var(--sidebar-width) + 20px);
  }

  .main-content {
    padding-top: 84px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 76px 16px 16px;
  }

  .brand-text {
    display: none;
  }

  .topbar {
    padding: 0 12px;
    gap: 8px;
  }

  .drawer {
    width: 280px;
  }
}
</style>

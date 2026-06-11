import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getProfile, updateProfile, changePassword } from '@/api/auth'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('userInfo') || 'null')
  } catch {
    localStorage.removeItem('userInfo')
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(readStoredUser())

  // 认证对话框状态
  const showAuthDialog = ref(false)
  const authDialogTab = ref('login')
  let authResolve = null
  let authReject = null

  const isLoggedIn = computed(() => !!token.value)

  // 要求登录 — 返回 Promise
  // 已登录立即 resolve；未登录弹出对话框，登录成功后 resolve，取消时 reject
  function requireAuth() {
    if (token.value) return Promise.resolve()
    if (showAuthDialog.value) {
      return new Promise((resolve, reject) => {
        const prevResolve = authResolve
        const prevReject = authReject
        authResolve = () => { if (prevResolve) prevResolve(); resolve() }
        authReject = (err) => { if (prevReject) prevReject(err); reject(err) }
      })
    }
    return new Promise((resolve, reject) => {
      authResolve = resolve
      authReject = reject
      showAuthDialog.value = true
    })
  }

  // 手动打开认证对话框
  function openAuthDialog(tab = 'login') {
    authDialogTab.value = tab
    return requireAuth()
  }

  // 内部：认证结果回调
  function _resolveAuth(success) {
    if (success && authResolve) {
      authResolve()
    } else if (!success && authReject) {
      authReject(new Error('AUTH_CANCELLED'))
    }
    authResolve = null
    authReject = null
    showAuthDialog.value = false
  }

  function _cancelAuth() {
    if (authReject) authReject(new Error('AUTH_CANCELLED'))
    authResolve = null
    authReject = null
    showAuthDialog.value = false
  }

  // 登录
  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.data.access_token
    userInfo.value = res.data.user
    localStorage.setItem('token', token.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    _resolveAuth(true)
    return res
  }

  // 注册
  async function register(username, email, password) {
    return await registerApi(username, email, password)
  }

  // 获取用户信息
  async function fetchProfile() {
    const res = await getProfile()
    userInfo.value = res.data
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return res
  }

  // 更新个人资料
  async function updateUserProfile(data) {
    const res = await updateProfile(data)
    userInfo.value = res.data
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return res
  }

  // 修改密码
  async function updatePassword(oldPassword, newPassword) {
    return await changePassword(oldPassword, newPassword)
  }

  // 退出登录
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return {
    token,
    userInfo,
    showAuthDialog,
    authDialogTab,
    isLoggedIn,
    requireAuth,
    openAuthDialog,
    _resolveAuth,
    _cancelAuth,
    login,
    register,
    fetchProfile,
    updateUserProfile,
    updatePassword,
    logout,
  }
})

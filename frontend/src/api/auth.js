import request from '@/utils/request'

/** 用户注册 */
export function register(username, email, password) {
  return request.post('/auth/register', { username, email, password })
}

/** 用户登录 */
export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

/** 获取当前用户信息 */
export function getProfile() {
  return request.get('/auth/profile')
}

/** 修改个人资料 */
export function updateProfile(data) {
  return request.put('/auth/profile', data)
}

/** 修改密码 */
export function changePassword(old_password, new_password) {
  return request.put('/auth/password', { old_password, new_password })
}

/** 获取 AI API Key */
export function getAiKey() {
  return request.get('/auth/ai-key')
}

/** 保存 AI API Key */
export function updateAiKey(ai_api_key) {
  return request.put('/auth/ai-key', { ai_api_key })
}

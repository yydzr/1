import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

// 请求拦截器 — 自动携带 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 — 统一处理错误
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === undefined) {
      return res
    }
    // 401 — 未登录或 token 过期，弹出登录对话框
    if (res.code === 401) {
      const hadToken = !!localStorage.getItem('token')
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      if (hadToken) {
        ElMessage.warning(res.message || '登录已过期，请重新登录')
      }
      // 无条件弹出登录弹窗（游客和过期 token 都弹）
      import('@/stores/user').then(({ useUserStore }) => {
        const store = useUserStore()
        if (!store.showAuthDialog) {
          store.showAuthDialog = true
        }
      })
      return Promise.reject(new Error(res.message || '请先登录'))
    }
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        const hadToken = !!localStorage.getItem('token')
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        if (hadToken) {
          ElMessage.warning('登录已过期，请重新登录')
        }
        // 无条件弹出登录弹窗
        import('@/stores/user').then(({ useUserStore }) => {
          const store = useUserStore()
          if (!store.showAuthDialog) {
            store.showAuthDialog = true
          }
        })
      } else if (status === 500) {
        ElMessage.error('服务器内部错误')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else {
        ElMessage.error(error.response.data?.message || '网络请求失败')
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络或后端服务')
    }
    return Promise.reject(error)
  }
)

export default request

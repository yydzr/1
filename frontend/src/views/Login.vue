<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5z" fill="#fbbc04"/>
          <path d="M2 17l10 5 10-5" fill="#f9ab00"/>
          <path d="M2 12l10 5 10-5" fill="#fdd663"/>
        </svg>
        <h1>效率管理</h1>
        <p>AI 智能个人效率管理系统</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名或邮箱" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password
            :prefix-icon="Lock" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button class="login-btn" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        还没有账户？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/dashboard')
  } catch {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

.login-card {
  width: 400px;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: 40px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border-light);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-top: 12px;
}

.login-header p {
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  margin-top: 4px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  background: var(--color-primary);
  border: none;
  color: #fff;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.login-btn:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.login-btn:active { transform: scale(0.97); }

.login-footer {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
}

.login-footer a {
  color: var(--color-primary);
  font-weight: var(--font-medium);
}
</style>

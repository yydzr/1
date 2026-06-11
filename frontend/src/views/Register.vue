<template>
  <div class="register-page">
    <div class="register-card">
      <div class="register-header">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5z" fill="#fbbc04"/>
          <path d="M2 17l10 5 10-5" fill="#f9ab00"/>
          <path d="M2 12l10 5 10-5" fill="#fdd663"/>
        </svg>
        <h1>创建新账户</h1>
        <p>注册 AI 智能个人效率管理系统</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="至少 3 个字符" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少 6 个字符" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button class="register-btn" :loading="loading" @click="handleRegister">
            {{ loading ? '注册中...' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        已有账户？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少 3 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.register(form.username, form.email, form.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    ElMessage.error('注册失败，请检查输入信息')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

.register-card {
  width: 420px;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: 40px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border-light);
}

.register-header {
  text-align: center;
  margin-bottom: 28px;
}

.register-header h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-top: 12px;
}

.register-header p {
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  margin-top: 4px;
}

.register-btn {
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

.register-btn:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.register-btn:active { transform: scale(0.97); }

.register-footer {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
}

.register-footer a {
  color: var(--color-primary);
  font-weight: var(--font-medium);
}
</style>

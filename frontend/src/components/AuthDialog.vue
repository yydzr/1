<template>
  <el-dialog
    v-model="userStore.showAuthDialog"
    :close-on-click-modal="false"
    width="420px"
    :show-close="false"
    :close-on-press-escape="false"
    destroy-on-close
  >
    <template #header>
      <div class="dialog-header">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5z" fill="#fbbc04"/>
          <path d="M2 17l10 5 10-5" fill="#f9ab00"/>
          <path d="M2 12l10 5 10-5" fill="#fdd663"/>
        </svg>
      </div>
    </template>

    <!-- 标签切换 -->
    <div class="auth-tabs">
      <button
        class="auth-tab"
        :class="{ active: userStore.authDialogTab === 'login' }"
        @click="switchTab('login')"
      >登录</button>
      <button
        class="auth-tab"
        :class="{ active: userStore.authDialogTab === 'register' }"
        @click="switchTab('register')"
      >注册</button>
    </div>

    <!-- 登录表单 -->
    <el-form
      v-if="userStore.authDialogTab === 'login'"
      ref="loginFormRef"
      :model="loginForm"
      :rules="loginRules"
      label-position="top"
      size="large"
      @keyup.enter="handleLogin"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="loginForm.username" placeholder="请输入用户名或邮箱" :prefix-icon="User" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" />
      </el-form-item>
      <el-form-item>
        <el-button class="submit-btn" :loading="loginLoading" @click="handleLogin">
          {{ loginLoading ? '登录中...' : '登 录' }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 注册表单 -->
    <el-form
      v-else
      ref="registerFormRef"
      :model="registerForm"
      :rules="registerRules"
      label-position="top"
      size="large"
      @keyup.enter="handleRegister"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="registerForm.username" placeholder="至少 3 个字符" :prefix-icon="User" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="registerForm.email" placeholder="请输入邮箱" :prefix-icon="Message" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="registerForm.password" type="password" placeholder="至少 6 个字符" show-password :prefix-icon="Lock" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" show-password :prefix-icon="Lock" />
      </el-form-item>
      <el-form-item>
        <el-button class="submit-btn" :loading="registerLoading" @click="handleRegister">
          {{ registerLoading ? '注册中...' : '注 册' }}
        </el-button>
      </el-form-item>
    </el-form>

    <div class="auth-footer" v-if="userStore.authDialogTab === 'login'">
      还没有账户？<a href="javascript:void(0)" @click="switchTab('register')">立即注册</a>
    </div>
    <div class="auth-footer" v-else>
      已有账户？<a href="javascript:void(0)" @click="switchTab('login')">立即登录</a>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const registerRules = {
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

function switchTab(tab) {
  userStore.authDialogTab = tab
  loginForm.username = ''
  loginForm.password = ''
  registerForm.username = ''
  registerForm.email = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
}

async function handleLogin() {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  loginLoading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    loginForm.username = ''
    loginForm.password = ''
  } catch {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  registerLoading.value = true
  try {
    await userStore.register(registerForm.username, registerForm.email, registerForm.password)
    ElMessage.success('注册成功，请登录')
    switchTab('login')
  } catch {
    ElMessage.error('注册失败，请检查输入信息')
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.dialog-header {
  text-align: center;
}

.auth-tabs {
  display: flex;
  border-bottom: 2px solid var(--color-border-light);
  margin-bottom: 24px;
}

.auth-tab {
  flex: 1;
  background: none;
  border: none;
  padding: 10px 0;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.auth-tab:hover {
  color: var(--color-text-primary);
}

.auth-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.submit-btn {
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

.submit-btn:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.submit-btn:active { transform: scale(0.97); }

.auth-footer {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-sm);
  margin-top: 6px;
}

.auth-footer a {
  color: var(--color-primary);
  font-weight: var(--font-medium);
}
</style>

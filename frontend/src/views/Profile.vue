<template>
  <div class="profile-page">
    <div class="profile-grid">
      <div class="chart-card">
        <div class="card-title">个人信息</div>
        <div class="profile-avatar"><el-avatar :size="80" icon="UserFilled"/><h3>{{userStore.userInfo?.username}}</h3></div>
        <el-descriptions :column="1" border style="margin-top:16px">
          <el-descriptions-item label="用户名">{{userStore.userInfo?.username}}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{userStore.userInfo?.email}}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{userStore.userInfo?.created_at}}</el-descriptions-item>
        </el-descriptions>
        <el-button type="primary" style="margin-top:16px;width:100%" @click="openProfileDialog">修改个人资料</el-button>
      </div>
      <div>
        <div class="chart-card"><div class="card-title">用户数据统计</div><div class="stats-row"><div class="user-stat"><span class="usv">{{stats.notes_count||0}}</span><span class="usl">笔记总数</span></div><div class="user-stat"><span class="usv">{{stats.todos_total||0}}</span><span class="usl">待办总数</span></div><div class="user-stat"><span class="usv">{{stats.total_focus||0}}<small>m</small></span><span class="usl">累计专注</span></div></div></div>
        <div class="chart-card" style="margin-top:16px"><div class="card-title">安全设置</div>
          <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
            <el-form-item label="旧密码" prop="old_password"><el-input v-model="pwdForm.old_password" type="password" show-password/></el-form-item>
            <el-form-item label="新密码" prop="new_password"><el-input v-model="pwdForm.new_password" type="password" show-password/></el-form-item>
            <el-form-item label="确认密码" prop="confirm_password"><el-input v-model="pwdForm.confirm_password" type="password" show-password/></el-form-item>
            <el-form-item><el-button type="primary" :loading="pwdLoading" @click="handleChangePwd">修改密码</el-button></el-form-item>
          </el-form>
        </div>
        <div class="chart-card" style="margin-top:16px"><div class="card-title">AI 设置</div>
          <p style="color:var(--color-text-tertiary);font-size:var(--text-sm);margin-bottom:16px">配置你自己的 DeepSeek API Key，AI 助手将使用你的个人 Key 调用。已保存的 Key 只显示脱敏信息。</p>
          <el-form label-width="100px">
            <el-form-item label="当前状态">
              <el-tag :type="aiKeyStatus.hasKey ? 'success' : 'info'">{{ aiKeyStatus.text }}</el-tag>
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="aiApiKey" type="password" show-password placeholder="输入新 Key；留空保存将清空当前 Key" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="aiKeyLoading" @click="handleSaveAiKey">保存</el-button>
              <el-button @click="loadAiKey">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
    <el-dialog v-model="profileDialog" title="修改个人资料" width="480px">
      <el-form :model="profileForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="profileForm.username"/></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="profileForm.email"/></el-form-item>
        <el-form-item label="头像 URL"><el-input v-model="profileForm.avatar"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="profileDialog=false">取消</el-button><el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref,reactive,onMounted} from 'vue';import {ElMessage} from 'element-plus';import {useUserStore} from '@/stores/user';import {getStats} from '@/api/dashboard';import {getAiKey,updateAiKey} from '@/api/auth'
const userStore=useUserStore();const stats=reactive({});const profileDialog=ref(false);const profileLoading=ref(false)
const profileForm=reactive({username:userStore.userInfo?.username||'',email:userStore.userInfo?.email||'',avatar:userStore.userInfo?.avatar||''})
const pwdFormRef=ref(null);const pwdLoading=ref(false);const pwdForm=reactive({old_password:'',new_password:'',confirm_password:''})
const aiApiKey=ref('');const aiKeyLoading=ref(false);const aiKeyStatus=reactive({hasKey:false,text:'未设置'})
const validateConfirmPwd=(rule,value,callback)=>{if(value!==pwdForm.new_password)callback(new Error('两次输入不一致'));else callback()}
const pwdRules={old_password:[{required:true,message:'请输入旧密码',trigger:'blur'}],new_password:[{required:true,min:6,message:'至少6个字符',trigger:'blur'}],confirm_password:[{required:true,message:'请确认密码',trigger:'blur'},{validator:validateConfirmPwd,trigger:'blur'}]}
async function openProfileDialog(){profileForm.username=userStore.userInfo?.username||'';profileForm.email=userStore.userInfo?.email||'';profileForm.avatar=userStore.userInfo?.avatar||'';profileDialog.value=true}
async function handleUpdateProfile(){profileLoading.value=true;try{await userStore.updateUserProfile({username:profileForm.username,email:profileForm.email,avatar:profileForm.avatar});ElMessage.success('修改成功');profileDialog.value=false}catch{}finally{profileLoading.value=false}}
async function handleChangePwd(){const valid=await pwdFormRef.value.validate().catch(()=>false);if(!valid)return;pwdLoading.value=true;try{await userStore.updatePassword(pwdForm.old_password,pwdForm.new_password);ElMessage.success('密码修改成功');pwdForm.old_password='';pwdForm.new_password='';pwdForm.confirm_password=''}catch{}finally{pwdLoading.value=false}}
function updateAiKeyStatus(data){aiKeyStatus.hasKey=!!data?.has_ai_api_key;aiKeyStatus.text=data?.has_ai_api_key?`已设置 (${data.masked_ai_api_key})`:'未设置'}
async function loadAiKey(){try{const res=await getAiKey();updateAiKeyStatus(res.data);aiApiKey.value=''}catch{}}
async function handleSaveAiKey(){aiKeyLoading.value=true;try{const res=await updateAiKey(aiApiKey.value);updateAiKeyStatus(res.data);aiApiKey.value='';ElMessage.success('API Key 保存成功')}catch{}finally{aiKeyLoading.value=false}}
onMounted(async()=>{try{const res=await getStats();Object.assign(stats,res.data||{})}catch{};loadAiKey()})
</script>

<style scoped>
.profile-grid{display:grid;grid-template-columns:360px 1fr;gap:16px}@media(max-width:768px){.profile-grid{grid-template-columns:1fr}}
.chart-card{background:var(--color-surface);border-radius:var(--radius-lg);padding:24px;box-shadow:var(--shadow-sm);border:1px solid var(--color-border-light)}.card-title{font-weight:var(--font-semibold);color:var(--color-text-primary);font-size:var(--text-base);margin-bottom:16px}
.profile-avatar{text-align:center;padding:16px 0}.profile-avatar h3{margin-top:12px;color:var(--color-text-primary);font-weight:var(--font-medium)}
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.user-stat{text-align:center;padding:20px 0;background:var(--color-surface-secondary);border-radius:var(--radius-md)}.usv{display:block;font-size:var(--text-2xl);font-weight:var(--font-semibold);color:var(--color-text-primary)}.usv small{font-size:var(--text-xs);font-weight:var(--font-normal);color:var(--color-text-tertiary)}.usl{font-size:var(--text-xs);color:var(--color-text-tertiary);margin-top:4px;display:block}
</style>

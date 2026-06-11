<template>
  <div class="goals-page">
    <div class="toolbar">
      <el-select v-model="filterStatus" placeholder="状态" clearable @change="filterGoals" style="width:120px">
        <el-option label="全部" value=""/><el-option label="进行中" value="进行中"/><el-option label="已完成" value="已完成"/><el-option label="已放弃" value="已放弃"/>
      </el-select>
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增目标</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="goals.length" class="goals-grid">
        <div v-for="goal in goals" :key="goal.id" class="goal-card">
          <div class="goal-head"><span class="goal-title">{{goal.title}}</span><el-tag :type="statusTag(goal.status)" size="small" round>{{goal.status}}</el-tag></div>
          <div class="goal-body"><p class="goal-desc">{{goal.description||'暂无描述'}}</p><el-progress :percentage="goal.progress" :stroke-width="10" :color="goal.progress>=100?'#0f9d58':'#1a73e8'"/><div class="goal-dates"><span v-if="goal.start_date">{{goal.start_date}}</span><span v-if="goal.end_date">— {{goal.end_date}}</span></div></div>
          <div class="goal-foot"><div><el-button size="small" @click="updateProgress(goal)">更新进度</el-button><el-button size="small" @click="aiPlan(goal)" :loading="aiLoading">AI 计划</el-button></div><div><el-button link :icon="Edit" @click="openDialog(goal)"/><el-button link :icon="Delete" @click="handleDelete(goal)"/></div></div>
        </div>
      </div>
      <el-empty v-else description="暂无目标"/>
    </div>
    <div v-if="page.total > page.per_page" class="pager"><el-pagination background layout="prev, pager, next, total" :current-page="page.page" :page-size="page.per_page" :total="page.total" @current-change="changePage"/></div>

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑目标':'新增目标'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title"/></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3"/></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status" style="width:160px"><el-option label="进行中" value="进行中"/><el-option label="已完成" value="已完成"/><el-option label="已放弃" value="已放弃"/></el-select></el-form-item>
        <el-form-item label="进度"><el-slider v-model="form.progress" :min="0" :max="100" show-input/></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%"/></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="progressDialog" title="更新进度" width="400px"><el-slider v-model="progressVal" :min="0" :max="100" show-input/><template #footer><el-button @click="progressDialog=false">取消</el-button><el-button type="primary" @click="saveProgress">确定</el-button></template></el-dialog>
    <el-dialog v-model="planDialog" title="AI 执行计划" width="600px"><div v-if="planData"><h4>{{planData.goal_title}}</h4><div v-for="(phase,i) in planData.plan" :key="i" style="margin:12px 0"><el-tag>{{phase.phase}}</el-tag><ul style="margin:8px 0 0 20px"><li v-for="(t,j) in phase.tasks" :key="j">{{t}}</li></ul></div></div><template #footer><el-button @click="planDialog=false">关闭</el-button></template></el-dialog>
  </div>
</template>

<script setup>
import {ref,reactive,onMounted} from 'vue';import {ElMessage,ElMessageBox} from 'element-plus';import {Plus,Edit,Delete} from '@element-plus/icons-vue'
import {getGoals,createGoal,updateGoal,deleteGoal,updateGoalProgress,aiGeneratePlan} from '@/api/goals'
const goals=ref([]);const loading=ref(false);const filterStatus=ref('');const dialogVisible=ref(false);const isEdit=ref(false);const submitting=ref(false);const editId=ref(null);const progressDialog=ref(false);const progressVal=ref(0);const progressGoalId=ref(null);const aiLoading=ref(false);const planDialog=ref(false);const planData=ref(null)
const page=reactive({page:1,per_page:12,total:0})
const form=reactive({title:'',description:'',status:'进行中',progress:0,start_date:'',end_date:''})
function statusTag(s){return s==='已完成'?'success':s==='进行中'?'primary':'info'}
async function loadGoals(){loading.value=true;try{const res=await getGoals({status:filterStatus.value,page:page.page,per_page:page.per_page,include_total:1});const data=res.data||{};goals.value=data.items||[];page.total=data.total||0}finally{loading.value=false}}
function filterGoals(){page.page=1;loadGoals()}
function changePage(p){page.page=p;loadGoals()}
function openDialog(g){if(g){isEdit.value=true;editId.value=g.id;Object.assign(form,g)}else{isEdit.value=false;editId.value=null;form.title='';form.description='';form.status='进行中';form.progress=0;form.start_date='';form.end_date=''}dialogVisible.value=true}
async function handleSubmit(){if(!form.title.trim()){ElMessage.warning('请输入标题');return}submitting.value=true;try{if(isEdit.value){await updateGoal(editId.value,form);ElMessage.success('修改成功')}else{await createGoal(form);ElMessage.success('创建成功')}dialogVisible.value=false;loadGoals()}finally{submitting.value=false}}
async function handleDelete(g){try{await ElMessageBox.confirm('确认删除？','提示',{type:'warning'});await deleteGoal(g.id);ElMessage.success('删除成功');loadGoals()}catch{}}
function updateProgress(g){progressGoalId.value=g.id;progressVal.value=g.progress;progressDialog.value=true}
async function saveProgress(){await updateGoalProgress(progressGoalId.value,progressVal.value);ElMessage.success('进度已更新');progressDialog.value=false;loadGoals()}
async function aiPlan(g){aiLoading.value=true;try{const res=await aiGeneratePlan(g.id);planData.value=res.data;planDialog.value=true}finally{aiLoading.value=false}}
onMounted(loadGoals)
</script>

<style scoped>
.toolbar{display:flex;gap:10px;margin-bottom:16px;align-items:center}.spacer{flex:1}.pager{display:flex;justify-content:center;margin-top:18px}
.goals-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.goal-card{background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 2px rgba(60,64,67,0.1),0 1px 3px rgba(60,64,67,0.08)}
.goal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.goal-title{font-weight:500;color:#202124}
.goal-desc{color:#5f6368;font-size:13px;margin-bottom:12px;min-height:20px}
.goal-dates{display:flex;gap:8px;margin-top:10px;font-size:12px;color:#5f6368}
.goal-foot{display:flex;justify-content:space-between;align-items:center;margin-top:14px}
</style>

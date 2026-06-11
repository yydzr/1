<template>
  <div class="todos-page">
    <div class="toolbar">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="filterTodos" style="width:120px">
        <el-option label="全部" value="" /><el-option label="未完成" value="未完成" /><el-option label="已完成" value="已完成" />
      </el-select>
      <el-button @click="loadTodayTodos">今日任务</el-button>
      <el-button @click="loadOverdueTodos" type="warning">逾期待办</el-button>
      <div class="spacer"></div>
      <el-button @click="aiGenerateDialog = true" :icon="MagicStick">AI 生成</el-button>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增待办</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="todos.length" class="todos-list">
        <div v-for="todo in todos" :key="todo.id" class="todo-card" :class="{ done: todo.status === '已完成' }">
          <div class="todo-head">
            <div class="todo-left">
              <el-checkbox v-model="todo._done" @change="toggleDone(todo)" />
              <span class="todo-title" :class="{ done: todo.status === '已完成' }">{{ todo.title }}</span>
              <el-tag :type="priorityTag(todo.priority)" size="small" round>{{ todo.priority }}</el-tag>
              <el-tag v-if="todo.status === '已完成'" size="small" round style="background:#e6f4ea;color:#137333;">已完成</el-tag>
            </div>
            <div class="todo-right">
              <el-button link :icon="Edit" @click="openDialog(todo)" />
              <el-button link :icon="Delete" @click="handleDelete(todo)" />
            </div>
          </div>
          <div class="todo-desc" v-if="todo.description">{{ todo.description?.slice(0, 80) }}</div>
          <div class="todo-meta">
            <span v-if="todo.due_date" class="meta-text">截止: {{ todo.due_date?.slice(0, 10) }}</span>
            <el-tag size="small" type="info">{{ todo.category }}</el-tag>
            <div style="flex:1;margin:0 12px;"><el-progress :percentage="todo.progress||0" :stroke-width="6" /></div>
            <el-button link size="small" @click="openProgressDialog(todo)">更新进度</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无待办" />
    </div>
    <div v-if="listMode === 'all' && page.total > page.per_page" class="pager"><el-pagination background layout="prev, pager, next, total" :current-page="page.page" :page-size="page.per_page" :total="page.total" @current-change="changePage"/></div>

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑待办':'新增待办'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="优先级"><el-radio-group v-model="form.priority"><el-radio-button label="低"/><el-radio-button label="中"/><el-radio-button label="高"/></el-radio-group></el-form-item>
        <el-form-item label="分类"><el-input v-model="form.category" /></el-form-item>
        <el-form-item label="截止日期"><el-date-picker v-model="form.due_date" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="isEdit" @click="doAiRecommendPriority" :loading="aiLoading">AI 推荐优先级</el-button>
        <el-button v-if="isEdit" @click="aiSplitThisTask" :loading="aiLoading">AI 拆分</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="progressDialog" title="更新进度" width="400px">
      <el-slider v-model="progressValue" :min="0" :max="100" show-input />
      <template #footer><el-button @click="progressDialog=false">取消</el-button><el-button type="primary" @click="saveProgress">确定</el-button></template>
    </el-dialog>

    <el-dialog v-model="aiGenerateDialog" title="AI 一句话生成待办" width="500px">
      <el-input v-model="aiPrompt" type="textarea" :rows="3" placeholder="描述你想做什么事..." />
      <template #footer><el-button @click="aiGenerateDialog=false">取消</el-button><el-button type="primary" :loading="aiLoading" @click="aiGenerate">生成</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, MagicStick } from '@element-plus/icons-vue'
import { getTodos, createTodo, updateTodo, deleteTodo, toggleTodo, updateProgress, getTodayTodos, getOverdueTodos, aiGenerateTodo, aiSplitTask, aiRecommendPriority } from '@/api/todos'

const todos=ref([]);const loading=ref(false);const filterStatus=ref('');const dialogVisible=ref(false);const isEdit=ref(false)
const submitting=ref(false);const aiLoading=ref(false);const editId=ref(null);const progressDialog=ref(false)
const progressValue=ref(0);const progressTodoId=ref(null);const aiGenerateDialog=ref(false);const aiPrompt=ref('')
const page=reactive({page:1,per_page:12,total:0});const listMode=ref('all')
const form=reactive({title:'',description:'',priority:'中',category:'默认',due_date:''})

async function loadTodos(){listMode.value='all';loading.value=true;try{const res=await getTodos({status:filterStatus.value,page:page.page,per_page:page.per_page,include_total:1});const data=res.data||{};todos.value=(data.items||[]).map(t=>({...t,_done:t.status==='已完成'}));page.total=data.total||0}finally{loading.value=false}}
async function loadTodayTodos(){listMode.value='today';page.total=0;const res=await getTodayTodos();todos.value=res.data.map(t=>({...t,_done:t.status==='已完成'}))}
async function loadOverdueTodos(){listMode.value='overdue';page.total=0;const res=await getOverdueTodos();todos.value=res.data.map(t=>({...t,_done:false}))}
function filterTodos(){page.page=1;loadTodos()}
function changePage(p){page.page=p;loadTodos()}
function priorityTag(p){return p==='高'?'danger':p==='中'?'warning':'info'}
function openDialog(todo){if(todo){isEdit.value=true;editId.value=todo.id;form.title=todo.title;form.description=todo.description;form.priority=todo.priority;form.category=todo.category;form.due_date=todo.due_date}else{isEdit.value=false;editId.value=null;form.title='';form.description='';form.priority='中';form.category='默认';form.due_date=''}dialogVisible.value=true}
async function handleSubmit(){if(!form.title.trim()){ElMessage.warning('请输入标题');return}submitting.value=true;try{if(isEdit.value){await updateTodo(editId.value,form);ElMessage.success('修改成功')}else{await createTodo(form);ElMessage.success('创建成功')}dialogVisible.value=false;loadTodos()}finally{submitting.value=false}}
async function handleDelete(todo){try{await ElMessageBox.confirm('确认删除？','提示',{type:'warning'});await deleteTodo(todo.id);ElMessage.success('删除成功');loadTodos()}catch{}}
async function toggleDone(todo){await toggleTodo(todo.id);loadTodos()}
function openProgressDialog(todo){progressTodoId.value=todo.id;progressValue.value=todo.progress||0;progressDialog.value=true}
async function saveProgress(){await updateProgress(progressTodoId.value,progressValue.value);ElMessage.success('进度已更新');progressDialog.value=false;loadTodos()}
async function aiGenerate(){if(!aiPrompt.value.trim()){ElMessage.warning('请输入描述');return}aiLoading.value=true;try{const res=await aiGenerateTodo(aiPrompt.value);form.title=res.data.title;form.description=res.data.description;form.priority=res.data.priority;form.category=res.data.category;aiGenerateDialog.value=false;dialogVisible.value=true;ElMessage.success('AI 已生成')}finally{aiLoading.value=false}}
async function aiSplitThisTask(){if(!form.title.trim()){ElMessage.warning('先输入标题');return}aiLoading.value=true;try{const res=await aiSplitTask(form.title);ElMessage.success('AI 拆分: '+JSON.stringify(res.data.subtasks?.map(s=>s.title).join('; ')))}finally{aiLoading.value=false}}
async function doAiRecommendPriority(){aiLoading.value=true;try{const res=await aiRecommendPriority({title:form.title,description:form.description});form.priority=res.data.priority;ElMessage.success('AI 推荐: '+form.priority)}finally{aiLoading.value=false}}
onMounted(loadTodos)
</script>

<style scoped>
.toolbar{display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap}.spacer{flex:1}.pager{display:flex;justify-content:center;margin-top:18px}
.todos-list{display:flex;flex-direction:column;gap:10px}
.todo-card{background:#fff;border-radius:8px;padding:16px 20px;box-shadow:0 1px 2px rgba(60,64,67,0.08)}
.todo-card.done{opacity:0.55}
.todo-head{display:flex;justify-content:space-between;align-items:center}
.todo-left{display:flex;align-items:center;gap:8px;flex:1}
.todo-title{font-weight:500;color:#202124}.todo-title.done{text-decoration:line-through;color:#5f6368}
.todo-desc{margin:6px 0 6px 32px;color:#5f6368;font-size:13px}
.todo-meta{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12px}.meta-text{color:#5f6368}
</style>

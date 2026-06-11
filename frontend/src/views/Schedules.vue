<template>
  <div class="schedules-page">
    <div class="sched-grid">
      <div class="chart-card">
        <div class="card-head">
          <span>日程日历</span>
          <div><el-button size="small" @click="loadToday">今日</el-button><el-button size="small" @click="loadWeek">本周</el-button></div>
        </div>
        <el-calendar v-model="calendarDate">
          <template #date-cell="{data}">
            <div class="cal-day" :class="{selected: selectedDate===data.day}" @click="selectDate(data.day)">
              <span>{{data.day.split('-').pop()?.replace(/^0/,'')}}</span>
              <div class="dots">
                <span v-if="hasSchedule(data.day)" class="dot dot-start"></span>
                <span v-if="hasEndDate(data.day)" class="dot dot-end"></span>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>
      <div class="chart-card">
        <div class="card-head"><span>{{scheduleTitle}}</span><el-button type="primary" size="small" :icon="Plus" @click="openDialog()">新增</el-button></div>
        <div v-if="schedules.length" class="s-list">
          <div v-for="s in schedules" :key="s.id" class="s-item" :style="{borderLeft:`4px solid ${s.color}`}">
            <div class="s-info"><strong>{{s.title}}</strong><span class="s-time">{{s.start_time?.slice(5,16)?.replace('-','/')?.replace('-','/')}} - {{s.end_time?.slice(5,16)?.replace('-','/')?.replace('-','/')}}</span><span v-if="s.location" class="s-loc">{{s.location}}</span></div>
            <div class="s-acts"><el-button link :icon="Edit" @click="openDialog(s)"/><el-button link :icon="Delete" @click="handleDelete(s)"/></div>
          </div>
        </div>
        <el-empty v-else description="暂无日程" :image-size="60"/>
        <div v-if="page.total > page.per_page" class="pager"><el-pagination small background layout="prev, pager, next" :current-page="page.page" :page-size="page.per_page" :total="page.total" @current-change="changePage"/></div>
      </div>
    </div>
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑日程':'新增日程'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title"/></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2"/></el-form-item>
        <el-form-item label="地点"><el-input v-model="form.location"/></el-form-item>
        <el-form-item label="开始时间" required><el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%"/></el-form-item>
        <el-form-item label="结束时间" required><el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%"/></el-form-item>
        <el-form-item label="颜色"><el-color-picker v-model="form.color"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref,reactive,onMounted,watch} from 'vue';import {ElMessage,ElMessageBox} from 'element-plus';import {Plus,Edit,Delete} from '@element-plus/icons-vue'
import {getSchedules,getScheduleDates,createSchedule,updateSchedule,deleteSchedule,getTodaySchedules,getWeekSchedules} from '@/api/schedules'
import {useUserStore} from '@/stores/user'
const userStore=useUserStore()
const schedules=ref([]);const calendarDate=ref(new Date());const scheduleTitle=ref('日程列表');const dialogVisible=ref(false);const isEdit=ref(false);const submitting=ref(false);const editId=ref(null);const allScheduleDates=ref(new Set());const selectedDate=ref('')
const page=reactive({page:1,per_page:10,total:0})
const form=reactive({title:'',description:'',location:'',start_time:'',end_time:'',color:'#1a73e8'})
const endDates=ref(new Set())
async function refreshAllDates(){let res=null;try{res=await getScheduleDates()}catch{return}const data=res.data||{};allScheduleDates.value=new Set(data.starts||[]);endDates.value=new Set(data.ends||[])}
function hasEndDate(day){return endDates.value.has(day)}
async function loadSchedules(date){try{const res=await getSchedules({date,page:page.page,per_page:page.per_page,include_total:1});const data=res.data||{};schedules.value=data.items||[];page.total=data.total||0;scheduleTitle.value=date?`${date} 日程`:'所有日程'}catch{}}
function selectDate(day){selectedDate.value=day;page.page=1;loadSchedules(day)}
async function loadToday(){const today=new Date().toISOString().slice(0,10);selectedDate.value=today;calendarDate.value=new Date();page.page=1;const res=await getTodaySchedules();schedules.value=res.data;page.total=0;scheduleTitle.value='今日日程'}
async function loadWeek(){selectedDate.value='';calendarDate.value=new Date();page.page=1;const res=await getWeekSchedules();schedules.value=res.data;page.total=0;scheduleTitle.value='本周日程'}
function changePage(p){page.page=p;loadSchedules(selectedDate.value)}
function hasSchedule(day){return allScheduleDates.value.has(day)}
function openDialog(s){if(s){isEdit.value=true;editId.value=s.id;form.title=s.title;form.description=s.description;form.location=s.location;form.start_time=s.start_time;form.end_time=s.end_time;form.color=s.color}else{isEdit.value=false;editId.value=null;form.title='';form.description='';form.location='';form.start_time='';form.end_time='';form.color='#1a73e8'}dialogVisible.value=true}
async function handleSubmit(){if(!form.title.trim()||!form.start_time||!form.end_time){ElMessage.warning('必填项不能为空');return}submitting.value=true;try{if(isEdit.value){await updateSchedule(editId.value,form);ElMessage.success('修改成功')}else{await createSchedule(form);ElMessage.success('创建成功')}dialogVisible.value=false;await refreshAllDates();if(selectedDate.value){loadSchedules(selectedDate.value)}else if(scheduleTitle.value==='今日日程'){loadToday()}else{loadWeek()}}finally{submitting.value=false}}
async function handleDelete(s){try{await ElMessageBox.confirm('确认删除？','提示',{type:'warning'});await deleteSchedule(s.id);ElMessage.success('删除成功');await refreshAllDates();if(selectedDate.value){loadSchedules(selectedDate.value)}else if(scheduleTitle.value==='今日日程'){loadToday()}else{loadWeek()}}catch{}}
async function init(){await refreshAllDates();loadSchedules()}
onMounted(()=>{if(userStore.isLoggedIn)init()})
watch(()=>userStore.isLoggedIn,(loggedIn)=>{if(loggedIn)init()})
</script>

<style scoped>
.sched-grid{display:grid;grid-template-columns:2fr 1fr;gap:16px}@media(max-width:1200px){.sched-grid{grid-template-columns:1fr}}
.chart-card{background:var(--color-surface);border-radius:var(--radius-lg);padding:20px;box-shadow:var(--shadow-sm);border:1px solid var(--color-border-light)}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-weight:var(--font-semibold);color:var(--color-text-primary)}
.s-list{display:flex;flex-direction:column;gap:8px;max-height:500px;overflow-y:auto}
.s-item{display:flex;justify-content:space-between;align-items:flex-start;padding:10px 12px;background:var(--color-surface-secondary);border-radius:var(--radius-sm)}
.s-info{display:flex;flex-direction:column;gap:2px}.s-info strong{color:var(--color-text-primary)}.s-time{font-size:var(--text-xs);color:var(--color-text-tertiary)}.s-loc{font-size:var(--text-xs);color:var(--color-text-tertiary)}
.s-acts{flex-shrink:0}.pager{display:flex;justify-content:center;margin-top:12px}
.cal-day{display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;width:100%;height:100%;min-height:36px;border-radius:var(--radius-sm);transition:background var(--transition-fast)}
.cal-day:hover{background:var(--color-border-light)}
.cal-day.selected{background:var(--color-primary);color:#fff;font-weight:var(--font-semibold)}
.cal-day.selected .dot{background:#fff}
.dots{display:flex;gap:3px;margin-top:2px}
.dot{width:6px;height:6px;border-radius:50%}
.dot-start{background:var(--color-primary)}
.dot-end{background:var(--color-accent)}
</style>

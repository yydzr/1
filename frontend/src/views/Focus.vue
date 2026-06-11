<template>
  <div class="focus-page">
    <div class="focus-grid">
      <div class="focus-left">
        <div class="chart-card timer-card">
          <div class="timer-circle" :class="{running:isRunning}">
            <span class="timer-display">{{formatTime(timeLeft)}}</span>
            <span class="timer-label">{{isBreak?'休息时间':'专注中'}}</span>
          </div>
          <div class="timer-controls">
            <el-button v-if="!isRunning" type="primary" size="large" :icon="VideoPlay" round @click="startFocus">开始专注</el-button>
            <el-button v-else type="warning" size="large" :icon="VideoPause" round @click="pauseFocus">暂停</el-button>
            <el-button size="large" :icon="RefreshRight" round @click="resetTimer">重置</el-button>
          </div>
          <div class="timer-settings">
            <span>专注</span><el-input-number v-model="focusMinutes" :min="1" :max="120" :step="5" size="small" :disabled="isRunning"/>
            <span>休息</span><el-input-number v-model="breakMinutes" :min="1" :max="60" :step="1" size="small" :disabled="isRunning"/>
          </div>
        </div>
        <div class="stat-row">
          <div class="chart-card stat-mini"><span class="sv">{{stats.today_focus||0}}<small>m</small></span><span class="sl">今日专注</span></div>
          <div class="chart-card stat-mini"><span class="sv">{{stats.total_focus||0}}<small>m</small></span><span class="sl">累计专注</span></div>
        </div>
      </div>
      <div class="focus-right">
        <div class="chart-card"><div class="card-title">最近7天专注趋势</div><div ref="focusChartRef" style="height:220px"></div></div>
        <div class="chart-card" style="margin-top:16px"><div class="card-title">专注记录</div>
          <el-table :data="records" style="width:100%" max-height="260">
            <el-table-column prop="focus_type" label="类型" width="100"/><el-table-column prop="duration" label="时长(min)" width="100"/><el-table-column prop="started_at" label="开始时间"/><el-table-column prop="ended_at" label="结束时间"/>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref,reactive,onMounted,onBeforeUnmount} from 'vue';import {ElMessage} from 'element-plus';import * as echarts from 'echarts'
import {VideoPlay,VideoPause,RefreshRight} from '@element-plus/icons-vue';import {getFocusRecords,createFocusRecord,getFocusStats,getFocusCharts} from '@/api/focus'
const focusChartRef=ref(null);let focusChart=null;const isRunning=ref(false);const isBreak=ref(false);const timeLeft=ref(25*60);const focusMinutes=ref(25);const breakMinutes=ref(5);let timerInterval=null;let startedAt=null;let targetEndAt=null
const records=ref([]);const stats=reactive({today_focus:0,total_focus:0,today_count:0})
function formatTime(s){const m=Math.floor(s/60);const sec=s%60;return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`}
function tickTimer(){if(!targetEndAt)return;timeLeft.value=Math.max(0,Math.ceil((targetEndAt-Date.now())/1000));if(timeLeft.value<=0)completeSession()}
function startTick(minutes){clearInterval(timerInterval);targetEndAt=Date.now()+minutes*60*1000;tickTimer();timerInterval=setInterval(tickTimer,1000)}
function startFocus(){isRunning.value=true;isBreak.value=false;startedAt=new Date().toISOString();startTick(focusMinutes.value)}
function pauseFocus(){isRunning.value=false;clearInterval(timerInterval);targetEndAt=null}
async function completeSession(){clearInterval(timerInterval);targetEndAt=null;isRunning.value=false;const d=isBreak.value?breakMinutes.value:focusMinutes.value;const now=new Date().toISOString();try{await createFocusRecord({duration:d,focus_type:isBreak.value?'休息':'番茄钟',started_at:startedAt,ended_at:now});ElMessage.success(isBreak.value?'休息结束':'专注完成！');if(!isBreak.value){isBreak.value=true;isRunning.value=true;startedAt=now;startTick(breakMinutes.value)}else resetTimer()}catch{ElMessage.error('保存失败')}loadData()}
function resetTimer(){clearInterval(timerInterval);targetEndAt=null;isRunning.value=false;isBreak.value=false;timeLeft.value=focusMinutes.value*60}
async function loadData(){try{const[recRes,statsRes,chartsRes]=await Promise.all([getFocusRecords(),getFocusStats(),getFocusCharts()]);records.value=recRes.data||[];Object.assign(stats,statsRes.data||{});if(focusChartRef.value){if(!focusChart)focusChart=echarts.init(focusChartRef.value);focusChart.setOption({tooltip:{trigger:'axis'},grid:{left:10,right:20,top:10,bottom:20},xAxis:{type:'category',data:chartsRes.data.days},yAxis:{type:'value',name:'分钟'},series:[{data:chartsRes.data.durations,type:'bar',itemStyle:{color:'#1a73e8',borderRadius:[4,4,0,0]}}]})}}catch{}}
function resizeFocusChart(){focusChart?.resize()}
onMounted(()=>{loadData();window.addEventListener('resize',resizeFocusChart)})
onBeforeUnmount(()=>{clearInterval(timerInterval);window.removeEventListener('resize',resizeFocusChart);focusChart?.dispose()})
</script>

<style scoped>
.focus-grid{display:grid;grid-template-columns:360px 1fr;gap:16px}@media(max-width:900px){.focus-grid{grid-template-columns:1fr}}
.chart-card{background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 2px rgba(60,64,67,0.1),0 1px 3px rgba(60,64,67,0.08)}
.timer-card{text-align:center}.timer-circle{width:180px;height:180px;border-radius:50%;border:4px solid #e8eaed;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto 20px;transition:border-color 0.5s}
.timer-circle.running{border-color:#1a73e8;box-shadow:0 0 30px rgba(26,115,232,0.15)}
.timer-display{font-size:40px;font-weight:300;color:#202124}.timer-label{font-size:14px;color:#5f6368}
.timer-controls{display:flex;gap:12px;justify-content:center;margin-bottom:16px}
.timer-settings{display:flex;align-items:center;justify-content:center;gap:8px;font-size:13px;color:#5f6368}
.stat-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}.stat-mini{text-align:center}.sv{font-size:24px;font-weight:500;color:#202124;display:block}.sv small{font-size:13px;font-weight:400;color:#5f6368}.sl{font-size:12px;color:#5f6368}
.card-title{font-weight:500;color:#202124;margin-bottom:12px;font-size:15px}
</style>

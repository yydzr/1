<template>
  <div class="ai-page">
    <div class="ai-grid">
      <div class="ai-chat">
        <div class="chart-card chat-card">
          <div class="card-title">AI 助手</div>
          <div class="chat-msgs" ref="chatBox">
            <div v-for="(msg,i) in messages" :key="i" class="msg-row" :class="msg.role"><div class="msg-bubble">{{msg.content}}</div></div>
            <div v-if="chatLoading" class="msg-row ai"><div class="msg-bubble loading">思考中...</div></div>
          </div>
          <div class="chat-input-area">
            <el-input v-model="chatInput" placeholder="输入问题..." :rows="2" type="textarea" @keyup.enter.ctrl="sendMessage"/>
            <el-button type="primary" :loading="chatLoading" @click="sendMessage" style="margin-top:8px;width:100%">发送 (Ctrl+Enter)</el-button>
          </div>
        </div>
      </div>
      <div class="ai-side">
        <div class="chart-card">
          <div class="card-title">快捷功能</div>
          <el-button @click="dailyPlan" :loading="funcLoading" style="width:100%;margin-bottom:10px">生成每日计划</el-button>
          <el-button @click="taskAnalysis" :loading="funcLoading" style="width:100%;margin-bottom:10px">分析任务压力</el-button>
          <el-button @click="summaryToday" :loading="funcLoading" style="width:100%;margin-bottom:10px">总结今日任务</el-button>
          <div v-if="funcResult" class="func-result"><el-divider/>
            <div v-if="funcResult.plan"><h4>{{funcResult.plan.date}} {{funcResult.plan.day}}</h4><div v-for="(item,i) in funcResult.plan.schedule" :key="i" style="padding:4px 0;font-size:13px;color:#5f6368"><strong>{{item.time}}</strong> — {{item.task}}</div><el-alert type="info" :title="funcResult.plan.tips" :closable="false" style="margin-top:8px"/></div>
            <div v-else-if="funcResult.pressure"><el-alert :type="funcResult.pressure==='高'?'error':funcResult.pressure==='中'?'warning':'success'" :title="'压力: '+funcResult.pressure" :closable="false"/><p style="margin-top:8px;color:#5f6368">总: {{funcResult.total_todos}} | 未完成: {{funcResult.undone}} | 逾期: {{funcResult.overdue}}</p><p style="color:#5f6368">{{funcResult.advice}}</p></div>
            <div v-else-if="funcResult.summary"><el-alert type="info" :title="funcResult.summary.message" :closable="false"/><p style="margin-top:8px;font-size:13px;color:#5f6368">完成: {{funcResult.summary.completed_tasks}} | 待办: {{funcResult.summary.remaining_tasks}} | 笔记: {{funcResult.summary.notes_updated}}</p></div>
          </div>
        </div>
        <div class="chart-card" style="margin-top:16px"><div class="card-title">AI 历史</div>
          <div v-if="records.length" style="max-height:300px;overflow-y:auto"><div v-for="r in records" :key="r.id" class="hist-item"><el-tag size="small">{{r.ai_type}}</el-tag><span class="hist-prompt">{{r.prompt?.slice(0,40)}}</span><span class="hist-time">{{r.created_at?.slice(0,10)}}</span></div></div>
          <el-empty v-else description="暂无记录" :image-size="50"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref,nextTick,onMounted} from 'vue';import {aiChat,aiDailyPlan,aiTaskAnalysis,aiSummaryToday,getAiRecords} from '@/api/ai'
const messages=ref([{role:'ai',content:'你好！我是 AI 助手，有什么可以帮你的？'}])
const chatInput=ref('');const chatLoading=ref(false);const funcLoading=ref(false);const chatBox=ref(null);const funcResult=ref(null);const records=ref([])
async function sendMessage(){const text=chatInput.value.trim();if(!text)return;messages.value.push({role:'user',content:text});chatInput.value='';chatLoading.value=true;await scrollToBottom();try{const res=await aiChat(text);messages.value.push({role:'ai',content:res.data.reply||'收到'});loadRecords()}catch{}finally{chatLoading.value=false;await scrollToBottom()}}
async function scrollToBottom(){await nextTick();if(chatBox.value)chatBox.value.scrollTop=chatBox.value.scrollHeight}
async function handleFunc(fn){funcLoading.value=true;funcResult.value=null;try{const res=await fn();funcResult.value=res.data;loadRecords()}catch{}finally{funcLoading.value=false}}
function dailyPlan(){handleFunc(aiDailyPlan)};function taskAnalysis(){handleFunc(aiTaskAnalysis)};function summaryToday(){handleFunc(aiSummaryToday)}
async function loadRecords(){try{const res=await getAiRecords();records.value=(res.data||[]).slice(0,20)}catch{}}
onMounted(loadRecords)
</script>

<style scoped>
.ai-grid{display:grid;grid-template-columns:2fr 1fr;gap:16px}@media(max-width:992px){.ai-grid{grid-template-columns:1fr}}
.chart-card{background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 2px rgba(60,64,67,0.1),0 1px 3px rgba(60,64,67,0.08)}.card-title{font-weight:500;color:#202124;font-size:15px;margin-bottom:12px}
.chat-card{display:flex;flex-direction:column;height:calc(100vh - 160px)}.chat-msgs{flex:1;overflow-y:auto;padding:8px 0;min-height:200px}
.msg-row{display:flex;margin-bottom:12px}.msg-row.user{justify-content:flex-end}.msg-row.ai{justify-content:flex-start}
.msg-bubble{max-width:80%;padding:10px 16px;border-radius:16px;font-size:14px;line-height:1.6}.msg-row.user .msg-bubble{background:#e8f0fe;color:#202124;border-bottom-right-radius:4px}.msg-row.ai .msg-bubble{background:#f1f3f4;color:#202124;border-bottom-left-radius:4px}.loading{opacity:0.5}
.chat-input-area{padding-top:12px;border-top:1px solid #e8eaed}
.hist-item{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f1f3f4;font-size:12px}.hist-prompt{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#5f6368}.hist-time{color:#80868b;white-space:nowrap}
</style>

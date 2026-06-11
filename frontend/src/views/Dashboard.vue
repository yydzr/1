<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="card in statsCards" :key="card.label" class="stat-card">
        <div class="stat-strip" :style="{ background: card.color }"></div>
        <div class="stat-body">
          <span class="stat-value">{{ card.value }}</span>
          <span class="stat-label">{{ card.label }}</span>
        </div>
        <el-icon class="stat-icon" :size="28" :color="card.color">
          <component :is="card.icon" />
        </el-icon>
      </div>
    </div>

    <!-- 图表行 -->
    <div class="charts-row">
      <div class="chart-card chart-lg">
        <div class="chart-card-header">最近 7 天任务完成趋势</div>
        <div ref="trendChartRef" style="height:280px"></div>
      </div>
      <div class="chart-card chart-sm">
        <div class="chart-card-header">任务状态分布</div>
        <div ref="pieChartRef" style="height:280px"></div>
      </div>
    </div>

    <!-- 列表行 -->
    <div class="list-row">
      <div class="chart-card" v-for="list in listCards" :key="list.title">
        <div class="chart-card-header">{{ list.title }}</div>
        <div v-if="list.items && list.items.length">
          <div class="list-item" v-for="(item, i) in list.items" :key="i" @click="list.onClick ? list.onClick(item) : null">
            <span class="item-title">{{ item.title }}</span>
            <span class="item-extra">{{ item.extra }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无数据" :image-size="50" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getStats, getCharts } from '@/api/dashboard'
import { Document, List, Check, Clock, Warning, Calendar, Timer, Aim } from '@element-plus/icons-vue'

const router = useRouter()
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

const statsData = reactive({
  notes_count: 0, todos_total: 0, todos_done: 0, todos_undone: 0,
  todos_overdue: 0, today_schedules: 0, today_focus: 0, total_focus: 0,
  goals_count: 0, avg_progress: 0,
  recent_notes: [], today_todos: [], today_schedule_list: [],
})

const statsCards = ref([
  { label: '笔记总数', value: 0, icon: markRaw(Document), color: '#fbbc04' },
  { label: '待办总数', value: 0, icon: markRaw(List), color: '#1a73e8' },
  { label: '已完成', value: 0, icon: markRaw(Check), color: '#0f9d58' },
  { label: '未完成', value: 0, icon: markRaw(Clock), color: '#f4b400' },
  { label: '逾期任务', value: 0, icon: markRaw(Warning), color: '#ea4335' },
  { label: '今日日程', value: 0, icon: markRaw(Calendar), color: '#5f6368' },
  { label: '累计专注', value: '0m', icon: markRaw(Timer), color: '#1a73e8' },
  { label: '目标数量', value: 0, icon: markRaw(Aim), color: '#0f9d58' },
])

const listCards = computed(() => [
  {
    title: '最近更新笔记',
    items: (statsData.recent_notes || []).map(n => ({ title: n.title, extra: n.updated_at?.slice(0, 10) })),
    onClick: (item) => { const note = statsData.recent_notes.find(n => n.title === item.title); if (note) router.push(`/notes/${note.id}`) },
  },
  { title: '今日待办', items: (statsData.today_todos || []).map(t => ({ title: t.title, extra: t.status })) },
  { title: '今日日程', items: (statsData.today_schedule_list || []).map(s => ({ title: s.title, extra: `${s.start_time?.slice(11,16)} - ${s.end_time?.slice(11,16)}` })) },
])

async function loadData() {
  try {
    const [statsRes, chartsRes] = await Promise.all([getStats(), getCharts()])
    const d = statsRes.data; Object.assign(statsData, d)
    statsCards.value[0].value = d.notes_count || 0
    statsCards.value[1].value = d.todos_total || 0
    statsCards.value[2].value = d.todos_done || 0
    statsCards.value[3].value = d.todos_undone || 0
    statsCards.value[4].value = d.todos_overdue || 0
    statsCards.value[5].value = d.today_schedules || 0
    statsCards.value[6].value = (d.total_focus || 0) + 'm'
    statsCards.value[7].value = d.goals_count || 0

    if (trendChartRef.value) {
      trendChart = echarts.init(trendChartRef.value)
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 10, right: 20, top: 10, bottom: 20 },
        xAxis: { type: 'category', data: chartsRes.data.trend.days },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{ data: chartsRes.data.trend.completed, type: 'line', smooth: true, areaStyle: { color: 'rgba(26,115,232,0.1)' }, lineStyle: { color: '#1a73e8', width: 2 }, itemStyle: { color: '#1a73e8' } }],
      })
    }
    if (pieChartRef.value) {
      pieChart = echarts.init(pieChartRef.value)
      pieChart.setOption({
        tooltip: { trigger: 'item' }, legend: { bottom: 0 },
        series: [{ type: 'pie', radius: ['45%', '75%'], center: ['50%', '45%'], data: chartsRes.data.distribution }],
      })
    }
  } catch {}
}

function resizeCharts() {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(() => { loadData(); window.addEventListener('resize', resizeCharts) })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); trendChart?.dispose(); pieChart?.dispose() })
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; margin-bottom: 20px; }

.stat-card {
  background: #fff; border-radius: 8px; display: flex; align-items: center;
  padding: 16px 16px 16px 0; gap: 12px; cursor: pointer;
  box-shadow: 0 1px 2px rgba(60,64,67,0.1), 0 1px 3px rgba(60,64,67,0.08);
  transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 1px 3px rgba(60,64,67,0.15), 0 3px 6px rgba(60,64,67,0.1); }
.stat-strip { width: 4px; height: 44px; border-radius: 0 3px 3px 0; flex-shrink: 0; }
.stat-body { flex: 1; }
.stat-value { font-size: 24px; font-weight: 500; color: #202124; display: block; }
.stat-label { font-size: 12px; color: #5f6368; }
.stat-icon { flex-shrink: 0; opacity: 0.3; }

.charts-row { display: grid; grid-template-columns: 3fr 2fr; gap: 16px; margin-bottom: 20px; }
@media (max-width: 992px) { .charts-row { grid-template-columns: 1fr; } }

.chart-card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(60,64,67,0.1), 0 1px 3px rgba(60,64,67,0.08); }
.chart-card-header { font-size: 15px; font-weight: 500; color: #202124; margin-bottom: 12px; }

.list-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.list-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #e8eaed; cursor: pointer; }
.list-item:hover { background: #f8f9fa; margin: 0 -8px; padding: 10px 8px; border-radius: 4px; }
.list-item:last-child { border-bottom: none; }
.item-title { font-size: 14px; color: #202124; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-extra { font-size: 12px; color: #5f6368; white-space: nowrap; }
</style>

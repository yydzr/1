<template>
  <div class="achievements-page">
    <div class="summary-band">
      <div>
        <h2>成就系统</h2>
        <p>{{ summary.unlocked || 0 }} / {{ summary.total || 0 }} 已解锁</p>
      </div>
      <div class="summary-metrics">
        <div class="metric">
          <span>{{ summary.progress || 0 }}%</span>
          <small>完成度</small>
        </div>
        <div class="metric">
          <span>{{ summary.focus_streak || 0 }}</span>
          <small>连续专注天数</small>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="achievement-grid">
      <div
        v-for="item in achievements"
        :key="item.code"
        class="achievement-card"
        :class="{ unlocked: item.unlocked }"
      >
        <div class="achievement-icon">
          <el-icon :size="24"><Trophy v-if="item.unlocked" /><Lock v-else /></el-icon>
        </div>
        <div class="achievement-main">
          <div class="achievement-head">
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.description }}</span>
            </div>
            <el-tag :type="item.unlocked ? 'success' : 'info'" size="small" round>
              {{ item.category }}
            </el-tag>
          </div>
          <el-progress
            :percentage="item.progress"
            :status="item.unlocked ? 'success' : undefined"
            :stroke-width="8"
          />
          <div class="achievement-foot">
            <span>{{ item.value }} / {{ item.target }}</span>
            <span>{{ item.unlocked ? '已解锁' : '进行中' }}</span>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !achievements.length" description="暂无成就数据" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Lock, Trophy } from '@element-plus/icons-vue'
import { getAchievements } from '@/api/achievements'

const loading = ref(false)
const achievements = ref([])
const summary = reactive({
  total: 0,
  unlocked: 0,
  locked: 0,
  progress: 0,
  focus_streak: 0,
})

async function loadAchievements() {
  loading.value = true
  try {
    const res = await getAchievements()
    achievements.value = res.data?.items || []
    Object.assign(summary, res.data?.summary || {})
  } finally {
    loading.value = false
  }
}

onMounted(loadAchievements)
</script>

<style scoped>
.achievements-page{display:flex;flex-direction:column;gap:18px}
.summary-band{display:flex;justify-content:space-between;align-items:center;gap:18px;background:var(--color-surface);border:1px solid var(--color-border-light);border-radius:var(--radius-lg);padding:22px 24px;box-shadow:var(--shadow-sm)}
.summary-band h2{margin:0 0 6px;font-size:var(--text-2xl);color:var(--color-text-primary);letter-spacing:0}
.summary-band p{margin:0;color:var(--color-text-secondary)}
.summary-metrics{display:flex;gap:12px;flex-wrap:wrap}
.metric{min-width:120px;padding:14px 16px;border-radius:var(--radius-md);background:var(--color-surface-secondary);text-align:center}
.metric span{display:block;font-size:var(--text-2xl);font-weight:var(--font-semibold);color:var(--color-primary)}
.metric small{color:var(--color-text-tertiary)}
.achievement-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;min-height:220px}
.achievement-card{display:flex;gap:14px;background:var(--color-surface);border:1px solid var(--color-border-light);border-radius:var(--radius-md);padding:18px;box-shadow:var(--shadow-sm);opacity:.78}
.achievement-card.unlocked{opacity:1;border-color:rgba(15,157,88,.28);background:linear-gradient(180deg,#fff 0%,#f7fff9 100%)}
.achievement-icon{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;background:var(--color-surface-secondary);color:var(--color-text-tertiary)}
.achievement-card.unlocked .achievement-icon{background:#e6f4ea;color:#0f9d58}
.achievement-main{flex:1;min-width:0}
.achievement-head{display:flex;justify-content:space-between;gap:10px;margin-bottom:12px}
.achievement-head strong{display:block;color:var(--color-text-primary);font-size:var(--text-base);margin-bottom:4px}
.achievement-head span{display:block;color:var(--color-text-secondary);font-size:var(--text-xs);line-height:1.5}
.achievement-foot{display:flex;justify-content:space-between;margin-top:8px;color:var(--color-text-tertiary);font-size:var(--text-xs)}
@media(max-width:720px){.summary-band{align-items:flex-start;flex-direction:column}.summary-metrics{width:100%}.metric{flex:1}}
</style>

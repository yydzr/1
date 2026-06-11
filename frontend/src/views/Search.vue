<template>
  <div class="search-page">
    <div class="search-toolbar">
      <el-input
        v-model="keyword"
        :prefix-icon="SearchIcon"
        placeholder="搜索笔记、待办、日程、目标、收藏"
        clearable
        @keyup.enter="submitSearch"
        @clear="submitSearch"
      />
      <el-button type="primary" :icon="SearchIcon" @click="submitSearch">搜索</el-button>
    </div>

    <el-tabs v-model="activeType" @tab-change="changeType">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="笔记" name="notes" />
      <el-tab-pane label="待办" name="todos" />
      <el-tab-pane label="日程" name="schedules" />
      <el-tab-pane label="目标" name="goals" />
      <el-tab-pane label="收藏" name="collections" />
    </el-tabs>

    <div v-loading="loading" class="search-results">
      <div v-if="searched && total > 0" class="result-total">共找到 {{ total }} 条结果</div>
      <div v-for="group in visibleGroups" :key="group.key" class="result-section">
        <div class="section-head">
          <span>{{ group.label }}</span>
          <el-tag size="small" type="info" round>{{ group.total }}</el-tag>
        </div>
        <div class="result-list">
          <button
            v-for="item in group.items"
            :key="`${item.type}-${item.id}`"
            class="result-item"
            @click="openResult(item)"
          >
            <el-icon :size="20"><component :is="iconMap[item.type] || Document" /></el-icon>
            <div class="result-body">
              <div class="result-title">
                <strong>{{ item.title }}</strong>
                <el-tag size="small" round>{{ item.type_label }}</el-tag>
              </div>
              <p v-if="item.summary">{{ item.summary }}</p>
              <span v-if="item.meta">{{ item.meta }}</span>
            </div>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
      <el-empty
        v-if="searched && !loading && total === 0"
        description="没有找到匹配内容"
      />
      <el-empty
        v-if="!searched && !loading"
        description="请输入关键词开始搜索"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Aim, ArrowRight, Calendar, Collection, Document, List, Search as SearchIcon } from '@element-plus/icons-vue'
import { globalSearch } from '@/api/search'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const keyword = ref('')
const activeType = ref('all')
const searched = ref(false)
const total = ref(0)
const groups = ref([])
const iconMap = reactive({
  notes: Document,
  todos: List,
  schedules: Calendar,
  goals: Aim,
  collections: Collection,
})

const visibleGroups = computed(() => groups.value.filter(group => group.total > 0 || activeType.value !== 'all'))

function syncFromRoute() {
  keyword.value = route.query.q || ''
  activeType.value = route.query.type || 'all'
}

async function loadSearch() {
  syncFromRoute()
  if (!keyword.value.trim()) {
    groups.value = []
    total.value = 0
    searched.value = false
    return
  }
  loading.value = true
  searched.value = true
  try {
    const res = await globalSearch({
      q: keyword.value.trim(),
      type: activeType.value,
      limit: 8,
    })
    groups.value = res.data?.groups || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function submitSearch() {
  router.push({
    path: '/search',
    query: {
      q: keyword.value.trim(),
      type: activeType.value,
    },
  })
}

function changeType() {
  submitSearch()
}

function openResult(item) {
  router.push(item.path)
}

onMounted(loadSearch)
watch(() => route.query, loadSearch)
</script>

<style scoped>
.search-page{display:flex;flex-direction:column;gap:14px}
.search-toolbar{display:flex;gap:10px;background:var(--color-surface);border:1px solid var(--color-border-light);border-radius:var(--radius-lg);padding:16px;box-shadow:var(--shadow-sm)}
.search-results{min-height:260px}
.result-total{margin:4px 0 14px;color:var(--color-text-secondary);font-size:var(--text-sm)}
.result-section{margin-bottom:18px}
.section-head{display:flex;align-items:center;gap:8px;margin-bottom:10px;font-weight:var(--font-semibold);color:var(--color-text-primary)}
.result-list{display:flex;flex-direction:column;gap:8px}
.result-item{display:flex;align-items:center;gap:12px;width:100%;text-align:left;border:1px solid var(--color-border-light);background:var(--color-surface);border-radius:var(--radius-md);padding:14px 16px;cursor:pointer;transition:box-shadow var(--transition-fast),transform var(--transition-fast),border-color var(--transition-fast)}
.result-item:hover{border-color:var(--color-primary);box-shadow:var(--shadow-md);transform:translateY(-1px)}
.result-body{flex:1;min-width:0}
.result-title{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.result-title strong{color:var(--color-text-primary);font-size:var(--text-sm);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.result-body p{margin:0 0 4px;color:var(--color-text-secondary);font-size:var(--text-xs);line-height:1.5}
.result-body span{color:var(--color-text-tertiary);font-size:var(--text-xs)}
@media(max-width:640px){.search-toolbar{flex-direction:column}.result-title{align-items:flex-start;flex-direction:column}}
</style>

<template>
  <div class="note-detail" v-loading="loading">
    <div class="back-bar">
      <el-button link :icon="ArrowLeft" @click="$router.push('/notes')">返回笔记列表</el-button>
    </div>

    <div class="detail-card" v-if="note.id">
      <div class="detail-head">
        <h2>{{ note.title }}</h2>
        <div class="detail-tags">
          <el-tag v-if="note.is_top" size="small" effect="dark" round>置顶</el-tag>
          <el-tag v-if="note.is_favorite" type="warning" size="small" effect="dark" round>收藏</el-tag>
          <el-tag v-if="note.is_archived" size="small" round>已归档</el-tag>
        </div>
      </div>
      <div class="detail-meta">
        <span>分类: <el-tag size="small">{{ note.category }}</el-tag></span>
        <span v-if="note.tags">标签: <el-tag v-for="t in parseTags(note.tags)" :key="t" size="small" type="info" style="margin-left:4px;">{{ t }}</el-tag></span>
        <span>更新: {{ note.updated_at }}</span>
      </div>

      <el-divider />
      <div class="detail-content">{{ note.content || '暂无内容' }}</div>
      <el-divider />

      <div class="detail-actions">
        <el-button @click="toggleTopN(note)" :type="note.is_top ? 'warning' : ''">{{ note.is_top ? '取消置顶' : '置顶' }}</el-button>
        <el-button @click="toggleFavN(note)" :type="note.is_favorite ? 'warning' : ''">{{ note.is_favorite ? '取消收藏' : '收藏' }}</el-button>
        <el-button @click="toggleArchN(note)" :type="note.is_archived ? 'info' : ''">{{ note.is_archived ? '取消归档' : '归档' }}</el-button>
        <el-button type="primary" @click="openEdit">编辑</el-button>
        <el-button type="danger" @click="handleDelete">删除</el-button>
      </div>

      <el-divider />
      <div class="ai-section">
        <span class="ai-label">AI 功能</span>
        <el-button @click="aiGenSummary" :loading="aiLoading">AI 总结</el-button>
        <el-button @click="aiGenKeywords" :loading="aiLoading">AI 提取关键词</el-button>
      </div>
      <div v-if="aiResult" class="ai-result">
        <el-alert :title="aiResult" type="info" :closable="false" show-icon />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="编辑笔记" width="640px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category" style="width:200px"><el-option v-for="c in categories" :key="c" :label="c" :value="c" /></el-select></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getNote, updateNote, deleteNote, toggleTop, toggleFavorite, toggleArchive, aiSummary, aiKeywords } from '@/api/notes'

const route = useRoute(); const router = useRouter()
const note = ref({}); const loading = ref(false)
const dialogVisible = ref(false); const submitting = ref(false)
const aiLoading = ref(false); const aiResult = ref('')
const form = reactive({ title: '', content: '', category: '未分类' })
const categories = ['未分类', '工作', '学习', '生活', '技术', '读书', '其他']

function parseTags(tags) { if (typeof tags === 'string') { try { return JSON.parse(tags) } catch { return [tags] } } return tags || [] }
async function loadNote() { loading.value = true; try { const res = await getNote(route.params.id); note.value = res.data } finally { loading.value = false } }
function openEdit() { form.title = note.value.title; form.content = note.value.content; form.category = note.value.category; dialogVisible.value = true }
async function handleUpdate() { submitting.value = true; try { await updateNote(note.value.id, { title: form.title, content: form.content, category: form.category }); ElMessage.success('修改成功'); dialogVisible.value = false; loadNote() } finally { submitting.value = false } }
async function handleDelete() { try { await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' }); await deleteNote(note.value.id); ElMessage.success('删除成功'); router.push('/notes') } catch {} }
async function toggleTopN(n) { await toggleTop(n.id); loadNote() }
async function toggleFavN(n) { await toggleFavorite(n.id); loadNote() }
async function toggleArchN(n) { await toggleArchive(n.id); loadNote() }
async function aiGenSummary() { aiLoading.value = true; aiResult.value = ''; try { const res = await aiSummary(note.value.id); aiResult.value = 'AI 总结: ' + res.data.summary } finally { aiLoading.value = false } }
async function aiGenKeywords() { aiLoading.value = true; aiResult.value = ''; try { const res = await aiKeywords({ title: note.value.title, content: note.value.content }); aiResult.value = 'AI 关键词: ' + (res.data.keywords || []).join(', ') } finally { aiLoading.value = false } }
onMounted(loadNote)
</script>

<style scoped>
.back-bar { margin-bottom: 16px; }
.detail-card { background: #fff; border-radius: 8px; padding: 28px; box-shadow: 0 1px 2px rgba(60,64,67,0.1), 0 1px 3px rgba(60,64,67,0.08); }
.detail-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.detail-head h2 { font-size: 22px; font-weight: 500; color: #202124; }
.detail-tags { display: flex; gap: 6px; }
.detail-meta { display: flex; gap: 16px; flex-wrap: wrap; color: #5f6368; font-size: 13px; align-items: center; margin-top: 12px; }
.detail-content { min-height: 200px; line-height: 1.8; font-size: 15px; color: #202124; padding: 8px 0; white-space: pre-wrap; word-break: break-word; }
.detail-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.ai-section { display: flex; align-items: center; gap: 12px; }
.ai-label { color: #5f6368; font-size: 14px; }
.ai-result { margin-top: 12px; }
</style>

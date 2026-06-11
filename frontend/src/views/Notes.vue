<template>
  <div class="notes-page">
    <!-- 快速添加栏 -->
    <div class="quick-add" @click="openDialog()">
      <el-icon :size="20"><Plus /></el-icon>
      <span>写一篇新笔记...</span>
    </div>

    <!-- 搜索 + 筛选 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索笔记..." clearable :prefix-icon="Search" class="search-in" @input="searchNotes" />
      <el-select v-model="filterCategory" placeholder="分类" clearable @change="searchNotes" style="width:140px">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增笔记</el-button>
    </div>

    <!-- 笔记卡片网格 — Keep 风格 -->
    <div v-loading="loading">
      <div v-if="notes.length" class="notes-grid">
        <div v-for="note in notes" :key="note.id" class="note-card" :style="noteBg(note)" @click="goDetail(note.id)">
          <div class="note-head">
            <span class="note-title">{{ note.title }}</span>
            <el-tag v-if="note.is_top" size="small" effect="dark" round>置顶</el-tag>
          </div>
          <div class="note-body">
            {{ note.content?.slice(0, 150) || '暂无内容' }}
          </div>
          <div class="note-foot">
            <div class="note-tags">
              <span class="note-cat">{{ note.category }}</span>
            </div>
            <div class="note-acts" @click.stop>
              <el-button v-if="note.is_favorite" link :icon="StarFilled" style="color:#f4b400" @click="toggleFav(note)" />
              <el-button v-else link :icon="Star" @click="toggleFav(note)" />
              <el-button link :icon="Delete" @click="handleDelete(note)" />
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无笔记，点击上方开始写笔记吧" />
    </div>
    <div v-if="page.total > page.per_page" class="pager">
      <el-pagination background layout="prev, pager, next, total" :current-page="page.page" :page-size="page.per_page" :total="page.total" @current-change="changePage" />
    </div>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑笔记' : '新增笔记'" width="640px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="笔记标题" maxlength="200" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="笔记内容..." />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width:200px">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <div class="color-pick">
            <span v-for="cl in noteColors" :key="cl" class="color-dot" :style="{background:cl}" :class="{picked: form.noteColor === cl}" @click="form.noteColor = cl"></span>
          </div>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tagsStr" placeholder="用逗号分隔多个标签" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="isEdit" @click="aiClassifyNote" :loading="aiLoading">AI 分类</el-button>
        <el-button v-if="isEdit" @click="aiGenTitle" :loading="aiLoading">AI 标题</el-button>
        <el-button v-if="isEdit" @click="aiGenKeywords" :loading="aiLoading">AI 关键词</el-button>
        <el-button v-if="isEdit" @click="aiGenSummary" :loading="aiLoading">AI 总结</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Star, StarFilled, Delete } from '@element-plus/icons-vue'
import { getNotes, createNote, updateNote, deleteNote, toggleTop, toggleFavorite, aiSummary, aiClassify, aiKeywords, aiGenerateTitle } from '@/api/notes'

const router = useRouter()
const notes = ref([]); const loading = ref(false)
const keyword = ref(''); const filterCategory = ref('')
const dialogVisible = ref(false); const isEdit = ref(false)
const submitting = ref(false); const aiLoading = ref(false); const editId = ref(null)
const page = reactive({ page: 1, per_page: 12, total: 0 })
const form = reactive({ title: '', content: '', category: '未分类', tagsStr: '', noteColor: '#ffffff' })
const categories = ['未分类', '工作', '学习', '生活', '技术', '读书', '其他']
const noteColors = ['#ffffff', '#fef7e0', '#e6f4ea', '#e8f0fe', '#fce8e6', '#f3e8fd', '#e0f2f1']

function noteBg(note) {
  const color = note.note_color || '#ffffff'
  return { background: color, borderColor: color === '#ffffff' ? '#e8eaed' : 'transparent' }
}

async function loadNotes() {
  loading.value = true
  try {
    const res = await getNotes({ keyword: keyword.value, category: filterCategory.value, page: page.page, per_page: page.per_page, include_total: 1 })
    const data = res.data || {}
    notes.value = data.items || []
    page.total = data.total || 0
  } finally { loading.value = false }
}
function searchNotes() { page.page = 1; loadNotes() }
function changePage(p) { page.page = p; loadNotes() }

function openDialog(note) {
  if (note) {
    isEdit.value = true; editId.value = note.id
    form.title = note.title; form.content = note.content; form.category = note.category
    form.tagsStr = note.tags ? (typeof note.tags === 'string' ? JSON.parse(note.tags || '[]') : note.tags).join(',') : ''
    form.noteColor = note.note_color || '#ffffff'
  } else {
    isEdit.value = false; editId.value = null
    form.title = ''; form.content = ''; form.category = '未分类'; form.tagsStr = ''; form.noteColor = '#ffffff'
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.title.trim()) { ElMessage.warning('请输入标题'); return }
  const data = { title: form.title.trim(), content: form.content, category: form.category, tags: form.tagsStr ? form.tagsStr.split(',').map(s => s.trim()).filter(Boolean) : [], note_color: form.noteColor }
  submitting.value = true
  try {
    if (isEdit.value) { await updateNote(editId.value, data); ElMessage.success('修改成功') }
    else { await createNote(data); ElMessage.success('创建成功') }
    dialogVisible.value = false; loadNotes()
  } finally { submitting.value = false }
}

async function handleDelete(note) {
  try { await ElMessageBox.confirm(`确定删除 "${note.title}" 吗？`, '提示', { type: 'warning' }); await deleteNote(note.id); ElMessage.success('删除成功'); loadNotes() } catch {}
}
async function toggleFav(note) { await toggleFavorite(note.id); loadNotes() }
function goDetail(id) { router.push(`/notes/${id}`) }

async function aiGenSummary() { if (!editId.value) return; aiLoading.value = true; try { const res = await aiSummary(editId.value); ElMessage.success('AI 总结: ' + res.data.summary) } finally { aiLoading.value = false } }
async function aiClassifyNote() { if (!editId.value) return; aiLoading.value = true; try { const res = await aiClassify({ title: form.title, content: form.content }); form.category = res.data.category; ElMessage.success('AI 分类: ' + form.category) } finally { aiLoading.value = false } }
async function aiGenKeywords() { aiLoading.value = true; try { const res = await aiKeywords({ title: form.title, content: form.content }); if (res.data.keywords) { form.tagsStr = res.data.keywords.join(',') } ElMessage.success('AI 关键词已生成') } finally { aiLoading.value = false } }
async function aiGenTitle() { aiLoading.value = true; try { const res = await aiGenerateTitle({ content: form.content }); if (res.data.title) { form.title = res.data.title; ElMessage.success('AI 标题: ' + res.data.title) } } finally { aiLoading.value = false } }

onMounted(loadNotes)
</script>

<style scoped>
.quick-add {
  background: #fff; border-radius: 8px; padding: 14px 20px; display: flex; align-items: center; gap: 12px;
  color: #5f6368; font-size: 14px; cursor: pointer; margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(60,64,67,0.1), 0 1px 3px rgba(60,64,67,0.08);
}
.quick-add:hover { box-shadow: 0 1px 3px rgba(60,64,67,0.15), 0 3px 6px rgba(60,64,67,0.1); }

.toolbar { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }
.search-in { flex: 1; min-width: 200px; }
.pager { display: flex; justify-content: center; margin-top: 18px; }

.notes-grid { columns: 4 280px; gap: 14px; }
@media (max-width: 1200px) { .notes-grid { columns: 3 260px; } }
@media (max-width: 768px) { .notes-grid { columns: 2 240px; } }
@media (max-width: 500px) { .notes-grid { columns: 1; } }

.note-card {
  break-inside: avoid; margin-bottom: 14px; border-radius: 10px; padding: 16px;
  border: 1px solid #e8eaed; cursor: pointer;
  box-shadow: 0 1px 2px rgba(60,64,67,0.08);
  transition: box-shadow 0.2s, transform 0.2s;
}
.note-card:hover { box-shadow: 0 1px 3px rgba(60,64,67,0.15), 0 3px 6px rgba(60,64,67,0.1); transform: translateY(-1px); }

.note-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 6px; margin-bottom: 8px; }
.note-title { font-weight: 500; color: #202124; font-size: 15px; word-break: break-word; }
.note-body { color: #5f6368; font-size: 13px; line-height: 1.5; margin-bottom: 12px; word-break: break-word; white-space: pre-wrap; }
.note-foot { display: flex; justify-content: space-between; align-items: center; }
.note-cat { font-size: 11px; color: #5f6368; background: rgba(0,0,0,0.06); padding: 2px 8px; border-radius: 10px; }
.note-acts { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
.note-card:hover .note-acts { opacity: 1; }

.color-pick { display: flex; gap: 8px; }
.color-dot { width: 28px; height: 28px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; transition: transform 0.2s; }
.color-dot:hover { transform: scale(1.15); }
.color-dot.picked { border-color: #1a73e8; transform: scale(1.2); }
</style>

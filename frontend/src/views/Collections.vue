<template>
  <div class="col-page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索收藏..." clearable :prefix-icon="Search" class="search-in" @input="searchCollections"/>
      <el-select v-model="filterCat" placeholder="分类" clearable @change="searchCollections" style="width:160px">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c"/>
      </el-select>
      <div class="spacer"></div>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增收藏</el-button>
    </div>
    <div v-loading="loading">
      <div v-if="collections.length" class="col-grid">
        <div v-for="item in collections" :key="item.id" class="col-card">
          <div class="col-head"><span class="col-title">{{item.title}}</span><div class="col-acts"><el-button v-if="item.url" link :icon="Link" @click="openUrl(item.url)"/><el-button link :icon="Edit" @click="openDialog(item)"/><el-button link :icon="Delete" @click="handleDelete(item)"/></div></div>
          <p class="col-desc">{{item.description||'暂无简介'}}</p>
          <div class="col-meta"><el-tag size="small">{{item.category}}</el-tag><el-tag v-for="t in parseTags(item.tags)" :key="t" size="small" type="info" style="margin-left:4px">{{t}}</el-tag></div>
          <div class="col-foot"><span class="col-time">{{item.updated_at?.slice(0,10)}}</span><div><el-button size="small" @click="aiSummary(item)" :loading="aiLoading">AI 摘要</el-button><el-button size="small" @click="aiTags(item)" :loading="aiLoading">AI 标签</el-button></div></div>
        </div>
      </div>
      <el-empty v-else description="暂无收藏"/>
    </div>
    <div v-if="page.total > page.per_page" class="pager"><el-pagination background layout="prev, pager, next, total" :current-page="page.page" :page-size="page.per_page" :total="page.total" @current-change="changePage"/></div>
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑收藏':'新增收藏'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title"/></el-form-item>
        <el-form-item label="链接"><el-input v-model="form.url"/></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.description" type="textarea" :rows="3"/></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category" style="width:200px"><el-option v-for="c in categories" :key="c" :label="c" :value="c"/></el-select></el-form-item>
        <el-form-item label="标签"><el-input v-model="form.tagsStr" placeholder="逗号分隔"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button></template>
    </el-dialog>
    <el-dialog v-model="aiDialog" title="AI 结果" width="500px"><p>{{aiResult}}</p><template #footer><el-button @click="aiDialog=false">关闭</el-button></template></el-dialog>
  </div>
</template>

<script setup>
import {ref,reactive,onMounted} from 'vue';import {ElMessage,ElMessageBox} from 'element-plus';import {Plus,Edit,Delete,Link,Search} from '@element-plus/icons-vue'
import {getCollections,createCollection,updateCollection,deleteCollection,aiSummaryCollection,aiTagsCollection} from '@/api/collections'
const collections=ref([]);const loading=ref(false);const keyword=ref('');const filterCat=ref('');const dialogVisible=ref(false);const isEdit=ref(false);const submitting=ref(false);const editId=ref(null);const aiLoading=ref(false);const aiDialog=ref(false);const aiResult=ref('')
const page=reactive({page:1,per_page:12,total:0})
const form=reactive({title:'',url:'',description:'',category:'未分类',tagsStr:''})
const categories=['未分类','前端','后端','AI','工具','教程','文档','开源','其他']
function parseTags(tags){if(typeof tags==='string'){try{return JSON.parse(tags)}catch{return[tags]}}return tags||[]}
async function loadCollections(){loading.value=true;try{const res=await getCollections({keyword:keyword.value,category:filterCat.value,page:page.page,per_page:page.per_page,include_total:1});const data=res.data||{};collections.value=data.items||[];page.total=data.total||0}finally{loading.value=false}}
function searchCollections(){page.page=1;loadCollections()}
function changePage(p){page.page=p;loadCollections()}
function openDialog(item){if(item){isEdit.value=true;editId.value=item.id;form.title=item.title;form.url=item.url;form.description=item.description;form.category=item.category;form.tagsStr=(parseTags(item.tags)||[]).join(',')}else{isEdit.value=false;editId.value=null;form.title='';form.url='';form.description='';form.category='未分类';form.tagsStr=''}dialogVisible.value=true}
async function handleSubmit(){if(!form.title.trim()){ElMessage.warning('请输入标题');return}const data={title:form.title,url:form.url,description:form.description,category:form.category,tags:form.tagsStr?form.tagsStr.split(',').map(s=>s.trim()).filter(Boolean):[]};submitting.value=true;try{if(isEdit.value){await updateCollection(editId.value,data);ElMessage.success('修改成功')}else{await createCollection(data);ElMessage.success('创建成功')}dialogVisible.value=false;loadCollections()}finally{submitting.value=false}}
async function handleDelete(item){try{await ElMessageBox.confirm('确认删除？','提示',{type:'warning'});await deleteCollection(item.id);ElMessage.success('删除成功');loadCollections()}catch{}}
function openUrl(url){if(url)window.open(url,'_blank')}
async function aiSummary(item){aiLoading.value=true;try{const res=await aiSummaryCollection(item.id);aiResult.value=res.data.summary||'无内容';aiDialog.value=true}finally{aiLoading.value=false}}
async function aiTags(item){aiLoading.value=true;try{const res=await aiTagsCollection(item.id);aiResult.value='AI 标签: '+(res.data.tags||[]).join(', ');aiDialog.value=true}finally{aiLoading.value=false}}
onMounted(loadCollections)
</script>

<style scoped>
.toolbar{display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap}.search-in{flex:1;min-width:200px}.spacer{flex:1}.pager{display:flex;justify-content:center;margin-top:18px}
.col-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.col-card{background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 2px rgba(60,64,67,0.1),0 1px 3px rgba(60,64,67,0.08)}
.col-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.col-title{font-weight:500;color:#202124}.col-acts{display:flex;gap:2px}
.col-desc{color:#5f6368;font-size:13px;min-height:36px}
.col-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.col-foot{display:flex;justify-content:space-between;align-items:center;margin-top:14px}.col-time{font-size:12px;color:#80868b}
</style>

# AI 智能个人效率管理系统（优化版）

基于 Vue 3 + Flask + SQLAlchemy 的个人效率管理系统，包含笔记、待办、日程、番茄专注、目标、收藏和 AI 助手模块。

本优化版保留源项目功能，同时改进了安全性、配置一致性、接口健壮性和部分前端风险点。

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Pinia、Axios、Element Plus、ECharts
- 后端：Flask、Flask-SQLAlchemy、Flask-JWT-Extended、Flask-CORS、OpenAI SDK
- 数据库：默认 SQLite；也可通过 `DATABASE_URL` 切换 MySQL

## 目录结构

```text
ai-efficiency-system-optimized/
  backend/                 Flask 后端
    app.py                 应用入口
    config.py              配置和环境变量
    models.py              数据模型
    routes/                API 路由
    requirements.txt       Python 依赖
  frontend/                Vue 前端
    src/
      api/                 接口封装
      router/              路由
      stores/              Pinia 状态
      views/               页面
  database.sql             MySQL 初始化脚本
```

## 快速启动

### 1. 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

后端默认运行在 `http://127.0.0.1:5000`。

默认数据库是 `backend/ai_efficiency.db`。首次启动时会自动建表。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:3000`，Vite 会把 `/api` 代理到后端。

## 环境变量

开发环境可以直接启动。部署或正式演示时建议至少配置：

```bash
set SECRET_KEY=请替换为随机长字符串
set JWT_SECRET_KEY=请替换为随机长字符串
set CORS_ORIGINS=http://localhost:3000
set DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

如果要使用 MySQL：

```bash
set DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/ai_efficiency?charset=utf8mb4
```

然后执行：

```bash
mysql -u root -p < database.sql
```

## Cloudflare 方案 B 部署

推荐结构：

```text
app.yourdomain.com  -> Cloudflare Pages -> Vue 前端
api.yourdomain.com  -> Cloudflare Tunnel -> Flask 后端
```

### 1. 部署前端到 Cloudflare Pages

在 Cloudflare Pages 创建项目，配置：

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

Pages 环境变量：

```text
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

本项目已支持 `VITE_API_BASE_URL`。本地开发不设置该变量时，仍使用 Vite 的 `/api` 代理。

### 2. 启动 Flask 后端

后端所在机器设置生产环境变量，可参考：

```text
backend/.env.production.example
```

必须替换：

```text
SECRET_KEY
JWT_SECRET_KEY
CORS_ORIGINS=https://app.yourdomain.com,https://你的-pages项目.pages.dev
```

启动后端：

```bash
cd backend
venv\Scripts\activate
python app.py
```

### 3. 使用 Cloudflare Tunnel 暴露后端

登录 Cloudflare：

```bash
cloudflared tunnel login
```

创建 Tunnel：

```bash
cloudflared tunnel create ai-efficiency-api
```

绑定域名：

```bash
cloudflared tunnel route dns ai-efficiency-api api.yourdomain.com
```

配置文件可参考：

```text
deploy/cloudflared-api.example.yml
```

启动 Tunnel：

```bash
cloudflared tunnel run ai-efficiency-api
```

访问检查：

```text
https://api.yourdomain.com/api/health
https://app.yourdomain.com
```

## 主要优化点

- 修复“今日待办”日期过滤错误，避免把全部任务算作今日任务。
- 用户资料接口不再返回 AI API Key 明文，前端只显示脱敏状态。
- CORS 从全开放改为环境变量白名单。
- 生产环境缺少 `SECRET_KEY` / `JWT_SECRET_KEY` 时会拒绝启动。
- 移除启动时手写 `ALTER TABLE`，建表脚本与模型保持一致。
- 列表接口增加默认分页上限，避免一次性拉取过多数据。
- 前端笔记详情不再使用 `v-html` 渲染用户内容，降低 XSS 风险。
- 修复 ECharts resize 监听器无法卸载的问题。
- `localStorage` 用户信息解析失败时会自动清理，避免页面白屏。

## 建议继续增强

- 引入 Flask-Migrate 管理后续数据库迁移。
- 增加后端 pytest 接口测试和前端组件/端到端测试。
- 对用户自定义 AI API Key 做服务端加密存储。

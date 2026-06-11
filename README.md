# AI 智能个人效率管理系统（优化版）

基于 Vue 3 + Flask + SQLAlchemy 的个人效率管理系统，包含笔记、待办、日程、番茄专注、目标、收藏和 AI 助手模块。

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Pinia、Axios、Element Plus、ECharts
- 后端：Flask、Flask-SQLAlchemy、Flask-JWT-Extended、Flask-CORS、OpenAI SDK
- 数据库：默认 SQLite，也可通过 `DATABASE_URL` 切换 MySQL

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

## 本地启动

### 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

后端默认运行在 `http://127.0.0.1:5000`。

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:3000`，Vite 会把 `/api` 代理到后端。

## Cloudflare 部署

推荐结构：

```text
前端 -> Cloudflare Workers/Pages
后端 -> Flask 服务器或 Cloudflare Tunnel
```

当前仓库已包含 `wrangler.toml`，可用以下 Cloudflare 构建配置部署前端：

```text
Root directory: /
Build command: cd frontend && npm ci && npm run build
Deploy command: npx wrangler deploy
```

生产环境前端变量：

```text
VITE_API_BASE_URL=https://你的后端域名/api
```

后端生产环境变量可参考：

```text
backend/.env.production.example
```

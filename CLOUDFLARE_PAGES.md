# Cloudflare Pages 部署说明

本项目已改造成可以整体运行在 Cloudflare Pages 上：

- 前端：Vue/Vite，部署为 Pages 静态资源。
- 后端：`functions/api/[[path]].js`，部署为 Pages Functions。
- 数据库：Cloudflare D1，绑定名必须是 `DB`。

## 1. 登录 Cloudflare

```bash
npx wrangler login
```

## 2. 创建 D1 数据库

```bash
npx wrangler d1 create ai-efficiency-db
```

把命令输出里的 `database_id` 填到 `wrangler.toml`：

```toml
[[d1_databases]]
binding = "DB"
database_name = "ai-efficiency-db"
database_id = "你的 database_id"
```

## 3. 初始化数据库表

本地预览数据库：

```bash
npx wrangler d1 migrations apply ai-efficiency-db --local
```

线上生产数据库：

```bash
npx wrangler d1 migrations apply ai-efficiency-db --remote
```

## 4. 配置生产环境变量

至少设置两个密钥：

```bash
npx wrangler pages secret put SECRET_KEY --project-name ai-efficiency-system
npx wrangler pages secret put JWT_SECRET_KEY --project-name ai-efficiency-system
```

如果希望所有用户共用一个 DeepSeek Key，也可以设置：

```bash
npx wrangler pages secret put DEEPSEEK_API_KEY --project-name ai-efficiency-system
```

普通变量可在 Cloudflare Dashboard 的 Pages 项目里设置：

```text
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

如果不设置全局 `DEEPSEEK_API_KEY`，用户仍可在个人中心保存自己的 Key。

## 5. 构建并部署

```bash
cd frontend
npm ci
npm run build
cd ..
npx wrangler pages deploy frontend/dist --project-name ai-efficiency-system
```

部署后前端会通过同源 `/api` 调用 Pages Functions，不需要再配置 `VITE_API_BASE_URL` 或独立 Flask 后端。

## 6. 本地开发预览

```bash
cd frontend
npm ci
npm run build
cd ..
npx wrangler pages dev frontend/dist --d1 DB=ai-efficiency-db
```

打开 Wrangler 输出的本地地址，注册账号后即可测试笔记、待办、日程、目标、专注、收藏、搜索、成就和 AI 接口。

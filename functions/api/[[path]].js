const DEFAULT_JWT_SECRET = 'dev-only-jwt-secret-change-me'
const DEFAULT_SECRET = 'dev-only-flask-secret-change-me'
const API_KEY_NOT_SET_MSG = '请先在个人中心设置你的 DeepSeek API Key，获取地址: https://platform.deepseek.com/api_keys'

const jsonHeaders = {
  'content-type': 'application/json; charset=utf-8',
}

export async function onRequest(context) {
  const url = new URL(context.request.url)
  const path = url.pathname.replace(/^\/api\/?/, '')
  const parts = path.split('/').filter(Boolean)
  const method = context.request.method.toUpperCase()

  if (!context.env.DB) {
    return error('Cloudflare D1 数据库未绑定，请在 Pages 项目中绑定变量名 DB', 500)
  }

  try {
    if (method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders(context.request) })
    if (parts.length === 1 && parts[0] === 'health') return success(null, 'OK')

    if (parts[0] === 'auth') return handleAuth(context, parts.slice(1), method)

    const user = await requireUser(context)
    if (user instanceof Response) return user

    switch (parts[0]) {
      case 'notes':
        return handleNotes(context, user, parts.slice(1), method)
      case 'todos':
        return handleTodos(context, user, parts.slice(1), method)
      case 'schedules':
        return handleSchedules(context, user, parts.slice(1), method)
      case 'goals':
        return handleGoals(context, user, parts.slice(1), method)
      case 'focus':
        return handleFocus(context, user, parts.slice(1), method)
      case 'collections':
        return handleCollections(context, user, parts.slice(1), method)
      case 'dashboard':
        return handleDashboard(context, user, parts.slice(1), method)
      case 'ai':
        return handleAi(context, user, parts.slice(1), method)
      case 'achievements':
        return handleAchievements(context, user, method)
      case 'search':
        return handleSearch(context, user, method)
      default:
        return error('接口不存在', 404)
    }
  } catch (err) {
    console.error(err)
    return error(err?.message || '服务器内部错误', 500)
  }
}

function corsHeaders(request) {
  const origin = request.headers.get('origin') || '*'
  return {
    ...jsonHeaders,
    'access-control-allow-origin': origin,
    'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    'access-control-allow-headers': 'content-type,authorization',
    'access-control-allow-credentials': 'true',
  }
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: jsonHeaders,
  })
}

function success(data = null, message = 'success', code = 200) {
  return jsonResponse({ code, message, data }, code)
}

function error(message = 'error', code = 400, data = null) {
  return jsonResponse({ code, message, data }, code)
}

async function body(request) {
  if (!request.headers.get('content-type')?.includes('application/json')) return {}
  return (await request.json().catch(() => null)) || {}
}

function intParam(value, fallback = 0) {
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value) || 0))
}

function now() {
  return formatDateTime(new Date())
}

function formatDateTime(value) {
  if (!value) return ''
  const d = value instanceof Date ? value : new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function formatDate(value) {
  return formatDateTime(value).slice(0, 10)
}

function startOfToday() {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return formatDateTime(d)
}

function tomorrowOf(dateText) {
  const d = new Date(dateText.replace(' ', 'T'))
  d.setDate(d.getDate() + 1)
  return formatDateTime(d)
}

function weekRange() {
  const d = new Date()
  const day = d.getDay() || 7
  d.setDate(d.getDate() - day + 1)
  d.setHours(0, 0, 0, 0)
  const start = formatDateTime(d)
  d.setDate(d.getDate() + 7)
  return [start, formatDateTime(d)]
}

function parseDateTime(value) {
  if (!value) return null
  const text = String(value).trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text} 00:00:00`
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(text)) return `${text}:00`
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(text)) return text
  const d = new Date(text)
  return Number.isNaN(d.getTime()) ? null : formatDateTime(d)
}

function pageArgs(url, defaultPerPage = 100, maxPerPage = 200) {
  const page = Math.max(1, intParam(url.searchParams.get('page'), 1))
  const perPage = Math.min(maxPerPage, Math.max(1, intParam(url.searchParams.get('per_page'), defaultPerPage)))
  return { page, perPage, offset: (page - 1) * perPage }
}

function includeTotal(url) {
  return url.searchParams.get('include_total') === '1'
}

async function listResponse(context, baseSql, params, orderSql, mapper, defaultPerPage = 100) {
  const url = new URL(context.request.url)
  const { page, perPage, offset } = pageArgs(url, includeTotal(url) ? 12 : defaultPerPage, includeTotal(url) ? 100 : 200)
  const rows = await context.env.DB.prepare(`${baseSql} ${orderSql} LIMIT ? OFFSET ?`).bind(...params, perPage, offset).all()
  const items = (rows.results || []).map(mapper)
  if (!includeTotal(url)) return success(items)
  const countRow = await context.env.DB.prepare(`SELECT COUNT(*) AS total FROM (${baseSql})`).bind(...params).first()
  return success({ items, total: countRow?.total || 0, page, per_page: perPage })
}

function userToDict(user) {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    avatar: user.avatar || '',
    created_at: formatDateTime(user.created_at),
    updated_at: formatDateTime(user.updated_at),
  }
}

function noteToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    title: row.title,
    content: row.content || '',
    category: row.category || '未分类',
    tags: row.tags || '[]',
    is_top: !!row.is_top,
    is_favorite: !!row.is_favorite,
    is_archived: !!row.is_archived,
    note_color: row.note_color || '#ffffff',
    created_at: formatDateTime(row.created_at),
    updated_at: formatDateTime(row.updated_at),
  }
}

function todoToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    title: row.title,
    description: row.description || '',
    priority: row.priority || '中',
    status: row.status || '未完成',
    category: row.category || '默认',
    progress: row.progress || 0,
    due_date: row.due_date ? formatDateTime(row.due_date) : null,
    created_at: formatDateTime(row.created_at),
    updated_at: formatDateTime(row.updated_at),
  }
}

function scheduleToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    title: row.title,
    description: row.description || '',
    location: row.location || '',
    start_time: formatDateTime(row.start_time),
    end_time: formatDateTime(row.end_time),
    color: row.color || '#409EFF',
    created_at: formatDateTime(row.created_at),
    updated_at: formatDateTime(row.updated_at),
  }
}

function goalToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    title: row.title,
    description: row.description || '',
    progress: row.progress || 0,
    status: row.status || '进行中',
    start_date: row.start_date ? formatDate(row.start_date) : '',
    end_date: row.end_date ? formatDate(row.end_date) : '',
    created_at: formatDateTime(row.created_at),
    updated_at: formatDateTime(row.updated_at),
  }
}

function focusToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    duration: row.duration || 0,
    focus_type: row.focus_type || '番茄钟',
    started_at: row.started_at ? formatDateTime(row.started_at) : '',
    ended_at: row.ended_at ? formatDateTime(row.ended_at) : '',
    created_at: formatDateTime(row.created_at),
  }
}

function collectionToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    title: row.title,
    url: row.url || '',
    description: row.description || '',
    category: row.category || '未分类',
    tags: row.tags || '[]',
    created_at: formatDateTime(row.created_at),
    updated_at: formatDateTime(row.updated_at),
  }
}

function aiRecordToDict(row) {
  return {
    id: row.id,
    user_id: row.user_id,
    prompt: row.prompt || '',
    result: row.result || '',
    ai_type: row.ai_type || 'chat',
    created_at: formatDateTime(row.created_at),
  }
}

function textEncoder() {
  return new TextEncoder()
}

function base64url(bytes) {
  const raw = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)
  let str = ''
  for (const b of raw) str += String.fromCharCode(b)
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function fromBase64url(text) {
  const normalized = text.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
  return Uint8Array.from(atob(padded), (c) => c.charCodeAt(0))
}

async function hmacSign(data, secret) {
  const key = await crypto.subtle.importKey('raw', textEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  return base64url(await crypto.subtle.sign('HMAC', key, textEncoder().encode(data)))
}

async function createToken(userId, env) {
  const header = base64url(textEncoder().encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })))
  const payload = base64url(textEncoder().encode(JSON.stringify({
    sub: String(userId),
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60,
  })))
  const signingInput = `${header}.${payload}`
  return `${signingInput}.${await hmacSign(signingInput, env.JWT_SECRET_KEY || DEFAULT_JWT_SECRET)}`
}

async function verifyToken(token, env) {
  const [header, payload, signature] = token.split('.')
  if (!header || !payload || !signature) return null
  const expected = await hmacSign(`${header}.${payload}`, env.JWT_SECRET_KEY || DEFAULT_JWT_SECRET)
  if (expected !== signature) return null
  const parsed = JSON.parse(new TextDecoder().decode(fromBase64url(payload)))
  if (!parsed.sub || (parsed.exp && parsed.exp < Math.floor(Date.now() / 1000))) return null
  return parsed
}

async function requireUser(context) {
  const auth = context.request.headers.get('authorization') || ''
  const match = auth.match(/^Bearer\s+(.+)$/i)
  if (!match) return error('请先登录', 401)
  const payload = await verifyToken(match[1], context.env)
  if (!payload) return error('登录凭证无效', 401)
  const user = await context.env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(Number(payload.sub)).first()
  return user || error('用户不存在', 401)
}

async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const key = await crypto.subtle.importKey('raw', textEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' }, key, 256)
  return `pbkdf2$100000$${base64url(salt)}$${base64url(bits)}`
}

async function verifyPassword(password, stored) {
  const [scheme, iterText, saltText, hashText] = String(stored || '').split('$')
  if (scheme !== 'pbkdf2') return false
  const salt = fromBase64url(saltText)
  const key = await crypto.subtle.importKey('raw', textEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: Number(iterText), hash: 'SHA-256' }, key, 256)
  return base64url(bits) === hashText
}

async function aesKey(secret) {
  const digest = await crypto.subtle.digest('SHA-256', textEncoder().encode(secret || DEFAULT_SECRET))
  return crypto.subtle.importKey('raw', digest, 'AES-GCM', false, ['encrypt', 'decrypt'])
}

async function encryptSecret(value, env) {
  if (!value) return ''
  if (value.startsWith('enc:')) return value
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await aesKey(env.SECRET_KEY), textEncoder().encode(value))
  return `enc:${base64url(iv)}:${base64url(encrypted)}`
}

async function decryptSecret(value, env) {
  if (!value) return ''
  if (!value.startsWith('enc:')) return value
  const [, ivText, cipherText] = value.split(':')
  try {
    const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: fromBase64url(ivText) }, await aesKey(env.SECRET_KEY), fromBase64url(cipherText))
    return new TextDecoder().decode(decrypted)
  } catch {
    return ''
  }
}

async function getUserApiKey(context, user) {
  const key = await decryptSecret(user.ai_api_key || '', context.env)
  return key || context.env.DEEPSEEK_API_KEY || ''
}

function maskApiKey(key) {
  if (!key) return ''
  if (key.length <= 10) return '*'.repeat(key.length)
  return `${key.slice(0, 6)}...${key.slice(-4)}`
}

async function handleAuth(context, parts, method) {
  const db = context.env.DB
  if (parts[0] === 'register' && method === 'POST') {
    const data = await body(context.request)
    const username = String(data.username || '').trim()
    const email = String(data.email || '').trim()
    const password = String(data.password || '')
    if (!username || !email || !password) return error('用户名、邮箱和密码不能为空', 400)
    if (username.length < 3) return error('用户名至少 3 个字符', 400)
    if (password.length < 6) return error('密码至少 6 个字符', 400)
    if (await db.prepare('SELECT id FROM users WHERE username = ?').bind(username).first()) return error('用户名已存在', 400)
    if (await db.prepare('SELECT id FROM users WHERE email = ?').bind(email).first()) return error('邮箱已被注册', 400)
    const created = now()
    const result = await db.prepare('INSERT INTO users (username,email,password_hash,created_at,updated_at) VALUES (?,?,?,?,?)')
      .bind(username, email, await hashPassword(password), created, created).run()
    const user = await db.prepare('SELECT * FROM users WHERE id = ?').bind(result.meta.last_row_id).first()
    return success(userToDict(user), '注册成功')
  }

  if (parts[0] === 'login' && method === 'POST') {
    const data = await body(context.request)
    const username = String(data.username || '').trim()
    const password = String(data.password || '')
    if (!username || !password) return error('用户名/邮箱和密码不能为空', 400)
    const user = await db.prepare('SELECT * FROM users WHERE username = ? OR email = ?').bind(username, username).first()
    if (!user || !(await verifyPassword(password, user.password_hash))) return error('用户名/邮箱或密码错误', 401)
    return success({ access_token: await createToken(user.id, context.env), user: userToDict(user) }, '登录成功')
  }

  const user = await requireUser(context)
  if (user instanceof Response) return user

  if (parts[0] === 'profile' && method === 'GET') return success(userToDict(user))
  if (parts[0] === 'profile' && method === 'PUT') {
    const data = await body(context.request)
    const username = String(data.username || '').trim()
    const email = String(data.email || '').trim()
    const avatar = String(data.avatar || '').trim()
    if (username && username !== user.username && await db.prepare('SELECT id FROM users WHERE username = ?').bind(username).first()) return error('用户名已存在', 400)
    if (email && email !== user.email && await db.prepare('SELECT id FROM users WHERE email = ?').bind(email).first()) return error('邮箱已被注册', 400)
    await db.prepare('UPDATE users SET username = ?, email = ?, avatar = ?, updated_at = ? WHERE id = ?')
      .bind(username || user.username, email || user.email, avatar || user.avatar || '', now(), user.id).run()
    return success(userToDict(await db.prepare('SELECT * FROM users WHERE id = ?').bind(user.id).first()), '修改成功')
  }

  if (parts[0] === 'password' && method === 'PUT') {
    const data = await body(context.request)
    if (!data.old_password || !data.new_password) return error('旧密码和新密码不能为空', 400)
    if (!(await verifyPassword(String(data.old_password), user.password_hash))) return error('旧密码错误', 400)
    if (String(data.new_password).length < 6) return error('新密码至少 6 个字符', 400)
    await db.prepare('UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?').bind(await hashPassword(String(data.new_password)), now(), user.id).run()
    return success(null, '密码修改成功')
  }

  if (parts[0] === 'ai-key' && method === 'GET') {
    const key = await decryptSecret(user.ai_api_key || '', context.env)
    return success({ has_ai_api_key: !!key, masked_ai_api_key: maskApiKey(key) })
  }
  if (parts[0] === 'ai-key' && method === 'PUT') {
    const data = await body(context.request)
    const key = String(data.ai_api_key || '').trim()
    await db.prepare('UPDATE users SET ai_api_key = ?, updated_at = ? WHERE id = ?').bind(await encryptSecret(key, context.env), now(), user.id).run()
    return success({ has_ai_api_key: !!key, masked_ai_api_key: maskApiKey(key) }, 'API Key 保存成功')
  }

  return error('接口不存在', 404)
}

async function getOwned(db, table, id, userId) {
  return db.prepare(`SELECT * FROM ${table} WHERE id = ? AND user_id = ?`).bind(id, userId).first()
}

async function handleNotes(context, user, parts, method) {
  const db = context.env.DB
  const url = new URL(context.request.url)
  if (parts.length === 0 && method === 'GET') {
    const where = ['user_id = ?']
    const params = [user.id]
    if (url.searchParams.get('keyword')) {
      where.push('(title LIKE ? OR content LIKE ?)')
      params.push(`%${url.searchParams.get('keyword').trim()}%`, `%${url.searchParams.get('keyword').trim()}%`)
    }
    if (url.searchParams.get('category')) {
      where.push('category = ?')
      params.push(url.searchParams.get('category').trim())
    }
    return listResponse(context, `SELECT * FROM notes WHERE ${where.join(' AND ')}`, params, 'ORDER BY is_top DESC, updated_at DESC', noteToDict)
  }
  if (parts.length === 0 && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    if (!title) return error('笔记标题不能为空', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO notes (user_id,title,content,category,tags,is_top,is_favorite,is_archived,note_color,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(user.id, title, data.content || '', data.category || '未分类', JSON.stringify(data.tags || []), data.is_top ? 1 : 0, data.is_favorite ? 1 : 0, 0, data.note_color || '#ffffff', ts, ts).run()
    return success(noteToDict(await db.prepare('SELECT * FROM notes WHERE id = ?').bind(result.meta.last_row_id).first()), '创建成功')
  }
  if (parts[0] === 'classify' && method === 'POST') return aiJsonWithFallback(context, user, await body(context.request), 'category', { category: '其他' }, '分类完成')
  if (parts[0] === 'keywords' && method === 'POST') return aiJsonWithFallback(context, user, await body(context.request), 'keywords', { keywords: ['通用'] }, '提取完成')
  if (parts[0] === 'generate-title' && method === 'POST') {
    const data = await body(context.request)
    return aiJsonWithFallback(context, user, data, 'title', { title: String(data.content || '').slice(0, 30) }, '标题生成完成')
  }

  const id = intParam(parts[0])
  const note = await getOwned(db, 'notes', id, user.id)
  if (!note) return error('笔记不存在', 404)
  if (parts.length === 1 && method === 'GET') return success(noteToDict(note))
  if (parts.length === 1 && method === 'DELETE') {
    await db.prepare('DELETE FROM notes WHERE id = ? AND user_id = ?').bind(id, user.id).run()
    return success(null, '删除成功')
  }
  if (parts.length === 1 && method === 'PUT') {
    const data = await body(context.request)
    await db.prepare(`UPDATE notes SET title=?,content=?,category=?,tags=?,is_top=?,is_favorite=?,is_archived=?,note_color=?,updated_at=? WHERE id=? AND user_id=?`)
      .bind(
        data.title !== undefined ? String(data.title).trim() : note.title,
        data.content !== undefined ? data.content : note.content || '',
        data.category !== undefined ? data.category : note.category || '未分类',
        data.tags !== undefined ? JSON.stringify(data.tags) : note.tags || '[]',
        data.is_top !== undefined ? (data.is_top ? 1 : 0) : note.is_top,
        data.is_favorite !== undefined ? (data.is_favorite ? 1 : 0) : note.is_favorite,
        data.is_archived !== undefined ? (data.is_archived ? 1 : 0) : note.is_archived,
        data.note_color !== undefined ? data.note_color : note.note_color || '#ffffff',
        now(), id, user.id,
      ).run()
    return success(noteToDict(await getOwned(db, 'notes', id, user.id)), '修改成功')
  }
  if (parts[1] === 'top' && method === 'PATCH') return toggleColumn(db, 'notes', id, user.id, 'is_top', noteToDict)
  if (parts[1] === 'favorite' && method === 'PATCH') return toggleColumn(db, 'notes', id, user.id, 'is_favorite', noteToDict)
  if (parts[1] === 'archive' && method === 'PATCH') return toggleColumn(db, 'notes', id, user.id, 'is_archived', noteToDict)
  if (parts[1] === 'summary' && method === 'POST') {
    if (!String(note.content || '').trim()) return success({ summary: '内容为空，无法总结', note_id: id })
    const summary = await chatText(context, user, `请用1-3句话总结以下笔记内容，提取核心要点：\n\n${note.content}`, '你是专业的笔记总结助手，简洁精准地提炼核心信息。', String(note.content || '').slice(0, 100))
    return success({ summary, note_id: id }, 'AI 总结完成')
  }
  return error('接口不存在', 404)
}

async function toggleColumn(db, table, id, userId, column, mapper) {
  const row = await getOwned(db, table, id, userId)
  await db.prepare(`UPDATE ${table} SET ${column} = ?, updated_at = ? WHERE id = ? AND user_id = ?`).bind(row[column] ? 0 : 1, now(), id, userId).run()
  return success(mapper(await getOwned(db, table, id, userId)), '操作成功')
}

async function handleTodos(context, user, parts, method) {
  const db = context.env.DB
  const url = new URL(context.request.url)
  if (parts[0] === 'today' && method === 'GET') return datedTodos(db, user.id, startOfToday(), tomorrowOf(startOfToday()), false)
  if (parts[0] === 'overdue' && method === 'GET') return datedTodos(db, user.id, null, startOfToday(), true)
  if (parts[0] === 'ai-generate' && method === 'POST') {
    const data = await body(context.request)
    const prompt = String(data.prompt || '').trim()
    if (!prompt) return error('请输入描述', 400)
    const fallback = { title: prompt, description: '', priority: '中', category: 'AI 生成', progress: 0 }
    return aiJsonWithFallback(context, user, data, 'todo', fallback, 'AI 生成完成')
  }
  if (parts[0] === 'ai-split' && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    if (!title) return error('请提供任务标题', 400)
    return aiJsonWithFallback(context, user, data, 'subtasks', { subtasks: [1, 2, 3].map((i) => ({ title: `${title} - 步骤${i}`, priority: '中' })) }, '拆分完成')
  }
  if (parts[0] === 'ai-priority' && method === 'POST') return aiJsonWithFallback(context, user, await body(context.request), 'priority', { priority: '中' }, '推荐完成')

  if (parts.length === 0 && method === 'GET') {
    const where = ['user_id = ?']
    const params = [user.id]
    for (const key of ['status', 'priority', 'category']) {
      const value = url.searchParams.get(key)?.trim()
      if (value) {
        where.push(`${key} = ?`)
        params.push(value)
      }
    }
    return listResponse(context, `SELECT * FROM todos WHERE ${where.join(' AND ')}`, params, 'ORDER BY priority DESC, due_date ASC, created_at DESC', todoToDict)
  }
  if (parts.length === 0 && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    if (!title) return error('待办标题不能为空', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO todos (user_id,title,description,priority,status,category,progress,due_date,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?)`).bind(user.id, title, data.description || '', data.priority || '中', data.status || '未完成', data.category || '默认', data.progress || 0, parseDateTime(data.due_date), ts, ts).run()
    return success(todoToDict(await db.prepare('SELECT * FROM todos WHERE id = ?').bind(result.meta.last_row_id).first()), '创建成功')
  }

  const id = intParam(parts[0])
  const todo = await getOwned(db, 'todos', id, user.id)
  if (!todo) return error('待办不存在', 404)
  if (parts.length === 1 && method === 'GET') return success(todoToDict(todo))
  if (parts.length === 1 && method === 'DELETE') {
    await db.prepare('DELETE FROM todos WHERE id = ? AND user_id = ?').bind(id, user.id).run()
    return success(null, '删除成功')
  }
  if (parts.length === 1 && method === 'PUT') {
    const data = await body(context.request)
    await db.prepare(`UPDATE todos SET title=?,description=?,priority=?,status=?,category=?,progress=?,due_date=?,updated_at=? WHERE id=? AND user_id=?`)
      .bind(data.title !== undefined ? String(data.title).trim() : todo.title, data.description ?? todo.description, data.priority ?? todo.priority, data.status ?? todo.status, data.category ?? todo.category, data.progress ?? todo.progress, data.due_date !== undefined ? parseDateTime(data.due_date) : todo.due_date, now(), id, user.id).run()
    return success(todoToDict(await getOwned(db, 'todos', id, user.id)), '修改成功')
  }
  if (parts[1] === 'toggle' && method === 'PATCH') {
    const done = todo.status === '已完成'
    await db.prepare('UPDATE todos SET status=?, progress=?, updated_at=? WHERE id=? AND user_id=?').bind(done ? '未完成' : '已完成', done ? 0 : 100, now(), id, user.id).run()
    return success(todoToDict(await getOwned(db, 'todos', id, user.id)), '操作成功')
  }
  if (parts[1] === 'progress' && method === 'PATCH') {
    const data = await body(context.request)
    const progress = clamp(data.progress, 0, 100)
    await db.prepare('UPDATE todos SET progress=?, status=?, updated_at=? WHERE id=? AND user_id=?').bind(progress, progress >= 100 ? '已完成' : todo.status, now(), id, user.id).run()
    return success(todoToDict(await getOwned(db, 'todos', id, user.id)), '进度更新成功')
  }
  return error('接口不存在', 404)
}

async function datedTodos(db, userId, start, end, overdue) {
  const sql = overdue
    ? `SELECT * FROM todos WHERE user_id=? AND status='未完成' AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC`
    : `SELECT * FROM todos WHERE user_id=? AND status='未完成' AND due_date IS NOT NULL AND due_date >= ? AND due_date < ? ORDER BY priority DESC, created_at DESC`
  const rows = overdue ? await db.prepare(sql).bind(userId, end).all() : await db.prepare(sql).bind(userId, start, end).all()
  return success((rows.results || []).map(todoToDict))
}

async function handleSchedules(context, user, parts, method) {
  const db = context.env.DB
  const url = new URL(context.request.url)
  if (parts[0] === 'dates' && method === 'GET') {
    const rows = await db.prepare('SELECT start_time,end_time FROM schedules WHERE user_id=?').bind(user.id).all()
    const starts = new Set()
    const ends = new Set()
    for (const row of rows.results || []) {
      if (row.start_time) starts.add(formatDate(row.start_time))
      if (row.end_time && formatDate(row.end_time) !== formatDate(row.start_time)) ends.add(formatDate(row.end_time))
    }
    return success({ starts: [...starts].sort(), ends: [...ends].sort() })
  }
  if (parts[0] === 'today' && method === 'GET') return rangeSchedules(db, user.id, startOfToday(), tomorrowOf(startOfToday()))
  if (parts[0] === 'week' && method === 'GET') return rangeSchedules(db, user.id, ...weekRange())
  if (parts.length === 0 && method === 'GET') {
    const date = url.searchParams.get('date')
    if (date) return rangeSchedules(db, user.id, `${date} 00:00:00`, tomorrowOf(`${date} 00:00:00`))
    return listResponse(context, 'SELECT * FROM schedules WHERE user_id=?', [user.id], 'ORDER BY start_time ASC', scheduleToDict)
  }
  if (parts.length === 0 && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    const start = parseDateTime(data.start_time)
    const end = parseDateTime(data.end_time)
    if (!title) return error('日程标题不能为空', 400)
    if (!start || !end) return error('开始时间和结束时间不能为空', 400)
    if (end <= start) return error('结束时间必须晚于开始时间', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO schedules (user_id,title,description,location,start_time,end_time,color,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?)`).bind(user.id, title, data.description || '', data.location || '', start, end, data.color || '#409EFF', ts, ts).run()
    return success(scheduleToDict(await db.prepare('SELECT * FROM schedules WHERE id=?').bind(result.meta.last_row_id).first()), '创建成功')
  }
  const id = intParam(parts[0])
  const schedule = await getOwned(db, 'schedules', id, user.id)
  if (!schedule) return error('日程不存在', 404)
  if (method === 'GET') return success(scheduleToDict(schedule))
  if (method === 'DELETE') {
    await db.prepare('DELETE FROM schedules WHERE id=? AND user_id=?').bind(id, user.id).run()
    return success(null, '删除成功')
  }
  if (method === 'PUT') {
    const data = await body(context.request)
    const start = data.start_time !== undefined ? parseDateTime(data.start_time) : schedule.start_time
    const end = data.end_time !== undefined ? parseDateTime(data.end_time) : schedule.end_time
    if (end <= start) return error('结束时间必须晚于开始时间', 400)
    await db.prepare(`UPDATE schedules SET title=?,description=?,location=?,start_time=?,end_time=?,color=?,updated_at=? WHERE id=? AND user_id=?`)
      .bind(data.title !== undefined ? String(data.title).trim() : schedule.title, data.description ?? schedule.description, data.location ?? schedule.location, start, end, data.color ?? schedule.color, now(), id, user.id).run()
    return success(scheduleToDict(await getOwned(db, 'schedules', id, user.id)), '修改成功')
  }
  return error('接口不存在', 404)
}

async function rangeSchedules(db, userId, start, end) {
  const rows = await db.prepare('SELECT * FROM schedules WHERE user_id=? AND start_time >= ? AND start_time < ? ORDER BY start_time ASC').bind(userId, start, end).all()
  return success((rows.results || []).map(scheduleToDict))
}

async function handleGoals(context, user, parts, method) {
  const db = context.env.DB
  const url = new URL(context.request.url)
  if (parts.length === 0 && method === 'GET') {
    const status = url.searchParams.get('status')?.trim()
    const sql = status ? 'SELECT * FROM goals WHERE user_id=? AND status=?' : 'SELECT * FROM goals WHERE user_id=?'
    return listResponse(context, sql, status ? [user.id, status] : [user.id], 'ORDER BY progress ASC, end_date ASC', goalToDict)
  }
  if (parts.length === 0 && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    if (!title) return error('目标标题不能为空', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO goals (user_id,title,description,progress,status,start_date,end_date,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?)`).bind(user.id, title, data.description || '', data.progress || 0, data.status || '进行中', parseDateTime(data.start_date), parseDateTime(data.end_date), ts, ts).run()
    return success(goalToDict(await db.prepare('SELECT * FROM goals WHERE id=?').bind(result.meta.last_row_id).first()), '创建成功')
  }
  const id = intParam(parts[0])
  const goal = await getOwned(db, 'goals', id, user.id)
  if (!goal) return error('目标不存在', 404)
  if (parts[1] === 'ai-plan' && method === 'POST') {
    const fallback = { phases: [{ phase: '准备阶段', tasks: ['明确需求', '收集资料', '制定计划'] }, { phase: '执行阶段', tasks: ['推进任务', '跟踪进度', '调整偏差'] }, { phase: '验收阶段', tasks: ['检查质量', '总结经验', '迭代优化'] }] }
    const data = await chatJson(context, user, `为以下目标制定一个分阶段执行计划，返回JSON：{"phases":[{"phase":"","tasks":[""]}]}\n目标：${goal.title}\n描述：${goal.description || '无'}\n进度：${goal.progress}%`, '你是目标规划专家，帮助用户制定可执行的阶段性计划。只返回JSON。', fallback)
    return success({ goal_title: goal.title, plan: data.phases || fallback.phases }, '计划生成完成')
  }
  if (method === 'GET') return success(goalToDict(goal))
  if (method === 'DELETE') {
    await db.prepare('DELETE FROM goals WHERE id=? AND user_id=?').bind(id, user.id).run()
    return success(null, '删除成功')
  }
  if (method === 'PUT' || (parts[1] === 'progress' && method === 'PATCH')) {
    const data = await body(context.request)
    const progress = data.progress !== undefined ? clamp(data.progress, 0, 100) : goal.progress
    await db.prepare(`UPDATE goals SET title=?,description=?,progress=?,status=?,start_date=?,end_date=?,updated_at=? WHERE id=? AND user_id=?`)
      .bind(data.title !== undefined ? String(data.title).trim() : goal.title, data.description ?? goal.description, progress, progress >= 100 ? '已完成' : (data.status ?? goal.status), data.start_date !== undefined ? parseDateTime(data.start_date) : goal.start_date, data.end_date !== undefined ? parseDateTime(data.end_date) : goal.end_date, now(), id, user.id).run()
    return success(goalToDict(await getOwned(db, 'goals', id, user.id)), method === 'PATCH' ? '进度更新成功' : '修改成功')
  }
  return error('接口不存在', 404)
}

async function handleFocus(context, user, parts, method) {
  const db = context.env.DB
  if (parts[0] === 'records' && method === 'GET') {
    const rows = await db.prepare('SELECT * FROM focus_records WHERE user_id=? ORDER BY created_at DESC LIMIT 100').bind(user.id).all()
    return success((rows.results || []).map(focusToDict))
  }
  if (parts[0] === 'records' && method === 'POST') {
    const data = await body(context.request)
    const duration = Number(data.duration || 0)
    if (duration <= 0) return error('专注时长必须大于 0', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO focus_records (user_id,duration,focus_type,started_at,ended_at,created_at)
      VALUES (?,?,?,?,?,?)`).bind(user.id, duration, data.focus_type || '番茄钟', parseDateTime(data.started_at), parseDateTime(data.ended_at) || ts, ts).run()
    return success(focusToDict(await db.prepare('SELECT * FROM focus_records WHERE id=?').bind(result.meta.last_row_id).first()), '保存成功')
  }
  if (parts[0] === 'stats' && method === 'GET') {
    const today = startOfToday()
    const tomorrow = tomorrowOf(today)
    const stats = await focusStats(db, user.id, today, tomorrow)
    return success(stats)
  }
  if (parts[0] === 'charts' && method === 'GET') {
    const days = []
    const durations = []
    for (let i = 6; i >= 0; i -= 1) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      d.setHours(0, 0, 0, 0)
      const start = formatDateTime(d)
      const label = formatDate(start).slice(5)
      const total = await db.prepare('SELECT COALESCE(SUM(duration),0) AS total FROM focus_records WHERE user_id=? AND created_at>=? AND created_at<?').bind(user.id, start, tomorrowOf(start)).first()
      days.push(label)
      durations.push(total?.total || 0)
    }
    return success({ days, durations })
  }
  return error('接口不存在', 404)
}

async function focusStats(db, userId, today, tomorrow) {
  const todayFocus = await db.prepare('SELECT COALESCE(SUM(duration),0) AS total FROM focus_records WHERE user_id=? AND created_at>=? AND created_at<?').bind(userId, today, tomorrow).first()
  const totalFocus = await db.prepare('SELECT COALESCE(SUM(duration),0) AS total FROM focus_records WHERE user_id=?').bind(userId).first()
  const todayCount = await db.prepare('SELECT COUNT(*) AS total FROM focus_records WHERE user_id=? AND created_at>=? AND created_at<?').bind(userId, today, tomorrow).first()
  return { today_focus: todayFocus?.total || 0, total_focus: totalFocus?.total || 0, today_count: todayCount?.total || 0 }
}

async function handleCollections(context, user, parts, method) {
  const db = context.env.DB
  const url = new URL(context.request.url)
  if (parts.length === 0 && method === 'GET') {
    const where = ['user_id = ?']
    const params = [user.id]
    if (url.searchParams.get('keyword')) {
      where.push('(title LIKE ? OR description LIKE ?)')
      params.push(`%${url.searchParams.get('keyword').trim()}%`, `%${url.searchParams.get('keyword').trim()}%`)
    }
    if (url.searchParams.get('category')) {
      where.push('category = ?')
      params.push(url.searchParams.get('category').trim())
    }
    return listResponse(context, `SELECT * FROM collections WHERE ${where.join(' AND ')}`, params, 'ORDER BY updated_at DESC', collectionToDict)
  }
  if (parts.length === 0 && method === 'POST') {
    const data = await body(context.request)
    const title = String(data.title || '').trim()
    if (!title) return error('收藏标题不能为空', 400)
    const ts = now()
    const result = await db.prepare(`INSERT INTO collections (user_id,title,url,description,category,tags,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?)`).bind(user.id, title, data.url || '', data.description || '', data.category || '未分类', JSON.stringify(data.tags || []), ts, ts).run()
    return success(collectionToDict(await db.prepare('SELECT * FROM collections WHERE id=?').bind(result.meta.last_row_id).first()), '创建成功')
  }
  const id = intParam(parts[0])
  const item = await getOwned(db, 'collections', id, user.id)
  if (!item) return error('收藏不存在', 404)
  if (parts[1] === 'ai-summary' && method === 'POST') {
    const summary = await chatText(context, user, `请用1-2句话概括以下收藏内容的核心价值：\n${item.title}\n${item.description || ''}`, '你是信息摘要专家，简洁精准地概括内容。', (item.description || item.title).slice(0, 80))
    return success({ summary }, '摘要生成完成')
  }
  if (parts[1] === 'ai-tags' && method === 'POST') {
    const result = await chatJson(context, user, `为以下收藏内容生成3-5个标签，返回JSON：{"tags":[""]}\n${item.title} ${item.description || ''}`, '你是标签生成专家，只返回JSON。标签应简洁准确。', { tags: ['通用'] })
    return success({ tags: result.tags || ['通用'] }, '标签生成完成')
  }
  if (method === 'GET') return success(collectionToDict(item))
  if (method === 'DELETE') {
    await db.prepare('DELETE FROM collections WHERE id=? AND user_id=?').bind(id, user.id).run()
    return success(null, '删除成功')
  }
  if (method === 'PUT') {
    const data = await body(context.request)
    await db.prepare(`UPDATE collections SET title=?,url=?,description=?,category=?,tags=?,updated_at=? WHERE id=? AND user_id=?`)
      .bind(data.title !== undefined ? String(data.title).trim() : item.title, data.url ?? item.url, data.description ?? item.description, data.category ?? item.category, data.tags !== undefined ? JSON.stringify(data.tags) : item.tags, now(), id, user.id).run()
    return success(collectionToDict(await getOwned(db, 'collections', id, user.id)), '修改成功')
  }
  return error('接口不存在', 404)
}

async function handleDashboard(context, user, parts, method) {
  if (method !== 'GET') return error('接口不存在', 404)
  const db = context.env.DB
  const today = startOfToday()
  const tomorrow = tomorrowOf(today)
  if (parts[0] === 'stats') {
    const counts = await Promise.all([
      count(db, 'notes', 'user_id=? AND is_archived=0', [user.id]),
      count(db, 'todos', 'user_id=?', [user.id]),
      count(db, 'todos', "user_id=? AND status='已完成'", [user.id]),
      count(db, 'todos', "user_id=? AND status='未完成'", [user.id]),
      count(db, 'todos', "user_id=? AND status='未完成' AND due_date IS NOT NULL AND due_date < ?", [user.id, today]),
      count(db, 'schedules', 'user_id=? AND start_time>=? AND start_time<?', [user.id, today, tomorrow]),
      count(db, 'goals', 'user_id=?', [user.id]),
    ])
    const focus = await focusStats(db, user.id, today, tomorrow)
    const avg = await db.prepare('SELECT COALESCE(AVG(progress),0) AS avg FROM goals WHERE user_id=?').bind(user.id).first()
    const recentNotes = await db.prepare('SELECT * FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 5').bind(user.id).all()
    const todayTodos = await db.prepare("SELECT * FROM todos WHERE user_id=? AND status='未完成' AND due_date IS NOT NULL AND due_date>=? AND due_date<? ORDER BY priority DESC, created_at DESC LIMIT 5").bind(user.id, today, tomorrow).all()
    const todaySchedules = await db.prepare('SELECT * FROM schedules WHERE user_id=? AND start_time>=? AND start_time<? ORDER BY start_time ASC').bind(user.id, today, tomorrow).all()
    return success({
      notes_count: counts[0],
      todos_total: counts[1],
      todos_done: counts[2],
      todos_undone: counts[3],
      todos_overdue: counts[4],
      today_schedules: counts[5],
      today_focus: focus.today_focus,
      total_focus: focus.total_focus,
      goals_count: counts[6],
      avg_progress: Math.round((avg?.avg || 0) * 10) / 10,
      recent_notes: (recentNotes.results || []).map(noteToDict),
      today_todos: (todayTodos.results || []).map(todoToDict),
      today_schedule_list: (todaySchedules.results || []).map(scheduleToDict),
    })
  }
  if (parts[0] === 'charts') {
    const days = []
    const completed = []
    for (let i = 6; i >= 0; i -= 1) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      d.setHours(0, 0, 0, 0)
      const start = formatDateTime(d)
      days.push(formatDate(start).slice(5))
      completed.push(await count(db, 'todos', "user_id=? AND status='已完成' AND updated_at>=? AND updated_at<?", [user.id, start, tomorrowOf(start)]))
    }
    return success({
      trend: { days, completed },
      distribution: [
        { name: '已完成', value: await count(db, 'todos', "user_id=? AND status='已完成'", [user.id]) },
        { name: '未完成', value: await count(db, 'todos', "user_id=? AND status='未完成'", [user.id]) },
      ],
    })
  }
  return error('接口不存在', 404)
}

async function count(db, table, where, params) {
  const row = await db.prepare(`SELECT COUNT(*) AS total FROM ${table} WHERE ${where}`).bind(...params).first()
  return row?.total || 0
}

async function handleAi(context, user, parts, method) {
  const db = context.env.DB
  if (method === 'GET' && parts[0] === 'records') {
    const type = new URL(context.request.url).searchParams.get('ai_type')?.trim()
    const rows = type
      ? await db.prepare('SELECT * FROM ai_records WHERE user_id=? AND ai_type=? ORDER BY created_at DESC LIMIT 50').bind(user.id, type).all()
      : await db.prepare('SELECT * FROM ai_records WHERE user_id=? ORDER BY created_at DESC LIMIT 50').bind(user.id).all()
    return success((rows.results || []).map(aiRecordToDict))
  }
  if (method !== 'POST') return error('接口不存在', 404)
  if (parts[0] === 'chat') {
    const data = await body(context.request)
    const prompt = String(data.prompt || '').trim()
    if (!prompt) return error('请输入问题', 400)
    const reply = await chatText(context, user, prompt, '你是一个专业的个人效率管理助手，给出具体、可操作、简洁清晰的建议。', '')
    await saveAiRecord(db, user.id, prompt, reply, 'chat')
    return success({ reply, prompt }, 'AI 回复完成')
  }
  if (parts[0] === 'daily-plan') {
    const result = await chatJson(context, user, '请为我生成今天的每日计划，返回JSON：{"date":"","day":"","schedule":[{"time":"","task":""}],"tips":""}', '你是一个时间管理专家，只返回JSON。', {
      date: formatDate(now()),
      day: '',
      schedule: [{ time: '09:00', task: '处理优先任务' }, { time: '14:00', task: '推进目标' }],
      tips: '先完成最重要的一件事。',
    })
    await saveAiRecord(db, user.id, '生成每日计划', JSON.stringify(result), 'plan')
    return success({ plan: result }, '计划生成完成')
  }
  if (parts[0] === 'task-analysis') {
    const total = await count(db, 'todos', 'user_id=?', [user.id])
    const undone = await count(db, 'todos', "user_id=? AND status='未完成'", [user.id])
    const overdue = await count(db, 'todos', "user_id=? AND status='未完成' AND due_date IS NOT NULL AND due_date<?", [user.id, startOfToday()])
    const result = await chatJson(context, user, `分析我的任务压力：总任务${total}，未完成${undone}，逾期${overdue}。返回JSON：{"pressure":"","total_todos":${total},"undone":${undone},"overdue":${overdue},"advice":""}`, '你是任务管理分析师，只返回JSON。', {
      pressure: overdue > 0 ? '高' : undone > 5 ? '中' : '低',
      total_todos: total,
      undone,
      overdue,
      advice: '建议优先处理逾期任务，并把大任务拆成小步骤。',
    })
    await saveAiRecord(db, user.id, '分析任务压力', JSON.stringify(result), 'analysis')
    return success(result, '分析完成')
  }
  if (parts[0] === 'summary-today') {
    const today = startOfToday()
    const tomorrow = tomorrowOf(today)
    const completed = await count(db, 'todos', "user_id=? AND status='已完成' AND updated_at>=? AND updated_at<?", [user.id, today, tomorrow])
    const remaining = await count(db, 'todos', "user_id=? AND status='未完成'", [user.id])
    const notes = await count(db, 'notes', 'user_id=? AND updated_at>=? AND updated_at<?', [user.id, today, tomorrow])
    const summary = { date: formatDate(today), completed_tasks: completed, remaining_tasks: remaining, notes_updated: notes, message: `今天完成了 ${completed} 个任务，更新了 ${notes} 篇笔记，还剩 ${remaining} 个待办事项。继续保持节奏。` }
    await saveAiRecord(db, user.id, '总结今日任务', JSON.stringify(summary), 'summary')
    return success({ summary }, '总结完成')
  }
  return error('接口不存在', 404)
}

async function handleAchievements(context, user, method) {
  if (method !== 'GET') return error('接口不存在', 404)
  const db = context.env.DB
  const totalFocus = (await db.prepare('SELECT COALESCE(SUM(duration),0) AS total FROM focus_records WHERE user_id=?').bind(user.id).first())?.total || 0
  const values = {
    notes: await count(db, 'notes', 'user_id=? AND is_archived=0', [user.id]),
    todos_created: await count(db, 'todos', 'user_id=?', [user.id]),
    todos_done: await count(db, 'todos', "user_id=? AND status='已完成'", [user.id]),
    focus_total: totalFocus,
    focus_sessions: await count(db, 'focus_records', 'user_id=?', [user.id]),
    goals: await count(db, 'goals', 'user_id=?', [user.id]),
    goals_done: await count(db, 'goals', "user_id=? AND (status='已完成' OR progress>=100)", [user.id]),
    collections: await count(db, 'collections', 'user_id=?', [user.id]),
    schedules: await count(db, 'schedules', 'user_id=?', [user.id]),
  }
  const focusStreak = await getFocusStreak(db, user.id)
  const ach = (code, title, description, category, value, target) => ({ code, title, description, category, value: Number(value || 0), target, progress: target <= 0 ? 100 : Math.min(100, Math.floor((Number(value || 0) / target) * 100)), unlocked: Number(value || 0) >= target })
  const items = [
    ach('first_note', '灵感起笔', '创建第一篇笔记', '笔记', values.notes, 1),
    ach('note_collector', '笔记收藏家', '累计创建 10 篇笔记', '笔记', values.notes, 10),
    ach('task_first_done', '任务破冰', '完成第一个待办任务', '待办', values.todos_done, 1),
    ach('task_master', '执行力达人', '累计完成 10 个待办任务', '待办', values.todos_done, 10),
    ach('task_planner', '计划启动器', '累计创建 10 个待办任务', '待办', values.todos_created, 10),
    ach('focus_beginner', '进入心流', '累计专注 25 分钟', '专注', values.focus_total, 25),
    ach('focus_runner', '稳定专注', '累计完成 10 次专注记录', '专注', values.focus_sessions, 10),
    ach('focus_streak_3', '连续专注', '连续 3 天留下专注记录', '专注', focusStreak, 3),
    ach('goal_setter', '目标上墙', '创建第一个目标', '目标', values.goals, 1),
    ach('goal_finisher', '目标达成', '完成第一个目标', '目标', values.goals_done, 1),
    ach('knowledge_keeper', '知识仓库', '累计收藏 5 条知识资源', '收藏', values.collections, 5),
    ach('schedule_keeper', '日程管家', '累计创建 5 条日程', '日程', values.schedules, 5),
  ]
  const unlocked = items.filter((item) => item.unlocked).length
  return success({ items, summary: { total: items.length, unlocked, locked: items.length - unlocked, progress: Math.round((unlocked / items.length) * 1000) / 10, focus_streak: focusStreak } })
}

async function getFocusStreak(db, userId) {
  const rows = await db.prepare('SELECT DISTINCT substr(created_at,1,10) AS day FROM focus_records WHERE user_id=?').bind(userId).all()
  const days = new Set((rows.results || []).map((row) => row.day))
  let streak = 0
  const d = new Date()
  while (days.has(formatDateTime(d).slice(0, 10))) {
    streak += 1
    d.setDate(d.getDate() - 1)
  }
  return streak
}

async function handleSearch(context, user, method) {
  if (method !== 'GET') return error('接口不存在', 404)
  const db = context.env.DB
  const url = new URL(context.request.url)
  const keyword = url.searchParams.get('q')?.trim() || ''
  const type = url.searchParams.get('type')?.trim() || 'all'
  const limit = Math.min(20, Math.max(1, intParam(url.searchParams.get('limit'), 6)))
  if (!keyword) return success({ keyword: '', total: 0, groups: [] })
  const like = `%${keyword}%`
  const groups = []
  const group = (key, label, items, total) => ({ key, label, items, total })
  const excerpt = (...values) => values.map((v) => String(v || '').replace(/\n/g, ' ').trim()).find(Boolean)?.slice(0, 120) || ''
  if (type === 'all' || type === 'notes') {
    const rows = await db.prepare('SELECT * FROM notes WHERE user_id=? AND is_archived=0 AND (title LIKE ? OR content LIKE ? OR category LIKE ? OR tags LIKE ?) ORDER BY updated_at DESC LIMIT ?').bind(user.id, like, like, like, like, limit).all()
    const total = await count(db, 'notes', 'user_id=? AND is_archived=0 AND (title LIKE ? OR content LIKE ? OR category LIKE ? OR tags LIKE ?)', [user.id, like, like, like, like])
    groups.push(group('notes', '笔记', (rows.results || []).map((item) => ({ type: 'notes', type_label: '笔记', id: item.id, title: item.title, summary: excerpt(item.content, item.category), meta: formatDate(item.updated_at), path: `/notes/${item.id}` })), total))
  }
  if (type === 'all' || type === 'todos') {
    const rows = await db.prepare('SELECT * FROM todos WHERE user_id=? AND (title LIKE ? OR description LIKE ? OR category LIKE ? OR priority LIKE ? OR status LIKE ?) ORDER BY updated_at DESC LIMIT ?').bind(user.id, like, like, like, like, like, limit).all()
    const total = await count(db, 'todos', 'user_id=? AND (title LIKE ? OR description LIKE ? OR category LIKE ? OR priority LIKE ? OR status LIKE ?)', [user.id, like, like, like, like, like])
    groups.push(group('todos', '待办', (rows.results || []).map((item) => ({ type: 'todos', type_label: '待办', id: item.id, title: item.title, summary: excerpt(item.description, item.category), meta: item.status, path: '/todos' })), total))
  }
  if (type === 'all' || type === 'schedules') {
    const rows = await db.prepare('SELECT * FROM schedules WHERE user_id=? AND (title LIKE ? OR description LIKE ? OR location LIKE ?) ORDER BY start_time DESC LIMIT ?').bind(user.id, like, like, like, limit).all()
    const total = await count(db, 'schedules', 'user_id=? AND (title LIKE ? OR description LIKE ? OR location LIKE ?)', [user.id, like, like, like])
    groups.push(group('schedules', '日程', (rows.results || []).map((item) => ({ type: 'schedules', type_label: '日程', id: item.id, title: item.title, summary: excerpt(item.description, item.location), meta: formatDateTime(item.start_time).slice(0, 16), path: '/schedules' })), total))
  }
  if (type === 'all' || type === 'goals') {
    const rows = await db.prepare('SELECT * FROM goals WHERE user_id=? AND (title LIKE ? OR description LIKE ? OR status LIKE ?) ORDER BY updated_at DESC LIMIT ?').bind(user.id, like, like, like, limit).all()
    const total = await count(db, 'goals', 'user_id=? AND (title LIKE ? OR description LIKE ? OR status LIKE ?)', [user.id, like, like, like])
    groups.push(group('goals', '目标', (rows.results || []).map((item) => ({ type: 'goals', type_label: '目标', id: item.id, title: item.title, summary: excerpt(item.description, item.status), meta: `${item.progress || 0}%`, path: '/goals' })), total))
  }
  if (type === 'all' || type === 'collections') {
    const rows = await db.prepare('SELECT * FROM collections WHERE user_id=? AND (title LIKE ? OR description LIKE ? OR url LIKE ? OR category LIKE ? OR tags LIKE ?) ORDER BY updated_at DESC LIMIT ?').bind(user.id, like, like, like, like, like, limit).all()
    const total = await count(db, 'collections', 'user_id=? AND (title LIKE ? OR description LIKE ? OR url LIKE ? OR category LIKE ? OR tags LIKE ?)', [user.id, like, like, like, like, like])
    groups.push(group('collections', '收藏', (rows.results || []).map((item) => ({ type: 'collections', type_label: '收藏', id: item.id, title: item.title, summary: excerpt(item.description, item.url, item.category), meta: item.category, path: '/collections' })), total))
  }
  return success({ keyword, total: groups.reduce((sum, item) => sum + item.total, 0), groups })
}

async function saveAiRecord(db, userId, prompt, result, type = 'chat') {
  await db.prepare('INSERT INTO ai_records (user_id,prompt,result,ai_type,created_at) VALUES (?,?,?,?,?)').bind(userId, prompt, String(result || ''), type, now()).run().catch(() => null)
}

async function chatText(context, user, prompt, systemPrompt, fallback) {
  const key = await getUserApiKey(context, user)
  if (!key || key.startsWith('sk-your-') || key === 'your-api-key') {
    if (fallback !== '') return fallback
    throw new Error(API_KEY_NOT_SET_MSG)
  }
  const resp = await fetch(`${context.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com'}/chat/completions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model: context.env.DEEPSEEK_MODEL || 'deepseek-chat',
      messages: [
        ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
        { role: 'user', content: prompt },
      ],
      temperature: 0.7,
      max_tokens: 2000,
    }),
  })
  if (!resp.ok) {
    if (fallback !== '') return fallback
    throw new Error(`AI 服务调用失败: ${resp.status}`)
  }
  const data = await resp.json()
  return data?.choices?.[0]?.message?.content || fallback
}

async function chatJson(context, user, prompt, systemPrompt, fallback) {
  try {
    const text = await chatText(context, user, prompt, `${systemPrompt || ''}\n请只返回合法的 JSON 格式，不要包含其他文字。`, JSON.stringify(fallback))
    const cleaned = text.trim().replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```$/i, '').trim()
    return JSON.parse(cleaned)
  } catch {
    return fallback
  }
}

async function aiJsonWithFallback(context, user, data, type, fallback, message) {
  const prompts = {
    category: [`请将以下笔记分类，返回JSON：{"category":""}\n标题：${data.title || ''}\n内容：${data.content || ''}`, '你是笔记分类助手，只返回JSON。'],
    keywords: [`从以下笔记中提取3-5个关键词，返回JSON：{"keywords":[""]}\n标题：${data.title || ''}\n内容：${data.content || ''}`, '你是关键词提取专家，只返回JSON。'],
    title: [`为以下笔记内容生成一个简短标题，返回JSON：{"title":""}\n${data.content || ''}`, '你是标题生成助手，只返回JSON。'],
    todo: [`根据用户描述生成一个待办事项，返回JSON：{"title":"","description":"","priority":"","category":""}\n用户描述：${data.prompt || ''}`, '你是任务管理助手，只返回JSON。'],
    subtasks: [`将以下复杂任务拆分为3-5个子任务，返回JSON：{"subtasks":[{"title":"","priority":""}]}\n任务：${data.title || ''}`, '你是任务拆分专家，只返回JSON。'],
    priority: [`根据任务信息推荐优先级（高/中/低），返回JSON：{"priority":"","reason":""}\n标题：${data.title || ''}\n描述：${data.description || ''}`, '你是任务优先级评估专家，只返回JSON。'],
  }
  const [prompt, systemPrompt] = prompts[type]
  const result = await chatJson(context, user, prompt, systemPrompt, fallback)
  return success(result, message)
}

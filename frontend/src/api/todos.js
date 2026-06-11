import request from '@/utils/request'

export function getTodos(params) {
  return request.get('/todos', { params })
}

export function getTodo(id) {
  return request.get(`/todos/${id}`)
}

export function createTodo(data) {
  return request.post('/todos', data)
}

export function updateTodo(id, data) {
  return request.put(`/todos/${id}`, data)
}

export function deleteTodo(id) {
  return request.delete(`/todos/${id}`)
}

export function toggleTodo(id) {
  return request.patch(`/todos/${id}/toggle`)
}

export function updateProgress(id, progress) {
  return request.patch(`/todos/${id}/progress`, { progress })
}

export function getTodayTodos() {
  return request.get('/todos/today')
}

export function getOverdueTodos() {
  return request.get('/todos/overdue')
}

export function aiGenerateTodo(prompt) {
  return request.post('/todos/ai-generate', { prompt })
}

export function aiSplitTask(title) {
  return request.post('/todos/ai-split', { title })
}

export function aiRecommendPriority(data) {
  return request.post('/todos/ai-priority', data)
}

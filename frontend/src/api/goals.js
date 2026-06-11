import request from '@/utils/request'

export function getGoals(params) {
  return request.get('/goals', { params })
}

export function createGoal(data) {
  return request.post('/goals', data)
}

export function getGoal(id) {
  return request.get(`/goals/${id}`)
}

export function updateGoal(id, data) {
  return request.put(`/goals/${id}`, data)
}

export function deleteGoal(id) {
  return request.delete(`/goals/${id}`)
}

export function updateGoalProgress(id, progress) {
  return request.patch(`/goals/${id}/progress`, { progress })
}

export function aiGeneratePlan(id) {
  return request.post(`/goals/${id}/ai-plan`)
}

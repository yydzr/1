import request from '@/utils/request'

export function aiChat(prompt) {
  return request.post('/ai/chat', { prompt })
}

export function aiDailyPlan() {
  return request.post('/ai/daily-plan')
}

export function aiTaskAnalysis() {
  return request.post('/ai/task-analysis')
}

export function aiSummaryToday() {
  return request.post('/ai/summary-today')
}

export function getAiRecords(params) {
  return request.get('/ai/records', { params })
}

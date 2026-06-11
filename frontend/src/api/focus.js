import request from '@/utils/request'

export function getFocusRecords() {
  return request.get('/focus/records')
}

export function createFocusRecord(data) {
  return request.post('/focus/records', data)
}

export function getFocusStats() {
  return request.get('/focus/stats')
}

export function getFocusCharts() {
  return request.get('/focus/charts')
}

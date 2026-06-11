import request from '@/utils/request'

export function getSchedules(params) {
  return request.get('/schedules', { params })
}

export function getScheduleDates() {
  return request.get('/schedules/dates')
}

export function createSchedule(data) {
  return request.post('/schedules', data)
}

export function getSchedule(id) {
  return request.get(`/schedules/${id}`)
}

export function updateSchedule(id, data) {
  return request.put(`/schedules/${id}`, data)
}

export function deleteSchedule(id) {
  return request.delete(`/schedules/${id}`)
}

export function getTodaySchedules() {
  return request.get('/schedules/today')
}

export function getWeekSchedules() {
  return request.get('/schedules/week')
}

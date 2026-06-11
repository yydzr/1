import request from '@/utils/request'

/** 首页统计数据 */
export function getStats() {
  return request.get('/dashboard/stats')
}

/** 首页图表数据 */
export function getCharts() {
  return request.get('/dashboard/charts')
}

import request from '@/utils/request'

export function globalSearch(params) {
  return request.get('/search', { params })
}

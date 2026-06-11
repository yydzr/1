import request from '@/utils/request'

export function getCollections(params) {
  return request.get('/collections', { params })
}

export function createCollection(data) {
  return request.post('/collections', data)
}

export function getCollection(id) {
  return request.get(`/collections/${id}`)
}

export function updateCollection(id, data) {
  return request.put(`/collections/${id}`, data)
}

export function deleteCollection(id) {
  return request.delete(`/collections/${id}`)
}

export function aiSummaryCollection(id) {
  return request.post(`/collections/${id}/ai-summary`)
}

export function aiTagsCollection(id) {
  return request.post(`/collections/${id}/ai-tags`)
}

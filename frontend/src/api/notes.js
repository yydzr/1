import request from '@/utils/request'

export function getNotes(params) {
  return request.get('/notes', { params })
}

export function getNote(id) {
  return request.get(`/notes/${id}`)
}

export function createNote(data) {
  return request.post('/notes', data)
}

export function updateNote(id, data) {
  return request.put(`/notes/${id}`, data)
}

export function deleteNote(id) {
  return request.delete(`/notes/${id}`)
}

export function toggleTop(id) {
  return request.patch(`/notes/${id}/top`)
}

export function toggleFavorite(id) {
  return request.patch(`/notes/${id}/favorite`)
}

export function toggleArchive(id) {
  return request.patch(`/notes/${id}/archive`)
}

export function aiSummary(id) {
  return request.post(`/notes/${id}/summary`)
}

export function aiClassify(data) {
  return request.post('/notes/classify', data)
}

export function aiKeywords(data) {
  return request.post('/notes/keywords', data)
}

export function aiGenerateTitle(data) {
  return request.post('/notes/generate-title', data)
}

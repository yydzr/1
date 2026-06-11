import request from '@/utils/request'

export function getAchievements() {
  return request.get('/achievements')
}

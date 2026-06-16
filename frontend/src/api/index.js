import axios from 'axios'
import { ElMessage } from 'element-plus'

// 管理员令牌（与后端 ADMIN_TOKEN 一致）
const ADMIN_TOKEN = 'wc2026-admin-token'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    // 为管理 API 自动添加 Bearer token（FastAPI 鉴权使用 Authorization 头）
    const url = config.url || ''
    if (
      url.startsWith('/admin/') ||
      url === '/odds/update'
    ) {
      config.headers.Authorization = `Bearer ${ADMIN_TOKEN}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    // FastAPI 返回 {detail: '...'}；旧 Flask 业务接口可能返回 {message: '...'}
    const payload = error.response?.data
    const message = payload?.detail || payload?.message || '请求失败，请稍后重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const matchAPI = {
  getMatchesByDate: (date) => api.get('/matches', { params: { date } }),
  updateMatchResult: (matchId, score1, score2) => api.post(`/matches/${matchId}/result`, { score1, score2 }),
  getGroupMatches: (group) => api.get('/group_stage', { params: group ? { group } : {} }),
  getKnockoutMatches: () => api.get('/knockout'),
  getKnockoutBracket: () => api.get('/knockout/bracket'),
  getRankings: (group) => api.get('/rankings', { params: group ? { group } : {} }),
  getFlags: () => api.get('/flags'),
  getLiveMatches: () => api.get('/live/matches'),
}

export const oddsAPI = {
  getSources: () => api.get('/odds/sources'),
  updateOdds: () => api.post('/odds/update')
}

export const adminAPI = {
  getGroups: () => api.get('/admin/groups'),
  addTeam: (teamName, groupId) => api.post('/admin/teams', { team_name: teamName, group_id: groupId }),
  deleteTeam: (teamId) => api.delete(`/admin/teams/${teamId}`),
  generateMatches: (groupId) => api.post('/admin/matches/generate', { group_id: groupId }),
  addGroupMatch: (team1, team2, matchTime, groupName) => api.post('/admin/group_matches', { team1, team2, match_time: matchTime, group_name: groupName }),
  getMatches: () => api.get('/admin/matches'),
  getMatch: (matchId) => api.get(`/admin/matches/${matchId}`),
  updateMatch: (matchId, data) => api.put(`/admin/matches/${matchId}`, data),
  updateOdds: () => api.post('/odds/update')
}

export default api

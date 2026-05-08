import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => config,
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.message || '请求失败，请稍后重试'
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

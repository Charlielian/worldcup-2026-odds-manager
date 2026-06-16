<template>
  <div class="live-matches">
    <!-- 页头 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="page-header">
          <h2>
            <el-icon><Clock /></el-icon>
            体彩实时赔率
          </h2>
          <div class="header-actions">
            <el-tag type="success" effect="dark">数据来源: 中国体彩</el-tag>
            <el-button type="primary" :icon="Refresh" @click="fetchMatches" :loading="loading" style="margin-left: 12px;">
              刷新数据
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 统计 -->
    <el-row :gutter="20" style="margin-bottom: 20px;" v-if="!loading && matches.length > 0">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ matches.length }}</div>
          <div class="stat-label">在售比赛</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ Object.keys(matchesByDate).length }}</div>
          <div class="stat-label">比赛日期</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ leagueCount }}</div>
          <div class="stat-label">联赛数量</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ lastUpdateTime }}</div>
          <div class="stat-label">最后更新</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 加载 -->
    <el-skeleton v-if="loading && matches.length === 0" :rows="5" animated />

    <!-- 错误 -->
    <el-alert v-if="error" :title="error" type="error" show-icon closable @close="error = ''" style="margin-bottom: 20px;" />

    <!-- 比赛列表 -->
    <div v-if="!loading && matches.length > 0">
      <el-collapse v-model="activeDate" accordion>
        <el-collapse-item v-for="(dateMatches, date) in matchesByDate" :key="date" :name="date">
          <template #title>
            <div class="date-header">
              <el-icon><Calendar /></el-icon>
              <span class="date-text">{{ formatDate(date) }}</span>
              <el-tag size="small" type="info" style="margin-left: 10px;">{{ dateMatches.length }} 场</el-tag>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col :xs="24" :sm="24" :md="24" :lg="24" v-for="match in dateMatches" :key="match.match_num" style="margin-bottom: 16px;">
              <el-card shadow="hover" class="match-card">
                <!-- 队伍信息 -->
                <div class="match-header">
                  <div class="match-meta">
                    <el-tag size="small" effect="plain">{{ match.league }}</el-tag>
                    <span class="match-num">{{ match.match_num }}</span>
                    <span class="match-time">{{ match.match_date }} {{ match.match_time }}</span>
                  </div>
                  <div class="teams">
                    <div class="team">
                      <span class="team-flag" v-if="match.home_icon && match.home_icon.type === 'national'">{{ match.home_icon.flag }}</span>
                      <img v-else-if="match.home_icon && match.home_icon.logo_url" :src="match.home_icon.logo_url" :alt="match.home_team" class="team-logo" />
                      <span class="team-name">{{ match.home_team }}</span>
                      <span class="team-rank" v-if="match.home_rank">{{ match.home_rank }}</span>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team">
                      <span class="team-flag" v-if="match.away_icon && match.away_icon.type === 'national'">{{ match.away_icon.flag }}</span>
                      <img v-else-if="match.away_icon && match.away_icon.logo_url" :src="match.away_icon.logo_url" :alt="match.away_team" class="team-logo" />
                      <span class="team-name">{{ match.away_team }}</span>
                      <span class="team-rank" v-if="match.away_rank">{{ match.away_rank }}</span>
                    </div>
                  </div>
                </div>

                <!-- 玩法 Tabs -->
                <el-tabs v-model="match._activeTab" type="border-card" class="play-tabs">
                  <!-- 胜平负 -->
                  <el-tab-pane label="胜平负(不让球)" name="had" :disabled="!match.had">
                    <div class="odds-grid-3" v-if="match.had">
                      <div class="odds-cell">
                        <span class="odds-label">主胜</span>
                        <span class="odds-value">{{ match.had.win }}</span>
                      </div>
                      <div class="odds-cell odds-draw">
                        <span class="odds-label">平局</span>
                        <span class="odds-value">{{ match.had.draw }}</span>
                      </div>
                      <div class="odds-cell">
                        <span class="odds-label">客胜</span>
                        <span class="odds-value">{{ match.had.lose }}</span>
                      </div>
                    </div>
                    <el-empty v-else description="暂无胜平负(不让球)赔率" :image-size="40" />
                  </el-tab-pane>

                  <!-- 让球胜平负 -->
                  <el-tab-pane :label="'让球胜平负' + (match.hhad ? '(' + match.hhad.goal_line + ')' : '')" name="hhad" :disabled="!match.hhad">
                    <div class="odds-grid-3" v-if="match.hhad">
                      <div class="odds-cell">
                        <span class="odds-label">主胜({{ match.hhad.goal_line }})</span>
                        <span class="odds-value">{{ match.hhad.win }}</span>
                      </div>
                      <div class="odds-cell odds-draw">
                        <span class="odds-label">平局</span>
                        <span class="odds-value">{{ match.hhad.draw }}</span>
                      </div>
                      <div class="odds-cell">
                        <span class="odds-label">客胜</span>
                        <span class="odds-value">{{ match.hhad.lose }}</span>
                      </div>
                    </div>
                  </el-tab-pane>

                  <!-- 猜比分 -->
                  <el-tab-pane label="猜比分" name="crs" :disabled="!match.crs || match.crs.length === 0">
                    <div class="score-grid" v-if="match.crs && match.crs.length > 0">
                      <div class="score-cell" v-for="item in match.crs" :key="item.score">
                        <span class="score-text">{{ item.score }}</span>
                        <span class="score-odds">{{ item.odds }}</span>
                      </div>
                    </div>
                    <el-empty v-else description="暂无数据" :image-size="40" />
                  </el-tab-pane>

                  <!-- 总进球 -->
                  <el-tab-pane label="总进球" name="ttg" :disabled="!match.ttg || match.ttg.length === 0">
                    <div class="odds-grid-3" v-if="match.ttg && match.ttg.length > 0">
                      <div class="odds-cell" v-for="item in match.ttg" :key="item.goals">
                        <span class="odds-label">{{ item.label }}</span>
                        <span class="odds-value">{{ item.odds }}</span>
                      </div>
                    </div>
                    <el-empty v-else description="暂无数据" :image-size="40" />
                  </el-tab-pane>

                  <!-- 半全场 -->
                  <el-tab-pane label="半全场" name="bqc" :disabled="!match.bqc || match.bqc.length === 0">
                    <div class="bqc-grid" v-if="match.bqc && match.bqc.length > 0">
                      <div class="bqc-cell" v-for="item in match.bqc" :key="item.code">
                        <span class="bqc-text">{{ item.result }}</span>
                        <span class="bqc-odds">{{ item.odds }}</span>
                      </div>
                    </div>
                    <el-empty v-else description="暂无数据" :image-size="40" />
                  </el-tab-pane>
                </el-tabs>

                <!-- 更新时间 -->
                <div class="update-time">
                  <el-icon><Clock /></el-icon>
                  {{ match.updated_at }}
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && matches.length === 0" description="暂无在售比赛数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Clock, Refresh, Calendar } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const error = ref('')
const matches = ref([])
const matchesByDate = ref({})
const activeDate = ref('')

const leagueCount = computed(() => {
  return new Set(matches.value.map(m => m.league).filter(Boolean)).size || '-'
})

const lastUpdateTime = computed(() => {
  if (matches.value.length === 0) return '-'
  const latest = matches.value.reduce((t, m) => (m.updated_at > t ? m.updated_at : t), '')
  return latest ? latest.split(' ')[1] || latest : '-'
})

const formatDate = (dateStr) => {
  if (!dateStr) return '未知日期'
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const d = new Date(dateStr)
  return `${dateStr} ${weekdays[d.getDay()]}`
}

const fetchMatches = async () => {
  loading.value = true
  error.value = ''
  try {
    const data = await api.get('/live/matches')
    // 计算默认激活的标签
    const getDefaultTab = (match) => {
      if (match.had) return 'had'
      if (match.hhad) return 'hhad'
      if (match.crs && match.crs.length > 0) return 'crs'
      if (match.ttg && match.ttg.length > 0) return 'ttg'
      if (match.bqc && match.bqc.length > 0) return 'bqc'
      return 'had'
    }
    matches.value = (data.all_matches || []).map(m => ({ ...m, _activeTab: getDefaultTab(m) }))
    // 给 matchesByDate 中的每场比赛也添加 _activeTab
    const mbd = data.matches_by_date || {}
    for (const date of Object.keys(mbd)) {
      mbd[date] = mbd[date].map(m => ({ ...m, _activeTab: getDefaultTab(m) }))
    }
    matchesByDate.value = mbd
    const dates = Object.keys(matchesByDate.value)
    if (dates.length > 0) activeDate.value = dates[0]
    ElMessage.success(`获取到 ${matches.value.length} 场在售比赛`)
  } catch (e) {
    console.error('获取比赛数据失败:', e)
    error.value = e.response?.data?.message || '获取数据失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchMatches() })
</script>

<style scoped>
.live-matches { padding: 20px; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.page-header h2 { margin: 0; display: flex; align-items: center; gap: 8px; }
.header-actions { display: flex; align-items: center; }

/* 统计 */
.stat-card { text-align: center; padding: 10px 0; }
.stat-value { font-size: 28px; font-weight: 700; color: #0047AB; }
.stat-label { font-size: 14px; color: var(--el-text-color-secondary); margin-top: 4px; }

/* 日期 */
.date-header { display: flex; align-items: center; font-size: 16px; font-weight: 600; }
.date-text { margin-left: 8px; }

/* 比赛卡片 */
.match-card { transition: transform 0.3s ease, box-shadow 0.3s ease; }
.match-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }

.match-header { margin-bottom: 12px; }
.match-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.match-num { font-size: 13px; color: var(--el-text-color-secondary); }
.match-time { font-size: 13px; color: var(--el-text-color-secondary); }

.teams { display: flex; justify-content: center; align-items: center; gap: 20px; padding: 10px 0; }
.team { text-align: center; min-width: 100px; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.team-flag { font-size: 28px; line-height: 1.2; }
.team-logo { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid #e4e7ed; }
.team-name { font-size: 18px; font-weight: 700; color: var(--el-text-color-primary); }
.team-rank { display: block; font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }
.vs { font-size: 16px; font-weight: 600; color: var(--el-text-color-placeholder); }

/* 玩法 Tabs */
.play-tabs { margin-top: 8px; }
.play-tabs :deep(.el-tabs__content) { padding: 12px; }

/* 胜平负 / 让球 / 总进球 三列 */
.odds-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.odds-cell { text-align: center; padding: 10px 6px; background: #f5f7fa; border-radius: 6px; }
.odds-cell.odds-draw { background: #fff8e1; }
.odds-label { display: block; font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 4px; }
.odds-value { display: block; font-size: 20px; font-weight: 700; color: #0047AB; }

/* 猜比分网格 */
.score-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr)); gap: 6px; }
.score-cell { text-align: center; padding: 8px 4px; background: #f5f7fa; border-radius: 6px; }
.score-text { display: block; font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 2px; }
.score-odds { display: block; font-size: 13px; font-weight: 700; color: #0047AB; }

/* 半全场网格 */
.bqc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.bqc-cell { text-align: center; padding: 10px 6px; background: #f5f7fa; border-radius: 6px; }
.bqc-text { display: block; font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 2px; }
.bqc-odds { display: block; font-size: 18px; font-weight: 700; color: #0047AB; }

/* 更新时间 */
.update-time {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  margin-top: 10px; font-size: 12px; color: var(--el-text-color-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; justify-content: space-between; }
  .team-name { font-size: 15px; }
  .odds-value { font-size: 17px; }
  .score-grid { grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); }
  .bqc-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>

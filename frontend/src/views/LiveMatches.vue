<template>
  <div class="live-matches">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="page-header">
          <h2>
            <el-icon><Clock /></el-icon>
            体彩实时赔率
          </h2>
          <div class="header-actions">
            <el-tag type="success" effect="dark">
              数据来源: 中国体彩
            </el-tag>
            <el-button 
              type="primary" 
              :icon="Refresh" 
              @click="fetchMatches" 
              :loading="loading"
              style="margin-left: 12px;"
            >
              刷新数据
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 加载状态 -->
    <el-skeleton v-if="loading && matches.length === 0" :rows="5" animated />

    <!-- 错误提示 -->
    <el-alert 
      v-if="error" 
      :title="error" 
      type="error" 
      show-icon 
      closable
      @close="error = ''"
      style="margin-bottom: 20px;"
    />

    <!-- 统计信息 -->
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

    <!-- 比赛列表 -->
    <div v-if="!loading && matches.length > 0">
      <el-collapse v-model="activeDate" accordion>
        <el-collapse-item 
          v-for="(dateMatches, date) in matchesByDate" 
          :key="date"
          :name="date"
        >
          <template #title>
            <div class="date-header">
              <el-icon><Calendar /></el-icon>
              <span class="date-text">{{ formatDate(date) }}</span>
              <el-tag size="small" type="info" style="margin-left: 10px;">
                {{ dateMatches.length }} 场比赛
              </el-tag>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col 
              :xs="24" :sm="12" :md="8" :lg="6"
              v-for="match in dateMatches" 
              :key="`${match.team1}-${match.team2}`"
              style="margin-bottom: 16px;"
            >
              <el-card shadow="hover" class="match-card">
                <!-- 队伍信息 -->
                <div class="teams-section">
                  <div class="team">
                    <span class="team-name">{{ match.team1 }}</span>
                  </div>
                  <div class="vs">VS</div>
                  <div class="team">
                    <span class="team-name">{{ match.team2 }}</span>
                  </div>
                </div>

                <el-divider style="margin: 12px 0;" />

                <!-- 赔率信息 -->
                <div class="odds-section">
                  <div class="odds-title">
                    <el-icon><DataAnalysis /></el-icon>
                    胜平负赔率
                    <el-tag size="small" type="info" effect="plain" style="margin-left: 8px;">
                      {{ match.source }}
                    </el-tag>
                  </div>
                  <div class="odds-grid">
                    <div class="odds-item">
                      <span class="odds-label">主胜</span>
                      <span class="odds-value">{{ match.win_odds }}</span>
                    </div>
                    <div class="odds-item odds-draw">
                      <span class="odds-label">平局</span>
                      <span class="odds-value">{{ match.draw_odds }}</span>
                    </div>
                    <div class="odds-item">
                      <span class="odds-label">客胜</span>
                      <span class="odds-value">{{ match.lose_odds }}</span>
                    </div>
                  </div>
                </div>

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
import { Clock, Refresh, Calendar, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const error = ref('')
const matches = ref([])
const matchesByDate = ref({})
const activeDate = ref('')

// 计算联赛数量
const leagueCount = computed(() => {
  // 从比赛数据中提取联赛信息（如果有）
  return new Set(matches.value.map(m => m.league).filter(Boolean)).size || '-'
})

// 最后更新时间
const lastUpdateTime = computed(() => {
  if (matches.value.length === 0) return '-'
  const latest = matches.value.reduce((latest, m) => {
    return m.updated_at > latest ? m.updated_at : latest
  }, '')
  return latest ? latest.split(' ')[1] : '-'
})

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知日期'
  const date = new Date(dateStr)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${dateStr} ${weekdays[date.getDay()]}`
}

// 获取比赛数据
const fetchMatches = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const data = await api.get('/live/matches')
    matches.value = data.all_matches || []
    matchesByDate.value = data.matches_by_date || {}
    
    // 默认展开第一个日期
    const dates = Object.keys(matchesByDate.value)
    if (dates.length > 0) {
      activeDate.value = dates[0]
    }
    
    ElMessage.success(`获取到 ${matches.value.length} 场在售比赛`)
  } catch (e) {
    console.error('获取比赛数据失败:', e)
    error.value = e.response?.data?.message || '获取数据失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMatches()
})
</script>

<style scoped>
.live-matches {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

/* 统计卡片 */
.stat-card {
  text-align: center;
  padding: 10px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--wc-primary, #0047AB);
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

/* 日期折叠面板 */
.date-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.date-text {
  margin-left: 8px;
}

/* 比赛卡片 */
.match-card {
  height: 100%;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.match-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.teams-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.team {
  flex: 1;
  text-align: center;
}

.team-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.vs {
  padding: 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

/* 赔率区域 */
.odds-section {
  background: linear-gradient(135deg, #f0f5ff, #fff8e1);
  border-radius: 8px;
  padding: 12px;
}

.odds-title {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  margin-bottom: 10px;
}

.odds-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.odds-item {
  text-align: center;
  padding: 8px 4px;
  background: #fff;
  border-radius: 6px;
}

.odds-item.odds-draw {
  background: #fff8e1;
}

.odds-label {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.odds-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--wc-primary, #0047AB);
}

/* 更新时间 */
.update-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .team-name {
    font-size: 13px;
  }
  
  .odds-value {
    font-size: 16px;
  }
}
</style>

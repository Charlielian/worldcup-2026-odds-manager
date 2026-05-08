<template>
  <div class="knockout-page" v-loading="loading">
    <div v-if="!loading && matches.length === 0" class="empty-state">
      <el-empty description="小组赛尚未结束，淘汰赛对阵待定" />
    </div>
    <div v-else-if="!loading">
      <el-collapse v-model="activeRounds">
        <el-collapse-item
          v-for="round in roundOrder"
          :key="round.key"
          :name="round.key"
        >
          <template #title>
            <div class="round-header">
              <span class="round-title">{{ round.label }}</span>
              <el-tag size="small" type="info">{{ getRoundMatches(round.key).length }} 场比赛</el-tag>
            </div>
          </template>
          <div class="round-matches">
            <el-card
              v-for="match in getRoundMatches(round.key)"
              :key="match.id"
              class="match-card"
              shadow="hover"
            >
              <div class="match-info">
                <div class="match-time-venue">
                  <el-icon><Clock /></el-icon>
                  <span>{{ match.match_time }}</span>
                  <span class="venue">{{ match.venue }}</span>
                </div>
                <el-tag
                  :type="getStatusType(match.status)"
                  size="small"
                  effect="dark"
                >
                  {{ getStatusLabel(match.status) }}
                </el-tag>
              </div>

              <div class="match-teams">
                <div class="team">
                  <span v-if="match.flag1" class="flag">{{ match.flag1 }}</span>
                  <span class="team-name">{{ match.team1 }}</span>
                </div>
                <div class="score-section">
                  <template v-if="match.status === 'finished'">
                    <span class="score">{{ match.score1 }}</span>
                    <span class="score-divider">:</span>
                    <span class="score">{{ match.score2 }}</span>
                  </template>
                  <template v-else>
                    <el-tag type="info" effect="plain" round>VS</el-tag>
                  </template>
                </div>
                <div class="team">
                  <span v-if="match.flag2" class="flag">{{ match.flag2 }}</span>
                  <span class="team-name">{{ match.team2 }}</span>
                </div>
              </div>

              <div v-if="match.odds && match.odds.win" class="match-odds">
                <div class="odds-label">赔率</div>
                <div class="odds-items">
                  <div class="odds-item">
                    <span class="odds-label-text">{{ match.team1 }} 胜</span>
                    <span class="odds-value">{{ match.odds.win }}</span>
                  </div>
                  <div class="odds-item">
                    <span class="odds-label-text">平</span>
                    <span class="odds-value">{{ match.odds.draw }}</span>
                  </div>
                  <div class="odds-item">
                    <span class="odds-label-text">{{ match.team2 }} 胜</span>
                    <span class="odds-value">{{ match.odds.lose }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { matchAPI } from '../api'
import { Clock } from '@element-plus/icons-vue'

const loading = ref(true)
const matches = ref([])
const activeRounds = ref([])

const roundOrder = [
  { key: '1/16决赛', label: '1/16决赛 (三十二强)' },
  { key: '1/8决赛', label: '1/8决赛 (十六强)' },
  { key: '1/4决赛', label: '1/4决赛 (八强)' },
  { key: '半决赛', label: '半决赛' },
  { key: '三四名决赛', label: '三四名决赛' },
  { key: '决赛', label: '决赛' }
]

const getRoundMatches = (roundKey) => {
  return matches.value.filter(m => m.stage === roundKey)
}

const getStatusType = (status) => {
  const map = { finished: 'success', upcoming: 'warning', live: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = { finished: '已结束', upcoming: '未开始', live: '进行中' }
  return map[status] || status
}

const fetchMatches = async () => {
  try {
    loading.value = true
    const res = await matchAPI.getKnockoutMatches()
    matches.value = res.matches || []
    // 默认展开有比赛的轮次
    const roundsWithMatches = roundOrder
      .filter(r => getRoundMatches(r.key).length > 0)
      .map(r => r.key)
    activeRounds.value = roundsWithMatches.length > 0 ? [roundsWithMatches[0]] : []
  } catch (error) {
    console.error('获取淘汰赛数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMatches()
})
</script>

<style scoped>
.knockout-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.round-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.round-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.round-matches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.match-card {
  border-radius: 12px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.match-card:hover {
  transform: translateY(-3px);
}

.match-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.match-time-venue {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 14px;
}

.venue {
  margin-left: 8px;
  color: #b0b5bd;
}

.match-teams {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.team {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.team:last-child {
  justify-content: flex-end;
}

.flag {
  font-size: 28px;
}

.team-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  min-width: 80px;
  justify-content: center;
}

.score {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.score-divider {
  font-size: 20px;
  color: #909399;
}

.match-odds {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ebeef5;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
}

.odds-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}

.odds-items {
  display: flex;
  justify-content: space-around;
}

.odds-item {
  text-align: center;
}

.odds-label-text {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.odds-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #e6a23c;
}

@media (max-width: 768px) {
  .round-matches {
    grid-template-columns: 1fr;
  }

  .team-name {
    font-size: 14px;
  }

  .flag {
    font-size: 22px;
  }
}
</style>

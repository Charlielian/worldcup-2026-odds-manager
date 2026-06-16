<template>
  <div class="knockout-page" v-loading="loading">
    <div v-if="!loading && allRounds.length === 0" class="empty-state">
      <el-empty description="小组赛尚未结束，淘汰赛对阵待定" />
    </div>

    <div v-else-if="!loading" class="knockout-list">
      <el-collapse v-model="activeRound" accordion>
        <el-collapse-item
          v-for="round in allRounds"
          :key="round.key"
          :name="round.key"
        >
          <template #title>
            <div class="round-header">
              <span class="round-icon">🏆</span>
              <span class="round-name">{{ round.label }}</span>
              <el-tag size="small" type="info" style="margin-left: 12px;">
                {{ round.matches.length }} 场
              </el-tag>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col
              :xs="24" :sm="12" :md="8" :lg="6"
              v-for="match in round.matches"
              :key="match.id"
              style="margin-bottom: 16px;"
            >
              <el-card
                shadow="hover"
                class="match-card"
                :class="{
                  'is-finished': match.status === 'finished',
                  'is-upcoming': match.status === 'upcoming'
                }"
              >
                <!-- 队伍信息 -->
                <div class="match-teams">
                  <div class="team-row" :class="{ 'is-winner': match.status === 'finished' && match.score1 > match.score2 }">
                    <span class="team-flag">{{ match.flag1 || '' }}</span>
                    <span class="team-name">{{ match.team1 }}</span>
                    <span v-if="match.status === 'finished'" class="team-score">{{ match.score1 }}</span>
                  </div>
                  <div class="vs-row">VS</div>
                  <div class="team-row" :class="{ 'is-winner': match.status === 'finished' && match.score2 > match.score1 }">
                    <span class="team-flag">{{ match.flag2 || '' }}</span>
                    <span class="team-name">{{ match.team2 }}</span>
                    <span v-if="match.status === 'finished'" class="team-score">{{ match.score2 }}</span>
                  </div>
                </div>

                <!-- 比赛时间 -->
                <div class="match-footer">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatTime(match.match_time) }}</span>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import { matchAPI } from '../api'

const loading = ref(true)
const matches = ref([])
const activeRound = ref('')

const roundConfig = [
  { key: '1/16决赛', label: '1/16决赛' },
  { key: '1/8决赛', label: '1/8决赛' },
  { key: '1/4决赛', label: '1/4决赛' },
  { key: '半决赛', label: '半决赛' },
  { key: '三四名决赛', label: '三四名决赛' },
  { key: '决赛', label: '决赛' },
]

const allRounds = computed(() => {
  return roundConfig
    .map(r => ({
      ...r,
      matches: matches.value.filter(m => m.stage === r.key)
    }))
    .filter(r => r.matches.length > 0)
})

const formatTime = (matchTime) => {
  if (!matchTime) return ''
  const parts = matchTime.split(' ')
  if (parts.length >= 2) {
    const dateParts = parts[0].split('-')
    if (dateParts.length >= 3) {
      return `${dateParts[1]}-${dateParts[2]} ${parts[1].substring(0, 5)}`
    }
  }
  return matchTime
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await matchAPI.getKnockoutMatches()
    matches.value = res.matches || []
    if (allRounds.value.length > 0) {
      activeRound.value = allRounds.value[0].key
    }
  } catch (error) {
    console.error('获取淘汰赛数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.knockout-page {
  padding: 20px;
  min-height: 100%;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.round-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.round-icon {
  margin-right: 8px;
}

.round-name {
  color: var(--el-text-color-primary);
}

/* 比赛卡片 */
.match-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.match-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.match-card.is-finished {
  border-color: #67c23a;
}

.match-card.is-upcoming {
  border-style: dashed;
}

.match-teams {
  padding: 8px 0;
}

.team-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.team-row.is-winner {
  background: #f0f9eb;
  border-radius: 4px;
  padding: 6px 8px;
  margin: 0 -8px;
}

.team-flag {
  font-size: 20px;
  min-width: 28px;
}

.team-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-score {
  font-size: 16px;
  font-weight: 700;
  color: #0047AB;
  min-width: 24px;
  text-align: center;
}

.vs-row {
  text-align: center;
  font-size: 12px;
  color: #909399;
  padding: 2px 0;
}

.match-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
  font-size: 12px;
  color: #909399;
}
</style>

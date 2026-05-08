<template>
  <div class="bracket-page" v-loading="loading">
    <div v-if="!loading && bracketData.length === 0" class="empty-state">
      <el-empty description="小组赛尚未结束，淘汰赛对阵待定" />
    </div>
    <div v-else-if="!loading" class="bracket-container">
      <div class="bracket-scroll">
        <div class="bracket-grid">
          <!-- 1/16决赛 -->
          <div class="bracket-round" v-if="getMatchesByRound('1/16决赛').length > 0">
            <div class="round-label">1/16决赛</div>
            <div class="round-matches">
              <div class="match-pair">
                <div
                  v-for="match in getMatchesByRound('1/16决赛').slice(0, 8)"
                  :key="match.id"
                  class="bracket-match-wrapper"
                >
                  <div class="bracket-connector bracket-connector-right"></div>
                  <el-card class="bracket-match-card" shadow="hover" :body-style="{ padding: '8px 12px' }">
                    <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                      <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                      <span class="bracket-team-name">{{ match.team1 }}</span>
                    </div>
                    <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                      <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                      <span class="bracket-team-name">{{ match.team2 }}</span>
                    </div>
                    <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                  </el-card>
                </div>
              </div>
              <div class="match-pair">
                <div
                  v-for="match in getMatchesByRound('1/16决赛').slice(8, 16)"
                  :key="match.id"
                  class="bracket-match-wrapper"
                >
                  <div class="bracket-connector bracket-connector-right"></div>
                  <el-card class="bracket-match-card" shadow="hover" :body-style="{ padding: '8px 12px' }">
                    <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                      <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                      <span class="bracket-team-name">{{ match.team1 }}</span>
                    </div>
                    <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                      <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                      <span class="bracket-team-name">{{ match.team2 }}</span>
                    </div>
                    <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                  </el-card>
                </div>
              </div>
            </div>
          </div>

          <!-- 1/8决赛 -->
          <div class="bracket-round" v-if="getMatchesByRound('1/8决赛').length > 0">
            <div class="round-label">1/8决赛</div>
            <div class="round-matches">
              <div
                v-for="(match, idx) in getMatchesByRound('1/8决赛')"
                :key="match.id"
                class="bracket-match-wrapper"
              >
                <div class="bracket-connector bracket-connector-left"></div>
                <div class="bracket-connector bracket-connector-right"></div>
                <el-card class="bracket-match-card" shadow="hover" :body-style="{ padding: '8px 12px' }">
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                    <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                    <span class="bracket-team-name">{{ match.team1 }}</span>
                  </div>
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                    <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                    <span class="bracket-team-name">{{ match.team2 }}</span>
                  </div>
                  <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                </el-card>
              </div>
            </div>
          </div>

          <!-- 1/4决赛 -->
          <div class="bracket-round" v-if="getMatchesByRound('1/4决赛').length > 0">
            <div class="round-label">1/4决赛</div>
            <div class="round-matches">
              <div
                v-for="match in getMatchesByRound('1/4决赛')"
                :key="match.id"
                class="bracket-match-wrapper"
              >
                <div class="bracket-connector bracket-connector-left"></div>
                <div class="bracket-connector bracket-connector-right"></div>
                <el-card class="bracket-match-card" shadow="hover" :body-style="{ padding: '8px 12px' }">
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                    <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                    <span class="bracket-team-name">{{ match.team1 }}</span>
                  </div>
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                    <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                    <span class="bracket-team-name">{{ match.team2 }}</span>
                  </div>
                  <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                </el-card>
              </div>
            </div>
          </div>

          <!-- 半决赛 -->
          <div class="bracket-round" v-if="getMatchesByRound('半决赛').length > 0">
            <div class="round-label">半决赛</div>
            <div class="round-matches">
              <div
                v-for="match in getMatchesByRound('半决赛')"
                :key="match.id"
                class="bracket-match-wrapper"
              >
                <div class="bracket-connector bracket-connector-left"></div>
                <div class="bracket-connector bracket-connector-right"></div>
                <el-card class="bracket-match-card" shadow="hover" :body-style="{ padding: '8px 12px' }">
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                    <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                    <span class="bracket-team-name">{{ match.team1 }}</span>
                  </div>
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                    <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                    <span class="bracket-team-name">{{ match.team2 }}</span>
                  </div>
                  <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                </el-card>
              </div>
            </div>
          </div>

          <!-- 决赛 -->
          <div class="bracket-round bracket-round-final" v-if="getMatchesByRound('决赛').length > 0">
            <div class="round-label">决赛</div>
            <div class="round-matches">
              <div
                v-for="match in getMatchesByRound('决赛')"
                :key="match.id"
                class="bracket-match-wrapper"
              >
                <div class="bracket-connector bracket-connector-left"></div>
                <el-card class="bracket-match-card bracket-final-card" shadow="hover" :body-style="{ padding: '12px 16px' }">
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team1) }">
                    <span v-if="match.flag1 && !isPlaceholder(match.team1)" class="bracket-flag">{{ match.flag1 }}</span>
                    <span class="bracket-team-name">{{ match.team1 }}</span>
                  </div>
                  <div class="bracket-team" :class="{ placeholder: isPlaceholder(match.team2) }">
                    <span v-if="match.flag2 && !isPlaceholder(match.team2)" class="bracket-flag">{{ match.flag2 }}</span>
                    <span class="bracket-team-name">{{ match.team2 }}</span>
                  </div>
                  <div class="bracket-match-time">{{ formatTime(match.match_time) }}</div>
                  <div v-if="match.venue" class="bracket-venue">{{ match.venue }}</div>
                </el-card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { matchAPI } from '../api'

const loading = ref(true)
const bracketData = ref([])

const isPlaceholder = (teamName) => {
  if (!teamName) return true
  return teamName.includes('胜者') || teamName.includes('负者') || teamName.includes('待定')
}

const getMatchesByRound = (roundName) => {
  return bracketData.value.filter(m => m.round_name === roundName)
}

const formatTime = (matchTime) => {
  if (!matchTime) return ''
  const parts = matchTime.split(' ')
  if (parts.length >= 2) {
    return parts[1].substring(0, 5)
  }
  return matchTime
}

const fetchBracket = async () => {
  try {
    loading.value = true
    const res = await matchAPI.getKnockoutBracket()
    bracketData.value = res.bracket_data || []
  } catch (error) {
    console.error('获取淘汰赛对阵图数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchBracket()
})
</script>

<style scoped>
.bracket-page {
  padding: 20px;
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.bracket-container {
  width: 100%;
  overflow-x: auto;
}

.bracket-scroll {
  min-width: 900px;
  padding: 20px 0;
}

.bracket-grid {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 600px;
}

.bracket-round {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 180px;
}

.bracket-round-final {
  flex: 0 0 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.round-label {
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  padding: 10px 0;
  border-bottom: 2px solid #0047AB;
  margin-bottom: 16px;
  background: #ecf5ff;
  border-radius: 4px;
}

.round-matches {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex: 1;
  gap: 12px;
  padding: 0 8px;
}

.bracket-round:first-child .round-matches {
  gap: 8px;
}

.match-pair {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex: 1;
  gap: 8px;
}

.bracket-match-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.bracket-match-card {
  width: 100%;
  border-radius: 8px;
  position: relative;
  z-index: 1;
}

.bracket-final-card {
  border: 2px solid #e6a23c;
  background: linear-gradient(135deg, #fdf6ec, #fef0e6);
}

.bracket-team {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bracket-team.placeholder {
  color: #c0c4cc;
  font-style: italic;
}

.bracket-flag {
  font-size: 18px;
  flex-shrink: 0;
}

.bracket-team-name {
  overflow: hidden;
  text-overflow: ellipsis;
}

.bracket-match-time {
  text-align: center;
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed #ebeef5;
}

.bracket-venue {
  text-align: center;
  font-size: 11px;
  color: #b0b5bd;
  margin-top: 2px;
}

/* Connecting lines */
.bracket-connector {
  position: absolute;
  top: 50%;
  width: 16px;
  height: 2px;
  background-color: #c0c4cc;
}

.bracket-connector-left {
  left: -16px;
}

.bracket-connector-right {
  right: -16px;
}

/* Vertical connectors between pairs */
.bracket-round:not(:first-child) .round-matches .bracket-match-wrapper:nth-child(odd) {
  padding-bottom: 0;
}

.bracket-round:not(:first-child) .round-matches .bracket-match-wrapper:nth-child(even) {
  padding-top: 0;
}

@media (max-width: 1024px) {
  .bracket-scroll {
    min-width: 800px;
  }

  .bracket-round {
    min-width: 150px;
  }
}
</style>

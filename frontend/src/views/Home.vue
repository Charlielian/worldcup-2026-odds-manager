<template>
  <div class="home-page" v-loading="loading" element-loading-text="加载中...">
    <!-- 当日比赛 -->
    <section class="section">
      <div class="section-header">
        <el-icon :size="24" color="#0047AB"><Calendar /></el-icon>
        <h2 class="section-title">当日比赛</h2>
        <el-tag type="info" size="large" round>{{ currentDate }}</el-tag>
      </div>

      <div v-if="!loading && dayMatches.length === 0">
        <el-empty description="当日无比赛" :image-size="120">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><Soccer /></el-icon>
          </template>
        </el-empty>
      </div>

      <el-row v-else :gutter="20">
        <el-col
          v-for="match in dayMatches"
          :key="match.id"
          :xs="24"
          :sm="24"
          :md="24"
          :lg="24"
        >
          <el-card class="match-card" shadow="hover">
            <!-- 比赛信息头部 -->
            <div class="match-info-header">
              <div class="match-meta">
                <span class="match-time">{{ match.match_time }}</span>
                <el-tag
                  :type="match.stage === '小组赛' ? 'primary' : 'warning'"
                  size="small"
                  effect="dark"
                  round
                >
                  {{ match.stage }}
                </el-tag>
                <el-tag
                  v-if="match.group_name"
                  type="info"
                  size="small"
                  effect="plain"
                  round
                >
                  {{ match.group_name }}
                </el-tag>
              </div>
              <el-tag
                :type="match.status === 'finished' ? 'success' : 'warning'"
                size="default"
                effect="dark"
                round
              >
                {{ match.status === 'finished' ? '已结束' : '未开始' }}
              </el-tag>
            </div>

            <el-divider style="margin: 12px 0;" />

            <!-- 队伍与比分 -->
            <div class="teams-section">
              <div class="team-block">
                <span class="team-flag">{{ match.flag1 || '' }}</span>
                <span class="team-name">{{ match.team1 }}</span>
              </div>

              <div class="score-block">
                <template v-if="match.status === 'finished'">
                  <span class="score-display">{{ match.score1 }}</span>
                  <span class="score-separator">:</span>
                  <span class="score-display">{{ match.score2 }}</span>
                </template>
                <template v-else>
                  <el-tag type="info" effect="dark" size="large" round>VS</el-tag>
                </template>
              </div>

              <div class="team-block">
                <span class="team-flag">{{ match.flag2 || '' }}</span>
                <span class="team-name">{{ match.team2 }}</span>
              </div>
            </div>

            <!-- 赔率信息 -->
            <div v-if="match.odds" class="odds-section">
              <el-divider style="margin: 12px 0;" />
              <div class="odds-header">
                <span class="odds-title">
                  <el-icon><DataAnalysis /></el-icon>
                  最新赔率
                  <el-tag v-if="match.odds.source" size="small" type="info" effect="plain" style="margin-left: 8px;">
                    {{ match.odds.source }}
                  </el-tag>
                </span>
                <span class="odds-update-time" v-if="match.odds.update_time">
                  更新: {{ match.odds.update_time }}
                </span>
              </div>
              <div class="odds-grid">
                <div class="odds-item">
                  <span class="odds-label">{{ match.team1 }} 胜</span>
                  <span class="odds-value">{{ match.odds.win_odds }}</span>
                </div>
                <div class="odds-item odds-draw">
                  <span class="odds-label">平局</span>
                  <span class="odds-value">{{ match.odds.draw_odds }}</span>
                </div>
                <div class="odds-item">
                  <span class="odds-label">{{ match.team2 }} 胜</span>
                  <span class="odds-value">{{ match.odds.lose_odds }}</span>
                </div>
              </div>
            </div>

            <!-- 比分提交表单（仅未结束比赛） -->
            <div v-if="match.status !== 'finished'" class="score-form-section">
              <el-divider style="margin: 12px 0;" />
              <div class="score-form">
                <div class="score-input-group">
                  <div class="score-input-item">
                    <span class="score-input-label">{{ match.team1 }} 比分</span>
                    <el-input-number
                      v-model="scoreFormMap[match.id].score1"
                      :min="0"
                      :max="99"
                      size="default"
                      controls-position="right"
                      placeholder="0"
                    />
                  </div>
                  <el-button
                    type="primary"
                    @click="submitScore(match)"
                    :loading="submittingMap[match.id]"
                    round
                  >
                    标记比赛结束
                  </el-button>
                  <div class="score-input-item">
                    <span class="score-input-label">{{ match.team2 }} 比分</span>
                    <el-input-number
                      v-model="scoreFormMap[match.id].score2"
                      :min="0"
                      :max="99"
                      size="default"
                      controls-position="right"
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <!-- 往后赛程 -->
    <section class="section upcoming-section">
      <div class="section-header">
        <el-icon :size="24" color="#0047AB"><Trophy /></el-icon>
        <h2 class="section-title">往后赛程</h2>
      </div>

      <div v-if="!loading && Object.keys(groupedUpcoming).length === 0">
        <el-empty description="暂无往后赛程" :image-size="120">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><Calendar /></el-icon>
          </template>
        </el-empty>
      </div>

      <div v-else>
        <div
          v-for="(matches, dateKey) in groupedUpcoming"
          :key="dateKey"
          class="date-group"
        >
          <!-- 日期标题卡片 -->
          <el-card
            class="date-header-card"
            shadow="never"
            @click="navigateToDate(dateKey)"
          >
            <div class="date-header-content">
              <div class="date-header-left">
                <el-icon :size="20" color="#0047AB"><Calendar /></el-icon>
                <span class="date-text">{{ dateKey }}</span>
              </div>
              <el-tag type="primary" size="small" effect="dark" round>
                {{ matches.length }} 场比赛
              </el-tag>
            </div>
          </el-card>

          <!-- 该日期下的比赛卡片 -->
          <el-row :gutter="16">
            <el-col
              v-for="match in matches"
              :key="match.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <el-card class="upcoming-match-card" shadow="hover">
                <div class="upcoming-match-time">{{ match.match_time }}</div>
                <div class="upcoming-teams">
                  <div class="upcoming-team">
                    <span class="upcoming-flag">{{ match.flag1 || '' }}</span>
                    <span class="upcoming-team-name">{{ match.team1 }}</span>
                  </div>
                  <span class="upcoming-vs">VS</span>
                  <div class="upcoming-team">
                    <span class="upcoming-flag">{{ match.flag2 || '' }}</span>
                    <span class="upcoming-team-name">{{ match.team2 }}</span>
                  </div>
                </div>
                <div class="upcoming-match-status">
                  <el-tag
                    :type="match.status === 'finished' ? 'success' : 'warning'"
                    size="small"
                    effect="plain"
                    round
                  >
                    {{ match.status === 'finished' ? '已结束' : '未开始' }}
                  </el-tag>
                  <el-tag
                    v-if="match.stage"
                    :type="match.stage === '小组赛' ? 'primary' : 'warning'"
                    size="small"
                    effect="plain"
                    round
                  >
                    {{ match.stage }}
                  </el-tag>
                </div>
                <div v-if="match.status === 'finished'" class="upcoming-score">
                  {{ match.score1 }} : {{ match.score2 }}
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, Trophy, Soccer, DataAnalysis } from '@element-plus/icons-vue'
import { matchAPI } from '../api'
import { debounce } from 'lodash-es'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const dayMatches = ref([])
const upcomingMatches = ref([])
const scoreFormMap = reactive({})
const submittingMap = reactive({})

const currentDate = computed(() => {
  return route.query.date || new Date().toISOString().split('T')[0]
})

// 按日期分组后续赛程
const groupedUpcoming = computed(() => {
  const grouped = {}
  upcomingMatches.value.forEach((match) => {
    const matchDate = match.match_time ? match.match_time.split(' ')[0] : ''
    if (!matchDate) return
    if (!grouped[matchDate]) {
      grouped[matchDate] = []
    }
    grouped[matchDate].push(match)
  })
  return grouped
})

// 初始化比分表单
const initScoreForms = () => {
  dayMatches.value.forEach((match) => {
    if (!(match.id in scoreFormMap)) {
      scoreFormMap[match.id] = { score1: 0, score2: 0 }
    }
    if (!(match.id in submittingMap)) {
      submittingMap[match.id] = false
    }
  })
}

// 获取比赛数据
const fetchMatches = async (date) => {
  try {
    loading.value = true
    const data = await matchAPI.getMatchesByDate(date)
    dayMatches.value = data.day_matches || []
    upcomingMatches.value = data.upcoming_matches || []
    initScoreForms()
  } catch (error) {
    console.error('获取比赛数据失败:', error)
    ElMessage.error('获取比赛数据失败')
  } finally {
    loading.value = false
  }
}

// 防抖版本的数据获取（300ms），用于日期快速切换时避免频繁请求
const debouncedFetchMatches = debounce((date) => {
  fetchMatches(date)
}, 300)

// 提交比分
const submitScore = async (match) => {
  const form = scoreFormMap[match.id]
  if (form.score1 === null || form.score2 === null || form.score1 === undefined || form.score2 === undefined) {
    ElMessage.warning('请输入完整的比分')
    return
  }

  try {
    submittingMap[match.id] = true
    await matchAPI.updateMatchResult(match.id, form.score1, form.score2)
    ElMessage.success('比赛结果已更新')
    // 重新获取数据
    await fetchMatches(currentDate.value)
  } catch (error) {
    console.error('更新比赛结果失败:', error)
    ElMessage.error('更新失败，请重试')
  } finally {
    submittingMap[match.id] = false
  }
}

// 导航到指定日期
const navigateToDate = (date) => {
  router.push({ path: '/', query: { date } })
}

// 监听日期查询参数变化（使用防抖避免快速切换日期时频繁请求API）
watch(
  () => route.query.date,
  (newDate) => {
    if (newDate) {
      debouncedFetchMatches(newDate)
    }
  }
)

onMounted(() => {
  fetchMatches(currentDate.value)
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* 区块样式 */
.section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin: 0;
  flex: 1;
}

/* 比赛卡片 */
.match-card {
  margin-bottom: 20px;
  border-radius: 12px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.match-card:hover {
  transform: translateY(-2px);
}

.match-card :deep(.el-card__body) {
  padding: 20px 24px;
}

/* 比赛信息头部 */
.match-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.match-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-time {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

/* 队伍区域 */
.teams-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
}

.team-block {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.team-block:last-child {
  justify-content: flex-end;
}

.team-flag {
  font-size: 32px;
  line-height: 1;
}

.team-name {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.score-block {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  flex-shrink: 0;
}

.score-display {
  font-size: 28px;
  font-weight: 800;
  color: #0047AB;
  min-width: 30px;
  text-align: center;
}

.score-separator {
  font-size: 24px;
  color: #909399;
  font-weight: 600;
}

/* 赔率区域 */
.odds-section {
  margin-top: 4px;
}

.odds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.odds-title {
  font-size: 14px;
  font-weight: 600;
  color: #0047AB;
  display: flex;
  align-items: center;
  gap: 6px;
}

.odds-update-time {
  font-size: 12px;
  color: #c0c4cc;
}

.odds-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.odds-item {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s ease;
}

.odds-item:hover {
  background-color: #ecf5ff;
}

.odds-item.odds-draw {
  background-color: #fdf6ec;
}

.odds-item.odds-draw:hover {
  background-color: #faecd8;
}

.odds-label {
  font-size: 13px;
  color: #606266;
}

.odds-value {
  font-size: 16px;
  font-weight: 700;
  color: #0047AB;
}

.odds-draw .odds-value {
  color: #e6a23c;
}

/* 比分提交表单 */
.score-form-section {
  margin-top: 4px;
}

.score-form {
  padding: 4px 0;
}

.score-input-group {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 16px;
}

.score-input-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.score-input-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

/* 往后赛程区域 */
.upcoming-section {
  margin-top: 48px;
}

.date-group {
  margin-bottom: 28px;
}

.date-header-card {
  cursor: pointer;
  margin-bottom: 16px;
  border-radius: 10px;
  border-left: 4px solid #0047AB;
  transition: all 0.3s ease;
}

.date-header-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 71, 171, 0.15);
}

.date-header-card :deep(.el-card__body) {
  padding: 14px 20px;
}

.date-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-text {
  font-size: 17px;
  font-weight: 700;
  color: #0047AB;
}

/* 后续比赛小卡片 */
.upcoming-match-card {
  margin-bottom: 12px;
  border-radius: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.upcoming-match-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.upcoming-match-card :deep(.el-card__body) {
  padding: 16px;
}

.upcoming-match-time {
  font-size: 13px;
  color: #909399;
  margin-bottom: 10px;
  font-weight: 500;
}

.upcoming-teams {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.upcoming-team {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.upcoming-team:last-child {
  justify-content: flex-end;
}

.upcoming-flag {
  font-size: 22px;
  line-height: 1;
  flex-shrink: 0;
}

.upcoming-team-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upcoming-vs {
  font-size: 12px;
  font-weight: 700;
  color: #c0c4cc;
  flex-shrink: 0;
  padding: 0 6px;
}

.upcoming-match-status {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.upcoming-score {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0047AB;
  text-align: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .teams-section {
    flex-direction: column;
    gap: 12px;
  }

  .team-block {
    justify-content: center !important;
  }

  .score-block {
    padding: 0;
  }

  .score-input-group {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .score-input-item {
    flex-direction: row;
    justify-content: space-between;
  }

  .odds-grid {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 18px;
  }

  .team-name {
    font-size: 16px;
  }
}
</style>

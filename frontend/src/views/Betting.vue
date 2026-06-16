<template>
  <div class="betting-page" v-loading="loading" element-loading-text="加载比赛数据中...">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-main">
        <el-icon :size="32" color="#0047AB"><Trophy /></el-icon>
        <div class="title-wrapper">
          <h1 class="page-title">投注全景</h1>
          <p class="page-subtitle">选择比赛和比分，查看赔率与胜率分析</p>
        </div>
      </div>
    </div>

    <!-- 两栏布局 -->
    <el-row :gutter="20" v-if="availableMatches.length > 0 || selectedMatch">

      <!-- 左侧：比赛列表 -->
      <el-col :xs="24" :sm="7" :md="5" :lg="4">
        <div class="left-panel">
          <div class="left-panel-header">
            <el-icon :size="16" color="#0047AB"><Trophy /></el-icon>
            <span class="left-panel-title">比赛列表</span>
            <span class="match-count">{{ availableMatches.length }} 场</span>
            <el-button type="primary" size="small" :icon="Refresh" circle @click="fetchMatches" class="refresh-btn" />
          </div>
          <div class="match-list-scroll">
            <div
              v-for="m in availableMatches"
              :key="m.id"
              class="match-list-item"
              :class="{ active: selectedMatchId === m.id }"
              @click="selectMatch(m)"
            >
              <div class="mli-team-row">
                <span class="mli-flag">{{ m.flag1 }}</span>
                <span class="mli-name">{{ m.team1 }}</span>
              </div>
              <div class="mli-center">
                <span class="mli-vs">VS</span>
                <span class="mli-time">{{ m.match_time }}</span>
              </div>
              <div class="mli-team-row">
                <span class="mli-flag">{{ m.flag2 }}</span>
                <span class="mli-name">{{ m.team2 }}</span>
              </div>
              <div class="mli-footer">
                <el-tag size="small" effect="plain" round>{{ m.group_name || m.stage }}</el-tag>
              </div>
            </div>
            <el-empty v-if="availableMatches.length === 0 && !loading" description="暂无比赛" :image-size="60" />
          </div>
        </div>
      </el-col>

      <!-- 右侧：投注主内容 -->
      <el-col :xs="24" :sm="17" :md="19" :lg="20">
        <div class="right-panel" v-if="selectedMatch">

          <!-- 当前比赛展示卡 -->
          <el-card class="main-match-card" shadow="hover">
            <div class="match-big-display">
              <div class="team-block left-team">
                <div class="flag-big">{{ selectedMatch.flag1 }}</div>
                <div class="team-name-big">{{ selectedMatch.team1 }}</div>
              </div>
              <div class="center-block">
                <div class="vs-badge">VS</div>
                <div class="match-info-lines">
                  <div class="info-line"><el-icon><Calendar /></el-icon><span>{{ selectedMatch.match_time }}</span></div>
                  <div class="info-line"><el-icon><Trophy /></el-icon><span>{{ selectedMatch.group_name || selectedMatch.stage }}</span></div>
                </div>
              </div>
              <div class="team-block right-team">
                <div class="flag-big">{{ selectedMatch.flag2 }}</div>
                <div class="team-name-big">{{ selectedMatch.team2 }}</div>
              </div>
            </div>
            <div class="live-odds-summary" v-if="selectedMatch.odds">
              <div class="odds-box"><span class="odds-label">{{ selectedMatch.team1 }} 胜</span><span class="odds-number win">{{ selectedMatch.odds.win_odds }}</span></div>
              <div class="odds-box"><span class="odds-label">平局</span><span class="odds-number draw">{{ selectedMatch.odds.draw_odds }}</span></div>
              <div class="odds-box"><span class="odds-label">{{ selectedMatch.team2 }} 胜</span><span class="odds-number lose">{{ selectedMatch.odds.lose_odds }}</span></div>
            </div>
            <el-alert v-else type="info" :closable="false" title="暂无赔率数据，下方显示为模拟赔率（基于标准足球比赛分布推算）。" />
          </el-card>

          <!-- 比分投注区 + 投注记录 -->
          <el-row :gutter="16">

            <!-- 比分投注 + 全景表 -->
            <el-col :xs="24" :md="14">
              <el-card class="score-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <el-icon :size="18" color="#0047AB"><Trophy /></el-icon>
                    <span class="card-header-title">比分投注</span>
                  </div>
                </template>
                <div class="score-input-area">
                  <div class="score-inputs-row">
                    <div class="score-input-box">
                      <label>{{ selectedMatch.team1 }}</label>
                      <el-input-number v-model="betScore1" :min="0" :max="15" :step="1" size="large" controls-position="right" class="score-num-input" />
                    </div>
                    <div class="score-colon">:</div>
                    <div class="score-input-box">
                      <label>{{ selectedMatch.team2 }}</label>
                      <el-input-number v-model="betScore2" :min="0" :max="15" :step="1" size="large" controls-position="right" class="score-num-input" />
                    </div>
                  </div>
                  <div class="quick-scores-row">
                    <span class="quick-scores-label">快捷比分：</span>
                    <el-button v-for="sc in quickScores" :key="sc.label" :type="betScore1 === sc.s1 && betScore2 === sc.s2 ? 'primary' : 'default'" size="small" round @click="betScore1 = sc.s1; betScore2 = sc.s2">{{ sc.s1 }}:{{ sc.s2 }}</el-button>
                  </div>
                </div>
                <el-divider />
                <div class="bet-calc-grid">
                  <div class="calc-item highlight">
                    <div class="calc-label">当前比分</div>
                    <div class="calc-value big">{{ betScore1 }} : {{ betScore2 }}</div>
                    <div class="calc-sub">{{ outcomeLabel }}</div>
                  </div>
                  <div class="calc-item">
                    <div class="calc-label">比分赔率</div>
                    <div class="calc-value big">{{ scoreOdds.toFixed(2) }}</div>
                    <div class="calc-sub">标准赔率推算</div>
                  </div>
                  <div class="calc-item">
                    <div class="calc-label">预计收益</div>
                    <div class="calc-value big success">¥ {{ netProfit.toFixed(2) }}</div>
                    <div class="calc-sub">（¥100投注）</div>
                  </div>
                  <div class="calc-item">
                    <div class="calc-label">命中概率</div>
                    <div class="calc-value big warn">{{ scoreProbability }}%</div>
                    <div class="calc-sub">该比分概率</div>
                  </div>
                </div>
                <div class="confirm-bet-row">
                  <el-input-number v-model="betAmount" :min="10" :max="100000" :step="10" size="large" controls-position="right" style="width: 180px" />
                  <el-button type="primary" size="large" @click="placeBet">确认投注 {{ betScore1 }}:{{ betScore2 }}（¥{{ betAmount }}）</el-button>
                </div>
              </el-card>

              <el-card class="panorama-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <el-icon :size="18" color="#0047AB"><DataAnalysis /></el-icon>
                    <span class="card-header-title">投注全景：各比分赔率 / 收益 / 概率</span>
                  </div>
                </template>
                <div class="panorama-intro">以 <b>¥{{ betAmount }}</b> 投注金额计算：投注金额越高，冷门比分潜在收益越大，命中概率越低。</div>
                <el-table :data="panoramaRows" stripe border size="small" :row-class-name="panoramaRowClass" style="width: 100%">
                  <el-table-column label="#" type="index" width="45" align="center" />
                  <el-table-column prop="score" label="比分" width="90" align="center">
                    <template #default="{ row }"><span class="score-cell" :class="row.outcomeClass">{{ row.score }}</span></template>
                  </el-table-column>
                  <el-table-column prop="outcome" label="结果" width="100" align="center" />
                  <el-table-column prop="odds" label="赔率" width="85" align="center">
                    <template #default="{ row }"><span class="odds-cell">{{ row.odds }}</span></template>
                  </el-table-column>
                  <el-table-column prop="prob" label="概率" width="90" align="center">
                    <template #default="{ row }">
                      <el-progress :percentage="row.probValue" :color="progressColor(row.probValue)" :stroke-width="8" :format="() => row.prob" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="prize" label="奖金(¥)" width="100" align="center">
                    <template #default="{ row }"><span class="prize-cell">{{ row.prize }}</span></template>
                  </el-table-column>
                  <el-table-column prop="profit" label="净收益(¥)" width="110" align="center">
                    <template #default="{ row }"><span class="profit-cell">{{ row.profit }}</span></template>
                  </el-table-column>
                  <el-table-column label="选投" width="90" align="center" fixed="right">
                    <template #default="{ row }">
                      <el-button size="small" :type="row.isSelected ? 'success' : 'primary'" text @click="pickFromPanorama(row)">{{ row.isSelected ? '已选' : '选择' }}</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>

            <!-- 右侧胜率分析 + 投注历史 -->
            <el-col :xs="24" :md="10">
              <el-card class="side-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <el-icon :size="18" color="#67c23a"><DataAnalysis /></el-icon>
                    <span class="card-header-title">胜负平 / 总进球数 胜率</span>
                  </div>
                </template>
                <div class="prob-section">
                  <div class="prob-line">
                    <div class="prob-head"><span class="prob-label">{{ selectedMatch.team1 }} 胜</span><span class="prob-value">{{ matchWinProb }}%</span></div>
                    <el-progress :percentage="matchWinProb" color="#409eff" :stroke-width="12" />
                    <span class="prob-odds">赔率 {{ selectedMatch.odds?.win_odds || defaultBaseOdds }}</span>
                  </div>
                  <div class="prob-line">
                    <div class="prob-head"><span class="prob-label">平局</span><span class="prob-value">{{ matchDrawProb }}%</span></div>
                    <el-progress :percentage="matchDrawProb" color="#e6a23c" :stroke-width="12" />
                    <span class="prob-odds">赔率 {{ selectedMatch.odds?.draw_odds || defaultDrawOdds }}</span>
                  </div>
                  <div class="prob-line">
                    <div class="prob-head"><span class="prob-label">{{ selectedMatch.team2 }} 胜</span><span class="prob-value">{{ matchLoseProb }}%</span></div>
                    <el-progress :percentage="matchLoseProb" color="#67c23a" :stroke-width="12" />
                    <span class="prob-odds">赔率 {{ selectedMatch.odds?.lose_odds || defaultBaseOdds }}</span>
                  </div>
                </div>
                <el-divider content-position="left">总进球数概率</el-divider>
                <div class="goals-grid">
                  <div v-for="gi in goalsInfo" :key="gi.label" class="goals-item">
                    <div class="goals-top"><span class="goals-label">{{ gi.label }}</span><span class="goals-value">{{ gi.prob }}%</span></div>
                    <el-progress :percentage="gi.probValue" :color="progressColor(gi.probValue)" :stroke-width="8" :format="() => ''" />
                    <span class="goals-odds">赔率 {{ gi.odds }}</span>
                  </div>
                </div>
              </el-card>

              <el-card class="side-card history-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <el-icon :size="18" color="#f56c6c"><Clock /></el-icon>
                    <span class="card-header-title">投注历史（本地）</span>
                    <el-button v-if="betHistory.length > 0" type="danger" size="small" text @click="clearHistory">清空</el-button>
                  </div>
                </template>
                <el-empty v-if="betHistory.length === 0" description="暂无投注记录" :image-size="60" />
                <el-timeline v-else>
                  <el-timeline-item v-for="(b, idx) in betHistory" :key="idx" :timestamp="b.time" placement="top" :type="b.type">
                    <el-card class="history-item" shadow="never">
                      <div class="history-match">
                        <span class="hf">{{ b.flag1 }}</span><span>{{ b.team1 }}</span><span class="hm">vs</span><span class="hf">{{ b.flag2 }}</span><span>{{ b.team2 }}</span>
                      </div>
                      <div class="history-score">
                        <el-tag type="primary" round size="small">投注 {{ b.s1 }}:{{ b.s2 }}</el-tag>
                        <span class="history-odds">赔率 {{ b.odds }}</span>
                      </div>
                      <div class="history-amount">
                        <span class="amount">¥{{ b.amount }}</span>
                        <el-divider direction="vertical" />
                        <span class="profit-label">奖金</span>
                        <span class="profit-val">¥{{ b.prize }}</span>
                      </div>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-col>

          </el-row>
        </div>
        <el-empty v-else description="请从左侧选择一场比赛" :image-size="100" />
      </el-col>

    </el-row>

    <el-empty v-if="!loading && availableMatches.length === 0 && !selectedMatch" description="暂无进行中的比赛" :image-size="100" />

    <!-- 投注确认弹窗 -->
    <el-dialog v-model="showConfirm" width="460px" title="确认投注">
      <div class="confirm-content">
        <div class="confirm-meta">
          <div class="confirm-teams">
            <span>{{ selectedMatch?.flag1 }}</span><span>{{ selectedMatch?.team1 }}</span>
            <span class="vs-small">vs</span>
            <span>{{ selectedMatch?.team2 }}</span><span>{{ selectedMatch?.flag2 }}</span>
          </div>
          <div class="confirm-score">
            <el-tag type="primary" size="large" round>比分：{{ betScore1 }}:{{ betScore2 }}</el-tag>
          </div>
        </div>
        <el-descriptions :column="1" border size="default" class="confirm-desc">
          <el-descriptions-item label="投注金额">¥ {{ betAmount }}</el-descriptions-item>
          <el-descriptions-item label="比分赔率">{{ scoreOdds.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="潜在奖金">¥ {{ (betAmount * scoreOdds).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="净收益">¥ {{ (betAmount * scoreOdds - betAmount).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="命中概率">{{ scoreProbability }}%</el-descriptions-item>
          <el-descriptions-item label="比赛时间">{{ selectedMatch?.match_time }}</el-descriptions-item>
        </el-descriptions>
        <el-alert type="warning" :closable="false" title="提示：投注有风险，请理性投注。此为模拟系统，不会产生真实交易。" />
      </div>
      <template #footer>
        <el-button @click="showConfirm = false">取消</el-button>
        <el-button type="primary" @click="confirmBet">确认投注</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Trophy, Calendar, DataAnalysis, Clock, Refresh } from '@element-plus/icons-vue'
import { matchAPI } from '../api'

const STORAGE_KEY = 'worldcup_bet_history_v1'

const loading = ref(false)
const availableMatches = ref([])
const selectedMatchId = ref(null)
const betScore1 = ref(2)
const betScore2 = ref(1)
const betAmount = ref(100)
const showConfirm = ref(false)
const betHistory = ref([])

const quickScores = [
  { label: '1-0', s1: 1, s2: 0 },
  { label: '2-0', s1: 2, s2: 0 },
  { label: '2-1', s1: 2, s2: 1 },
  { label: '3-1', s1: 3, s2: 1 },
  { label: '3-2', s1: 3, s2: 2 },
  { label: '1-1', s1: 1, s2: 1 },
  { label: '0-0', s1: 0, s2: 0 },
  { label: '0-1', s1: 0, s2: 1 },
]

const defaultBaseOdds = 2.5
const defaultDrawOdds = 3.2

const selectedMatch = computed(() => availableMatches.value.find(m => m.id === selectedMatchId.value) || null)
const winOdds = computed(() => parseFloat(selectedMatch.value?.odds?.win_odds) || defaultBaseOdds)
const drawOdds = computed(() => parseFloat(selectedMatch.value?.odds?.draw_odds) || defaultDrawOdds)
const loseOdds = computed(() => parseFloat(selectedMatch.value?.odds?.lose_odds) || defaultBaseOdds)

const _impliedTotal = computed(() => (1 / winOdds.value) + (1 / drawOdds.value) + (1 / loseOdds.value))
const matchWinProb = computed(() => Math.round((1 / winOdds.value) / _impliedTotal.value * 100))
const matchDrawProb = computed(() => Math.round((1 / drawOdds.value) / _impliedTotal.value * 100))
const matchLoseProb = computed(() => Math.round((1 / loseOdds.value) / _impliedTotal.value * 100))

const outcome = computed(() => {
  if (betScore1.value > betScore2.value) return 'home'
  if (betScore1.value < betScore2.value) return 'away'
  return 'draw'
})

const outcomeLabel = computed(() => {
  if (outcome.value === 'home') return selectedMatch.value?.team1 + ' 胜'
  if (outcome.value === 'away') return selectedMatch.value?.team2 + ' 胜'
  return '平局'
})

function calcScoreOdds(s1, s2) {
  const win = winOdds.value
  const draw = drawOdds.value
  const lose = loseOdds.value
  if (s1 > s2) {
    const diff = s1 - s2
    const goals = s1 + s2
    return +(win * (1 + (diff - 1) * 0.35) * (1 + goals * 0.08)).toFixed(2)
  } else if (s1 === s2) {
    return +(draw * (1 + s1 * 0.15)).toFixed(2)
  } else {
    const diff = s2 - s1
    const goals = s1 + s2
    return +(lose * (1 + (diff - 1) * 0.35) * (1 + goals * 0.08)).toFixed(2)
  }
}

const scoreOdds = computed(() => calcScoreOdds(betScore1.value, betScore2.value))
const scoreProbability = computed(() => scoreOdds.value > 0 ? ((1 / scoreOdds.value) * 100 * 0.85).toFixed(1) : '0')
const prize = computed(() => +(betAmount.value * scoreOdds.value).toFixed(2))
const netProfit = computed(() => +(prize.value - betAmount.value).toFixed(2))

const panoramaRows = computed(() => {
  if (!selectedMatch.value) return []
  const scores = [
    { s1: 1, s2: 0 }, { s1: 2, s2: 0 }, { s1: 2, s2: 1 },
    { s1: 3, s2: 0 }, { s1: 3, s2: 1 }, { s1: 3, s2: 2 },
    { s1: 0, s2: 0 }, { s1: 1, s2: 1 }, { s1: 2, s2: 2 },
    { s1: 0, s2: 1 }, { s1: 0, s2: 2 }, { s1: 1, s2: 2 },
    { s1: 2, s2: 3 }, { s1: 4, s2: 3 }, { s1: 3, s2: 4 },
  ]
  return scores.map(sc => {
    const odds = calcScoreOdds(sc.s1, sc.s2)
    const prize2 = +(betAmount.value * odds).toFixed(2)
    const profit = +(prize2 - betAmount.value).toFixed(2)
    const prob = ((1 / odds) * 100 * 0.85).toFixed(1)
    let outcomeType = '平局'
    let outcomeClass = 'out-draw'
    if (sc.s1 > sc.s2) {
      outcomeType = selectedMatch.value.team1 + '胜'
      outcomeClass = 'out-home'
    } else if (sc.s1 < sc.s2) {
      outcomeType = selectedMatch.value.team2 + '胜'
      outcomeClass = 'out-away'
    }
    return {
      score: `${sc.s1}:${sc.s2}`, s1: sc.s1, s2: sc.s2,
      outcome: outcomeType, outcomeClass,
      odds: odds.toFixed(2), prob: prob + '%',
      probValue: Math.min(100, Math.round(parseFloat(prob))),
      prize: prize2.toFixed(2),
      profit: profit >= 0 ? '+' + profit.toFixed(2) : profit.toFixed(2),
      isSelected: sc.s1 === betScore1.value && sc.s2 === betScore2.value,
    }
  }).sort((a, b) => parseFloat(a.odds) - parseFloat(b.odds))
})

function panoramaRowClass({ row }) { return row.isSelected ? 'row-selected' : '' }
function progressColor(val) {
  if (val > 20) return '#67c23a'
  if (val > 8) return '#409eff'
  if (val > 3) return '#e6a23c'
  return '#f56c6c'
}

const goalsInfo = computed(() => {
  if (!selectedMatch.value) return []
  const total = (1 / winOdds.value + 1 / loseOdds.value) * 2.2
  function poisson(lambda, k) {
    let sum = 0
    for (let i = 0; i <= k; i++) {
      let fact = 1
      for (let j = 2; j <= i; j++) fact *= j
      sum += (Math.pow(lambda, i) * Math.exp(-lambda)) / fact
    }
    return sum
  }
  const lambda = Math.max(1.5, Math.min(3.5, total))
  const under = Math.round(poisson(lambda, 1) * 100 * 0.85)
  const two = Math.round((poisson(lambda, 2) - poisson(lambda, 1)) * 100 * 0.85)
  const three = Math.round((poisson(lambda, 3) - poisson(lambda, 2)) * 100 * 0.85)
  const over = Math.max(0, 100 - under - two - three)
  return [
    { label: '0-1 球', prob: under, probValue: under, odds: (100 / (under || 1)).toFixed(2) },
    { label: '2 球', prob: two, probValue: two, odds: (100 / (two || 1)).toFixed(2) },
    { label: '3 球', prob: three, probValue: three, odds: (100 / (three || 1)).toFixed(2) },
    { label: '≥4 球', prob: over, probValue: over, odds: (100 / (over || 1)).toFixed(2) },
  ]
})

const fetchMatches = async () => {
  try {
    loading.value = true
    const data = await matchAPI.getMatchesByDate(new Date().toISOString().split('T')[0])
    availableMatches.value = [...(data.day_matches || []), ...(data.upcoming_matches || [])].filter(m => m.status !== 'finished')
    if (availableMatches.value.length > 0 && !selectedMatchId.value) {
      selectedMatchId.value = availableMatches.value[0].id
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const selectMatch = (m) => {
  selectedMatchId.value = m.id
  betScore1.value = 2
  betScore2.value = 1
}

const pickFromPanorama = (row) => { betScore1.value = row.s1; betScore2.value = row.s2 }
const placeBet = () => { showConfirm.value = true }

const confirmBet = () => {
  if (!selectedMatch.value) return
  betHistory.value.unshift({
    id: Date.now(),
    team1: selectedMatch.value.team1, team2: selectedMatch.value.team2,
    flag1: selectedMatch.value.flag1, flag2: selectedMatch.value.flag2,
    s1: betScore1.value, s2: betScore2.value,
    odds: scoreOdds.value.toFixed(2),
    amount: betAmount.value, prize: prize.value,
    time: new Date().toLocaleString('zh-CN'), type: 'primary',
  })
  saveHistory()
  showConfirm.value = false
  ElMessage.success('投注已记录！')
}

const saveHistory = () => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(betHistory.value.slice(0, 20))) } catch (_) {} }
const loadHistory = () => { try { const v = localStorage.getItem(STORAGE_KEY); if (v) betHistory.value = JSON.parse(v) } catch (_) {} }

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有投注历史吗？', '提示', { confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning' })
    betHistory.value = []
    saveHistory()
    ElMessage.success('已清空')
  } catch (_) {}
}

watch(selectedMatchId, () => { betScore1.value = 2; betScore2.value = 1 })
onMounted(() => { loadHistory(); fetchMatches() })
</script>

<style scoped>
.betting-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 4px 24px 4px; }
.header-main { display: flex; align-items: center; gap: 14px; }
.title-wrapper h1 { font-size: 28px; font-weight: 700; color: #0047AB; margin: 0; }
.page-subtitle { font-size: 13px; color: #909399; margin: 4px 0 0 0; }

/* 左侧比赛列表 */
.left-panel { background: #fff; border-radius: 12px; padding: 0 0 12px 0; border: 1px solid #ebeef5; }
.left-panel-header { display: flex; align-items: center; gap: 6px; padding: 14px 14px 10px 14px; border-bottom: 1px solid #f0f0f0; }
.left-panel-title { font-size: 14px; font-weight: 600; color: #303133; flex: 1; }
.match-count { font-size: 12px; color: #909399; background: #f5f7fa; padding: 2px 8px; border-radius: 10px; }
.refresh-btn { padding: 6px !important; }
.match-list-scroll { max-height: calc(100vh - 220px); overflow-y: auto; padding: 8px; }
.match-list-item { border: 2px solid #ebeef5; border-radius: 10px; padding: 10px 12px; cursor: pointer; transition: all 0.2s; margin-bottom: 8px; }
.match-list-item:hover { border-color: #0047AB; transform: translateX(3px); }
.match-list-item.active { border-color: #0047AB; background: linear-gradient(135deg, rgba(0,71,171,.06), rgba(64,158,255,.06)); box-shadow: 0 4px 12px rgba(0,71,171,.15); }
.mli-team-row { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: #303133; }
.mli-center { display: flex; align-items: center; justify-content: center; gap: 6px; margin: 5px 0; }
.mli-vs { font-size: 11px; font-weight: 800; color: #909399; letter-spacing: 1px; }
.mli-time { font-size: 11px; color: #909399; }
.mli-flag { font-size: 16px; }
.mli-footer { display: flex; justify-content: center; margin-top: 4px; }

/* 右侧主内容 */
.right-panel { }
.main-match-card { margin-bottom: 16px; border-radius: 12px; }
.match-big-display { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 8px 0 16px 0; }
.team-block { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.flag-big { font-size: 42px; }
.team-name-big { font-size: 20px; font-weight: 700; color: #0047AB; }
.right-team .team-name-big { color: #67c23a; }
.center-block { text-align: center; padding: 0 12px; }
.vs-badge { display: inline-block; font-size: 16px; font-weight: 800; letter-spacing: 2px; color: #ffc107; background: #002244; padding: 6px 14px; border-radius: 20px; margin-bottom: 8px; }
.match-info-lines { font-size: 12px; color: #606266; }
.info-line { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 3px; }
.live-odds-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.odds-box { background: #f5f7fa; border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
.odds-label { font-size: 12px; color: #606266; }
.odds-number { font-size: 18px; font-weight: 700; }
.odds-number.win { color: #409eff }
.odds-number.draw { color: #e6a23c }
.odds-number.lose { color: #67c23a }

/* 比分投注卡 */
.score-card, .panorama-card, .side-card { margin-bottom: 16px; border-radius: 12px; }
.card-header { display: flex; align-items: center; gap: 8px; }
.card-header-title { font-size: 15px; font-weight: 600; color: #303133; }
.score-input-area { padding: 4px 0 10px 0; }
.score-inputs-row { display: flex; justify-content: center; align-items: center; gap: 16px; }
.score-input-box { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.score-input-box label { font-size: 12px; color: #606266; font-weight: 600; }
.score-colon { font-size: 28px; font-weight: 700; color: #303133; margin-top: 20px; }
.quick-scores-row { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 14px; padding-top: 12px; border-top: 1px dashed #e4e7ed; }
.quick-scores-label { font-size: 12px; color: #606266; margin-right: 2px; }
.bet-calc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 2px 0 14px 0; }
.calc-item { background: #f5f7fa; border-radius: 8px; padding: 10px; text-align: center; }
.calc-item.highlight { background: linear-gradient(135deg, #ecf5ff, #fdf6ec); }
.calc-label { font-size: 11px; color: #606266; margin-bottom: 4px; }
.calc-value.big { font-size: 20px; font-weight: 700; color: #303133; }
.calc-value.success { color: #67c23a }
.calc-value.warn { color: #e6a23c }
.calc-sub { font-size: 10px; color: #909399; margin-top: 3px; }
.confirm-bet-row { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 14px; }

/* 全景表 */
.panorama-intro { padding: 8px 12px; background: #ecf5ff; border-radius: 8px; font-size: 12px; color: #0047AB; margin-bottom: 10px; }
.score-cell { font-weight: 700; font-size: 13px; }
.score-cell.out-home { color: #409eff }
.score-cell.out-draw { color: #e6a23c }
.score-cell.out-away { color: #67c23a }
.odds-cell { font-size: 14px; font-weight: 700; color: #0047AB; }
.prize-cell { font-size: 13px; font-weight: 700; color: #f56c6c; }
.profit-cell { font-size: 13px; font-weight: 700; color: #67c23a; }
:deep(.el-table__row.row-selected td) { background-color: rgba(0,71,171,.08) !important; }

/* 胜率分析 */
.prob-section { padding: 4px 0 8px 0; }
.prob-line { margin-bottom: 14px; }
.prob-head { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; }
.prob-value { font-weight: 700; color: #303133; }
.prob-odds { font-size: 11px; color: #909399; display: block; text-align: right; margin-top: 3px; }
.goals-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.goals-item { background: #f5f7fa; padding: 8px; border-radius: 8px; }
.goals-top { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; color: #606266; }
.goals-value { font-weight: 700; color: #303133; }
.goals-odds { display: block; text-align: right; font-size: 11px; color: #0047AB; font-weight: 700; margin-top: 3px; }

/* 历史 */
.history-item { background: #f5f7fa; border-radius: 8px; padding: 8px 10px; font-size: 12px; }
.history-match { display: flex; align-items: center; gap: 4px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.hf { font-size: 16px }
.hm { color: #909399; font-weight: 400 }
.history-score { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-odds { font-size: 11px; color: #0047AB; font-weight: 700; }
.history-amount { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.amount { font-weight: 700; color: #303133; }
.profit-label { color: #909399; }
.profit-val { font-weight: 700; color: #67c23a; }

/* 确认弹窗 */
.confirm-content { padding: 4px 0; }
.confirm-meta { text-align: center; margin-bottom: 14px; }
.confirm-teams { display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 8px; }
.vs-small { color: #909399; font-weight: 400; }
.confirm-score { margin-top: 5px; }
.confirm-desc { margin: 8px 0 12px 0; }

/* 响应式 */
@media (max-width: 992px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .match-big-display { flex-direction: column; gap: 12px; }
  .team-block { flex-direction: row; }
  .live-odds-summary { grid-template-columns: 1fr; }
  .bet-calc-grid { grid-template-columns: 1fr 1fr; }
  .title-wrapper h1 { font-size: 22px }
  .flag-big { font-size: 32px }
  .team-name-big { font-size: 16px }
}
@media (max-width: 768px) {
  .goals-grid { grid-template-columns: 1fr }
  .score-inputs-row { flex-direction: column; gap: 10px; }
  .confirm-bet-row { flex-direction: column; }
  .quick-scores-row { justify-content: center; }
}
</style>

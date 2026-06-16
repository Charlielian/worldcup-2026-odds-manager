<template>
  <div class="betting-page" v-loading="loading" element-loading-text="加载体彩数据中...">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-main">
        <el-icon :size="32" color="#0047AB"><Trophy /></el-icon>
        <div class="title-wrapper">
          <h1 class="page-title">投注中心</h1>
          <p class="page-subtitle">中国体彩竞彩足球 · 胜平负 / 让球 / 比分 / 总进球 / 半全场</p>
        </div>
      </div>
      <div class="header-right">
        <el-tag type="info" effect="plain">
          <el-icon :size="12"><Clock /></el-icon>
          {{ currentTime }}
        </el-tag>
        <el-button type="primary" :icon="Refresh" size="small" @click="fetchLiveMatches">刷新数据</el-button>
      </div>
    </div>

    <!-- 两栏布局 -->
    <el-row :gutter="16">

      <!-- 左侧：比赛列表 -->
      <el-col :xs="24" :sm="6" :md="5" :lg="4">
        <div class="left-panel">
          <div class="left-panel-header">
            <el-icon :size="15" color="#0047AB"><Trophy /></el-icon>
            <span class="left-panel-title">比赛列表</span>
            <el-tag type="primary" size="small" effect="plain">{{ liveMatches.length }} 场</el-tag>
          </div>

          <el-tabs v-model="activeDateTab" class="date-tabs" @tab-change="onDateTabChange">
            <el-tab-pane
              v-for="date in dateList"
              :key="date"
              :label="formatDateLabel(date)"
              :name="date"
            >
              <div class="match-list-scroll">
                <div
                  v-for="m in matchesByDate[date] || []"
                  :key="m.match_num"
                  class="match-list-item"
                  :class="{ active: selectedMatchNum === m.match_num }"
                  @click="selectMatch(m)"
                >
                  <div class="mli-match-num">{{ m.match_num }}</div>
                  <div class="mli-team-row">
                    <span class="mli-name">{{ m.home_team }}</span>
                  </div>
                  <div class="mli-center">
                    <span class="mli-vs">VS</span>
                    <span class="mli-time">{{ m.match_time }}</span>
                  </div>
                  <div class="mli-team-row">
                    <span class="mli-name">{{ m.away_team }}</span>
                  </div>
                  <div class="mli-footer">
                    <el-tag size="small" type="warning" effect="plain" round>{{ m.league }}</el-tag>
                  </div>
                  <!-- 简要赔率 -->
                  <div class="mli-odds-mini" v-if="m.had">
                    <span class="odds-mini-item">{{ m.had.win }}</span>
                    <span class="odds-mini-item">{{ m.had.draw }}</span>
                    <span class="odds-mini-item">{{ m.had.lose }}</span>
                  </div>
                </div>

                <el-empty
                  v-if="(matchesByDate[date] || []).length === 0 && !loading"
                  description="该日期无比赛"
                  :image-size="60"
                />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-col>

      <!-- 右侧：投注主内容 -->
      <el-col :xs="24" :sm="18" :md="19" :lg="20">
        <div class="right-panel" v-if="selectedMatch">

          <!-- 比赛信息卡 -->
          <el-card class="main-match-card" shadow="hover">
            <div class="match-big-display">
              <div class="team-block left-team">
                <div class="team-name-big">{{ selectedMatch.home_team }}</div>
                <div class="team-abb">{{ selectedMatch.home_team }}</div>
              </div>
              <div class="center-block">
                <div class="vs-badge">VS</div>
                <div class="match-meta">
                  <div class="meta-row">
                    <el-tag size="small" type="warning" round>{{ selectedMatch.league }}</el-tag>
                    <el-tag size="small" round>{{ selectedMatch.match_num }}</el-tag>
                  </div>
                  <div class="meta-time">
                    <el-icon :size="13"><Calendar /></el-icon>
                    {{ selectedMatch.match_date }} {{ selectedMatch.match_time }}
                  </div>
                </div>
              </div>
              <div class="team-block right-team">
                <div class="team-name-big">{{ selectedMatch.away_team }}</div>
                <div class="team-abb">{{ selectedMatch.away_team }}</div>
              </div>
            </div>
          </el-card>

          <!-- 玩法选择 Tab -->
          <el-card class="play-type-card" shadow="hover">
            <template #header>
              <div class="play-type-header">
                <span class="play-type-title">选择投注玩法</span>
                <span class="update-time" v-if="selectedMatch.had">
                  <el-icon :size="11"><Clock /></el-icon>
                  更新: {{ selectedMatch.had.update_time || '--' }}
                </span>
              </div>
            </template>

            <el-tabs v-model="activePlayType" class="play-type-tabs" @tab-change="onPlayTypeChange">
              <!-- 胜平负 -->
              <el-tab-pane name="SPF">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-name">胜平负</span>
                    <span class="tab-en">SPF</span>
                  </div>
                </template>
                <div class="play-section">
                  <div class="play-title-row">
                    <span class="play-label">竞彩足球 胜平负</span>
                    <span class="play-tip">选择一项结果进行投注</span>
                  </div>
                  <div class="odds-btn-grid spf-grid">
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'SPF' && selectedBet.option === 'win' }"
                      @click="pickBet('SPF', 'win', selectedMatch.had?.win, '主胜')"
                    >
                      <div class="odds-btn-label">{{ selectedMatch.home_team }} 胜</div>
                      <div class="odds-btn-value">{{ selectedMatch.had?.win || '--' }}</div>
                    </div>
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'SPF' && selectedBet.option === 'draw' }"
                      @click="pickBet('SPF', 'draw', selectedMatch.had?.draw, '平局')"
                    >
                      <div class="odds-btn-label">平局</div>
                      <div class="odds-btn-value">{{ selectedMatch.had?.draw || '--' }}</div>
                    </div>
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'SPF' && selectedBet.option === 'lose' }"
                      @click="pickBet('SPF', 'lose', selectedMatch.had?.lose, '客胜')"
                    >
                      <div class="odds-btn-label">{{ selectedMatch.away_team }} 胜</div>
                      <div class="odds-btn-value">{{ selectedMatch.had?.lose || '--' }}</div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 让球胜平负 -->
              <el-tab-pane name="HHAD">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-name">让球</span>
                    <span class="tab-en">HHAD</span>
                  </div>
                </template>
                <div class="play-section" v-if="selectedMatch.hhad">
                  <div class="play-title-row">
                    <span class="play-label">竞彩足球 让球胜平负</span>
                    <span class="let-ball-tag">
                      <el-tag type="primary" size="small" effect="dark" round>
                        {{ selectedMatch.hhad.goal_line || 0 }}
                      </el-tag>
                    </span>
                  </div>
                  <div class="let-ball-info">
                    主队 {{ selectedMatch.home_team }} {{ selectedMatch.hhad.goal_line || 0 }}
                  </div>
                  <div class="odds-btn-grid spf-grid">
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'HHAD' && selectedBet.option === 'win' }"
                      @click="pickBet('HHAD', 'win', selectedMatch.hhad?.win, '让球主胜')"
                    >
                      <div class="odds-btn-label">{{ selectedMatch.home_team }} 胜</div>
                      <div class="odds-btn-value">{{ selectedMatch.hhad?.win || '--' }}</div>
                    </div>
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'HHAD' && selectedBet.option === 'draw' }"
                      @click="pickBet('HHAD', 'draw', selectedMatch.hhad?.draw, '让球平局')"
                    >
                      <div class="odds-btn-label">平局</div>
                      <div class="odds-btn-value">{{ selectedMatch.hhad?.draw || '--' }}</div>
                    </div>
                    <div
                      class="odds-btn"
                      :class="{ selected: selectedBet.playType === 'HHAD' && selectedBet.option === 'lose' }"
                      @click="pickBet('HHAD', 'lose', selectedMatch.hhad?.lose, '让球客胜')"
                    >
                      <div class="odds-btn-label">{{ selectedMatch.away_team }} 胜</div>
                      <div class="odds-btn-value">{{ selectedMatch.hhad?.lose || '--' }}</div>
                    </div>
                  </div>
                </div>
                <el-empty v-else description="暂不支持让球玩法" :image-size="60" />
              </el-tab-pane>

              <!-- 比分 -->
              <el-tab-pane name="CRS">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-name">比分</span>
                    <span class="tab-en">CRS</span>
                  </div>
                </template>
                <div class="play-section" v-if="selectedMatch.crs">
                  <div class="play-title-row">
                    <span class="play-label">竞彩足球 比分</span>
                    <span class="play-tip">选择具体比分进行投注</span>
                  </div>
                  <div class="crs-grid">
                    <!-- 主队赢 -->
                    <div class="crs-group">
                      <div class="crs-group-title" :style="{ color: '#409eff' }">{{ selectedMatch.home_team }} 赢</div>
                      <div class="crs-items">
                        <div
                          v-for="score in getCrsByResult('home', selectedMatch.crs)"
                          :key="score.key"
                          class="crs-btn"
                          :class="{ selected: selectedBet.playType === 'CRS' && selectedBet.option === score.key }"
                          @click="pickBet('CRS', score.key, score.odds, score.label)"
                        >
                          <span class="crs-score">{{ score.label }}</span>
                          <span class="crs-odds">{{ score.odds || '--' }}</span>
                        </div>
                      </div>
                    </div>
                    <!-- 平局 -->
                    <div class="crs-group">
                      <div class="crs-group-title" :style="{ color: '#e6a23c' }">平局</div>
                      <div class="crs-items">
                        <div
                          v-for="score in getCrsByResult('draw', selectedMatch.crs)"
                          :key="score.key"
                          class="crs-btn"
                          :class="{ selected: selectedBet.playType === 'CRS' && selectedBet.option === score.key }"
                          @click="pickBet('CRS', score.key, score.odds, score.label)"
                        >
                          <span class="crs-score">{{ score.label }}</span>
                          <span class="crs-odds">{{ score.odds || '--' }}</span>
                        </div>
                      </div>
                    </div>
                    <!-- 客队赢 -->
                    <div class="crs-group">
                      <div class="crs-group-title" :style="{ color: '#67c23a' }">{{ selectedMatch.away_team }} 赢</div>
                      <div class="crs-items">
                        <div
                          v-for="score in getCrsByResult('away', selectedMatch.crs)"
                          :key="score.key"
                          class="crs-btn"
                          :class="{ selected: selectedBet.playType === 'CRS' && selectedBet.option === score.key }"
                          @click="pickBet('CRS', score.key, score.odds, score.label)"
                        >
                          <span class="crs-score">{{ score.label }}</span>
                          <span class="crs-odds">{{ score.odds || '--' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <el-empty v-else description="暂不支持比分玩法" :image-size="60" />
              </el-tab-pane>

              <!-- 总进球 -->
              <el-tab-pane name="TTG">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-name">总进球</span>
                    <span class="tab-en">TTG</span>
                  </div>
                </template>
                <div class="play-section" v-if="selectedMatch.ttg">
                  <div class="play-title-row">
                    <span class="play-label">竞彩足球 总进球数</span>
                    <span class="play-tip">全场总进球数</span>
                  </div>
                  <div class="ttg-grid">
                    <div
                      v-for="item in getTtgOptions(selectedMatch.ttg)"
                      :key="item.key"
                      class="ttg-btn"
                      :class="{ selected: selectedBet.playType === 'TTG' && selectedBet.option === item.key }"
                      @click="pickBet('TTG', item.key, item.odds, item.label)"
                    >
                      <span class="ttg-label">{{ item.label }}</span>
                      <span class="ttg-odds">{{ item.odds || '--' }}</span>
                    </div>
                  </div>
                </div>
                <el-empty v-else description="暂不支持总进球玩法" :image-size="60" />
              </el-tab-pane>

              <!-- 半全场 -->
              <el-tab-pane name="BQC">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-name">半全场</span>
                    <span class="tab-en">BQC</span>
                  </div>
                </template>
                <div class="play-section" v-if="selectedMatch.bqc">
                  <div class="play-title-row">
                    <span class="play-label">竞彩足球 半全场</span>
                    <span class="play-tip">半场结果 × 全场结果</span>
                  </div>
                  <div class="bqc-matrix">
                    <div class="bqc-header">
                      <span></span>
                      <span>{{ selectedMatch.home_team }} 赢</span>
                      <span>平局</span>
                      <span>{{ selectedMatch.away_team }} 赢</span>
                    </div>
                    <div
                      v-for="half in ['win', 'draw', 'lose']"
                      :key="half"
                      class="bqc-row"
                    >
                      <span class="bqc-half-label">{{ getHalfLabel(half) }}</span>
                      <div
                        v-for="full in ['win', 'draw', 'lose']"
                        :key="full"
                        class="bqc-btn"
                        :class="{ selected: selectedBet.playType === 'BQC' && selectedBet.option === `${half}_${full}` }"
                        @click="pickBet('BQC', `${half}_${full}`, getBqcOdds(selectedMatch.bqc, half, full), getBqcLabel(half, full))"
                      >
                        <span class="bqc-odds">{{ getBqcOdds(selectedMatch.bqc, half, full) || '--' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <el-empty v-else description="暂不支持半全场玩法" :image-size="60" />
              </el-tab-pane>
            </el-tabs>
          </el-card>

          <!-- 投注确认区 -->
          <el-card class="bet-confirm-card" shadow="hover" v-if="selectedBet.playType">
            <div class="bet-confirm-inner">
              <div class="bet-match-info">
                <div class="bet-teams">
                  <span>{{ selectedMatch.home_team }}</span>
                  <span class="bet-vs">vs</span>
                  <span>{{ selectedMatch.away_team }}</span>
                </div>
                <div class="bet-meta">
                  <el-tag type="primary" size="small" round>{{ getPlayTypeName(selectedBet.playType) }}</el-tag>
                  <el-tag type="success" size="small" round>{{ selectedBet.optionLabel }}</el-tag>
                </div>
              </div>
              <div class="bet-calc">
                <div class="bet-calc-item">
                  <span class="calc-label">赔率</span>
                  <span class="calc-value odds">{{ selectedBet.odds || '--' }}</span>
                </div>
                <div class="bet-calc-item">
                  <span class="calc-label">概率</span>
                  <span class="calc-value prob">{{ winProb }}%</span>
                </div>
                <div class="bet-calc-item">
                  <span class="calc-label">金额</span>
                  <el-input-number v-model="betAmount" :min="10" :max="100000" :step="10" size="default" controls-position="right" style="width: 130px" />
                </div>
                <div class="bet-calc-item">
                  <span class="calc-label">预计奖金</span>
                  <span class="calc-value prize">¥{{ estimatedPrize }}</span>
                </div>
              </div>
              <div class="bet-actions">
                <el-button type="primary" size="large" @click="placeBet" class="confirm-btn">
                  <el-icon><Trophy /></el-icon>
                  确认投注
                </el-button>
                <el-button size="large" @click="clearBet">清除选择</el-button>
              </div>
            </div>
          </el-card>

          <!-- 赔率参考卡 -->
          <el-row :gutter="12" class="odds-ref-row">
            <el-col :xs="24" :md="12">
              <el-card class="ref-card" shadow="hover">
                <template #header>
                  <div class="ref-header">
                    <span>胜平负 / 让球胜平负</span>
                  </div>
                </template>
                <div class="ref-grid">
                  <div class="ref-row">
                    <span class="ref-label">胜平负</span>
                    <span class="ref-val win">{{ selectedMatch.had?.win || '--' }}</span>
                    <span class="ref-val draw">{{ selectedMatch.had?.draw || '--' }}</span>
                    <span class="ref-val lose">{{ selectedMatch.had?.lose || '--' }}</span>
                  </div>
                  <div class="ref-row" v-if="selectedMatch.hhad">
                    <span class="ref-label">让球 {{ selectedMatch.hhad.goal_line || 0 }}</span>
                    <span class="ref-val win">{{ selectedMatch.hhad?.win || '--' }}</span>
                    <span class="ref-val draw">{{ selectedMatch.hhad?.draw || '--' }}</span>
                    <span class="ref-val lose">{{ selectedMatch.hhad?.lose || '--' }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card class="ref-card" shadow="hover">
                <template #header>
                  <div class="ref-header">
                    <span>投注历史（本地）</span>
                    <el-button v-if="betHistory.length > 0" type="danger" size="small" text @click="clearHistory">清空</el-button>
                  </div>
                </template>
                <el-empty v-if="betHistory.length === 0" description="暂无投注记录" :image-size="60" />
                <div v-else class="history-list">
                  <div v-for="b in betHistory.slice(0, 5)" :key="b.id" class="history-item-row">
                    <span class="hf-match">{{ b.home }} vs {{ b.away }}</span>
                    <el-tag size="small" type="primary" round>{{ b.playTypeName }} {{ b.optionLabel }}</el-tag>
                    <span class="hf-amount">¥{{ b.amount }}</span>
                    <span class="hf-time">{{ b.time }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-empty v-else description="请从左侧选择一场比赛" :image-size="100" />
      </el-col>
    </el-row>

    <!-- 投注确认弹窗 -->
    <el-dialog v-model="showConfirm" width="460px" title="确认投注">
      <div class="confirm-content" v-if="selectedMatch">
        <div class="confirm-match">
          <span>{{ selectedMatch.home_team }}</span>
          <span class="vs-small">vs</span>
          <span>{{ selectedMatch.away_team }}</span>
        </div>
        <el-divider />
        <el-descriptions :column="1" border size="default">
          <el-descriptions-item label="玩法">{{ getPlayTypeName(selectedBet.playType) }}</el-descriptions-item>
          <el-descriptions-item label="投注选项">{{ selectedBet.optionLabel }}</el-descriptions-item>
          <el-descriptions-item label="赔率">{{ selectedBet.odds }}</el-descriptions-item>
          <el-descriptions-item label="投注金额">¥ {{ betAmount }}</el-descriptions-item>
          <el-descriptions-item label="预计奖金">¥ {{ estimatedPrize }}</el-descriptions-item>
          <el-descriptions-item label="比赛时间">{{ selectedMatch.match_date }} {{ selectedMatch.match_time }}</el-descriptions-item>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Trophy, Calendar, Clock, Refresh } from '@element-plus/icons-vue'
import { matchAPI } from '../api'

const STORAGE_KEY = 'worldcup_bet_history_v2'

// 状态
const loading = ref(false)
const liveMatches = ref([])
const matchesByDate = ref({})
const dateList = ref([])
const activeDateTab = ref('')
const selectedMatchNum = ref(null)
const activePlayType = ref('SPF')
const betAmount = ref(100)
const showConfirm = ref(false)
const betHistory = ref([])
const currentTime = ref('')
let timer = null

const selectedMatch = computed(() => {
  return liveMatches.value.find(m => m.match_num === selectedMatchNum.value) || null
})

const selectedBet = ref({ playType: '', option: '', odds: null, optionLabel: '' })

// 胜率推算
const winProb = computed(() => {
  if (!selectedBet.value.odds) return 0
  return ((1 / selectedBet.value.odds) * 100 * 0.85).toFixed(1)
})

const estimatedPrize = computed(() => {
  if (!selectedBet.value.odds) return '0.00'
  return (betAmount.value * selectedBet.value.odds).toFixed(2)
})

// 获取日期列表
const fetchLiveMatches = async () => {
  try {
    loading.value = true
    const data = await matchAPI.getLiveMatches()
    liveMatches.value = data.all_matches || []
    matchesByDate.value = data.matches_by_date || {}
    dateList.value = Object.keys(matchesByDate.value).sort()
    if (dateList.value.length > 0 && !activeDateTab.value) {
      activeDateTab.value = dateList.value[0]
    }
    if (dateList.value.length > 0 && !selectedMatchNum.value) {
      const firstMatch = (matchesByDate.value[dateList.value[0]] || [])[0]
      if (firstMatch) selectMatch(firstMatch)
    }
  } catch (e) {
    console.error('获取体彩数据失败:', e)
    ElMessage.error('获取体彩数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const selectMatch = (m) => {
  selectedMatchNum.value = m.match_num
  selectedBet.value = { playType: '', option: '', odds: null, optionLabel: '' }
}

const onDateTabChange = () => {
  const matches = matchesByDate.value[activeDateTab.value] || []
  if (matches.length > 0) selectMatch(matches[0])
}

const onPlayTypeChange = () => {
  selectedBet.value = { playType: '', option: '', odds: null, optionLabel: '' }
}

const pickBet = (playType, option, odds, label) => {
  selectedBet.value = { playType, option, odds, optionLabel: label }
}

const clearBet = () => {
  selectedBet.value = { playType: '', option: '', odds: null, optionLabel: '' }
}

// 玩法名称
const PLAY_TYPE_NAMES = { SPF: '胜平负', HHAD: '让球胜平负', CRS: '比分', TTG: '总进球', BQC: '半全场' }
const getPlayTypeName = (pt) => PLAY_TYPE_NAMES[pt] || pt

// 比分玩法选项
const getCrsByResult = (result, crsData) => {
  if (!crsData || !crsData.scores) return []
  const scores = crsData.scores
  const map = {
    home: [
      { key: '1:0', label: '1:0', odds: scores['1:0'] },
      { key: '2:0', label: '2:0', odds: scores['2:0'] },
      { key: '2:1', label: '2:1', odds: scores['2:1'] },
      { key: '3:0', label: '3:0', odds: scores['3:0'] },
      { key: '3:1', label: '3:1', odds: scores['3:1'] },
      { key: '3:2', label: '3:2', odds: scores['3:2'] },
      { key: '胜其他', label: '胜其他', odds: scores['胜其他'] },
    ],
    draw: [
      { key: '0:0', label: '0:0', odds: scores['0:0'] },
      { key: '1:1', label: '1:1', odds: scores['1:1'] },
      { key: '2:2', label: '2:2', odds: scores['2:2'] },
      { key: '3:3', label: '3:3', odds: scores['3:3'] },
    ],
    away: [
      { key: '0:1', label: '0:1', odds: scores['0:1'] },
      { key: '0:2', label: '0:2', odds: scores['0:2'] },
      { key: '1:2', label: '1:2', odds: scores['1:2'] },
      { key: '0:3', label: '0:3', odds: scores['0:3'] },
      { key: '1:3', label: '1:3', odds: scores['1:3'] },
      { key: '2:3', label: '2:3', odds: scores['2:3'] },
      { key: '负其他', label: '负其他', odds: scores['负其他'] },
    ],
  }
  return (map[result] || []).filter(s => s.odds != null && s.odds !== 0)
}

// 总进球选项
const getTtgOptions = (ttgData) => {
  if (!ttgData) return []
  const items = [
    { key: 'total_0', label: '0 球', odds: ttgData.total_0 },
    { key: 'total_1', label: '1 球', odds: ttgData.total_1 },
    { key: 'total_2', label: '2 球', odds: ttgData.total_2 },
    { key: 'total_3', label: '3 球', odds: ttgData.total_3 },
    { key: 'total_4', label: '4 球', odds: ttgData.total_4 },
    { key: 'total_5', label: '5 球', odds: ttgData.total_5 },
    { key: 'total_6', label: '6 球', odds: ttgData.total_6 },
    { key: 'total_7', label: '≥7 球', odds: ttgData.total_7 },
  ]
  return items.filter(i => i.odds != null && i.odds !== 0)
}

// 半全场选项
const HALF_LABELS = { win: '胜', draw: '平', lose: '负' }
const getHalfLabel = (h) => HALF_LABELS[h] || h
const getBqcLabel = (half, full) => `${HALF_LABELS[half]} / ${HALF_LABELS[full]}`
const BQC_KEYS = {
  win_win: 'win_win', win_draw: 'win_draw', win_lose: 'win_lose',
  draw_win: 'draw_win', draw_draw: 'draw_draw', draw_lose: 'draw_lose',
  lose_win: 'lose_win', lose_draw: 'lose_draw', lose_lose: 'lose_lose',
}
const getBqcOdds = (bqc, half, full) => {
  if (!bqc) return null
  const key = `${half}_${full}`
  return bqc[BqcKey(key)] || null
}
const BqcKey = (k) => k  // 直接返回 key（已经在 BQC 数据中使用 _ 分隔）

// 日期格式化
const formatDateLabel = (dateStr) => {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    return `${parseInt(parts[1])}/${parseInt(parts[2])}`
  }
  return dateStr
}

// 更新时钟
const updateTime = () => {
  const now = new Date()
  currentTime.value = `${now.getMonth() + 1}/${now.getDate()} ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

// 投注确认
const placeBet = () => {
  if (!selectedBet.value.playType || !selectedBet.value.odds) {
    ElMessage.warning('请先选择投注选项')
    return
  }
  showConfirm.value = true
}

const confirmBet = () => {
  if (!selectedMatch.value) return
  betHistory.value.unshift({
    id: Date.now(),
    home: selectedMatch.value.home_team,
    away: selectedMatch.value.away_team,
    match_num: selectedMatch.value.match_num,
    playType: selectedBet.value.playType,
    playTypeName: getPlayTypeName(selectedBet.value.playType),
    optionLabel: selectedBet.value.optionLabel,
    odds: selectedBet.value.odds,
    amount: betAmount.value,
    prize: parseFloat(estimatedPrize.value),
    time: new Date().toLocaleString('zh-CN'),
  })
  saveHistory()
  showConfirm.value = false
  ElMessage.success('投注已记录！')
}

const saveHistory = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(betHistory.value.slice(0, 30)))
  } catch (_) {}
}

const loadHistory = () => {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v) betHistory.value = JSON.parse(v)
  } catch (_) {}
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有投注历史吗？', '提示', {
      confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning'
    })
    betHistory.value = []
    saveHistory()
    ElMessage.success('已清空')
  } catch (_) {}
}

onMounted(() => {
  loadHistory()
  fetchLiveMatches()
  updateTime()
  timer = setInterval(updateTime, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.betting-page { max-width: 1400px; margin: 0 auto; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 4px 20px 4px;
}
.header-main { display: flex; align-items: center; gap: 14px; }
.title-wrapper h1 { font-size: 26px; font-weight: 700; color: #0047AB; margin: 0; }
.page-subtitle { font-size: 12px; color: #909399; margin: 3px 0 0 0; }
.header-right { display: flex; align-items: center; gap: 10px; }

/* 左侧面板 */
.left-panel {
  background: #fff; border-radius: 12px; border: 1px solid #ebeef5;
  overflow: hidden; margin-bottom: 16px;
}
.left-panel-header {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 14px 8px 14px; border-bottom: 1px solid #f0f0f0;
}
.left-panel-title { font-size: 14px; font-weight: 600; color: #303133; flex: 1; }

.date-tabs :deep(.el-tabs__header) { margin: 0; }
.date-tabs :deep(.el-tabs__nav-wrap) { padding: 0 8px; }
.date-tabs :deep(.el-tabs__item) { font-size: 12px; padding: 0 10px; height: 32px; line-height: 32px; }

.match-list-scroll { max-height: calc(100vh - 280px); overflow-y: auto; padding: 8px; }
.match-list-item {
  border: 2px solid #ebeef5; border-radius: 10px; padding: 9px 10px;
  cursor: pointer; transition: all 0.2s; margin-bottom: 8px;
}
.match-list-item:hover { border-color: #0047AB; transform: translateX(3px); }
.match-list-item.active {
  border-color: #0047AB;
  background: linear-gradient(135deg, rgba(0,71,171,.06), rgba(64,158,255,.06));
  box-shadow: 0 4px 12px rgba(0,71,171,.15);
}
.mli-match-num { font-size: 11px; color: #909399; margin-bottom: 4px; font-weight: 600; }
.mli-team-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #303133; }
.mli-center { display: flex; align-items: center; justify-content: center; gap: 6px; margin: 4px 0; }
.mli-vs { font-size: 10px; font-weight: 800; color: #909399; letter-spacing: 1px; }
.mli-time { font-size: 11px; color: #909399; }
.mli-footer { display: flex; justify-content: center; margin-top: 4px; }
.mli-odds-mini {
  display: flex; justify-content: center; gap: 6px; margin-top: 6px;
  padding-top: 5px; border-top: 1px dashed #f0f0f0;
}
.odds-mini-item { font-size: 12px; font-weight: 700; color: #0047AB; min-width: 28px; text-align: center; }

/* 右侧主面板 */
.right-panel { }
.main-match-card { margin-bottom: 12px; border-radius: 12px; }
.match-big-display { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 6px 0 10px 0; }
.team-block { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.team-name-big { font-size: 20px; font-weight: 700; color: #0047AB; }
.right-team .team-name-big { color: #67c23a; }
.team-abb { font-size: 11px; color: #909399; }
.center-block { text-align: center; padding: 0 10px; }
.vs-badge { display: inline-block; font-size: 14px; font-weight: 800; letter-spacing: 2px; color: #ffc107; background: #002244; padding: 5px 12px; border-radius: 18px; margin-bottom: 8px; }
.match-meta { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.meta-row { display: flex; gap: 5px; }
.meta-time { font-size: 12px; color: #606266; display: flex; align-items: center; gap: 4px; }

/* 玩法选择卡 */
.play-type-card { margin-bottom: 12px; border-radius: 12px; }
.play-type-header { display: flex; justify-content: space-between; align-items: center; }
.play-type-title { font-size: 15px; font-weight: 600; color: #303133; }
.update-time { font-size: 11px; color: #909399; display: flex; align-items: center; gap: 3px; }

.play-type-tabs :deep(.el-tabs__header) { margin: 0; }
.play-type-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.play-type-tabs :deep(.el-tabs__item) { height: 36px; line-height: 36px; font-size: 13px; }

.tab-label { display: flex; flex-direction: column; align-items: center; line-height: 1.3; }
.tab-name { font-size: 13px; }
.tab-en { font-size: 10px; color: #909399; font-weight: 400; }

.play-section { padding: 12px 4px 4px 4px; }
.play-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.play-label { font-size: 13px; font-weight: 600; color: #303133; }
.play-tip { font-size: 12px; color: #909399; }

/* 胜平负/让球按钮 */
.odds-btn-grid { display: grid; gap: 10px; }
.spf-grid { grid-template-columns: repeat(3, 1fr); }
.odds-btn {
  border: 2px solid #ebeef5; border-radius: 10px; padding: 14px 8px;
  text-align: center; cursor: pointer; transition: all 0.2s;
  background: #fff;
}
.odds-btn:hover { border-color: #0047AB; }
.odds-btn.selected { border-color: #0047AB; background: linear-gradient(135deg, #ecf5ff, #d0e8ff); }
.odds-btn-label { font-size: 12px; color: #606266; margin-bottom: 6px; }
.odds-btn-value { font-size: 20px; font-weight: 700; color: #0047AB; }
.odds-btn.selected .odds-btn-value { color: #0047AB; }

.let-ball-info { font-size: 12px; color: #909399; margin-bottom: 10px; text-align: center; }
.let-ball-tag { }

/* 比分玩法 */
.crs-grid { display: flex; flex-direction: column; gap: 12px; }
.crs-group { }
.crs-group-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px solid #f0f0f0; }
.crs-items { display: flex; flex-wrap: wrap; gap: 8px; }
.crs-btn {
  border: 1px solid #e4e7ed; border-radius: 8px; padding: 7px 12px;
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  cursor: pointer; min-width: 68px; transition: all 0.15s; background: #fff;
}
.crs-btn:hover { border-color: #0047AB; }
.crs-btn.selected { border-color: #0047AB; background: #ecf5ff; }
.crs-score { font-size: 14px; font-weight: 700; color: #303133; }
.crs-odds { font-size: 12px; font-weight: 700; color: #0047AB; }

/* 总进球 */
.ttg-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.ttg-btn {
  border: 1px solid #e4e7ed; border-radius: 8px; padding: 12px 8px;
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  cursor: pointer; transition: all 0.15s; background: #fff;
}
.ttg-btn:hover { border-color: #0047AB; }
.ttg-btn.selected { border-color: #0047AB; background: #ecf5ff; }
.ttg-label { font-size: 13px; font-weight: 600; color: #303133; }
.ttg-odds { font-size: 14px; font-weight: 700; color: #0047AB; }

/* 半全场 */
.bqc-matrix { display: flex; flex-direction: column; gap: 6px; }
.bqc-header { display: grid; grid-template-columns: 60px repeat(3, 1fr); gap: 6px; margin-bottom: 4px; }
.bqc-header span { font-size: 12px; font-weight: 600; color: #606266; text-align: center; }
.bqc-row { display: grid; grid-template-columns: 60px repeat(3, 1fr); gap: 6px; align-items: center; }
.bqc-half-label { font-size: 12px; color: #606266; font-weight: 600; text-align: center; }
.bqc-btn {
  border: 1px solid #e4e7ed; border-radius: 6px; padding: 8px 4px;
  text-align: center; cursor: pointer; transition: all 0.15s; background: #fff;
}
.bqc-btn:hover { border-color: #0047AB; }
.bqc-btn.selected { border-color: #0047AB; background: #ecf5ff; }
.bqc-odds { font-size: 13px; font-weight: 700; color: #0047AB; }

/* 投注确认卡 */
.bet-confirm-card { margin-bottom: 12px; border-radius: 12px; background: linear-gradient(135deg, #f0f9ff, #e8f4fd); border: 1px solid #cce4f7; }
.bet-confirm-inner { display: flex; flex-direction: column; gap: 14px; padding: 4px 0; }
.bet-match-info { display: flex; justify-content: space-between; align-items: center; }
.bet-teams { font-size: 15px; font-weight: 700; color: #303133; }
.bet-vs { color: #909399; font-weight: 400; margin: 0 6px; }
.bet-meta { display: flex; gap: 6px; }
.bet-calc { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.bet-calc-item { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.calc-label { font-size: 11px; color: #909399; }
.calc-value { font-size: 16px; font-weight: 700; }
.calc-value.odds { color: #0047AB; }
.calc-value.prob { color: #e6a23c; }
.calc-value.prize { color: #67c23a; }
.bet-actions { display: flex; gap: 10px; }
.confirm-btn { min-width: 140px; }

/* 参考卡 */
.odds-ref-row { margin-top: 4px; }
.ref-card { border-radius: 12px; }
.ref-header { font-size: 13px; font-weight: 600; color: #303133; display: flex; justify-content: space-between; align-items: center; }
.ref-grid { }
.ref-row {
  display: grid; grid-template-columns: 80px repeat(3, 1fr); gap: 6px;
  align-items: center; padding: 8px 0; border-bottom: 1px dashed #f0f0f0;
}
.ref-row:last-child { border-bottom: none; }
.ref-label { font-size: 12px; color: #606266; font-weight: 600; text-align: center; }
.ref-val { font-size: 14px; font-weight: 700; text-align: center; }
.ref-val.win { color: #409eff }
.ref-val.draw { color: #e6a23c }
.ref-val.lose { color: #67c23a }

.history-list { display: flex; flex-direction: column; gap: 6px; }
.history-item-row {
  display: flex; align-items: center; gap: 8px; padding: 5px 0;
  border-bottom: 1px dashed #f0f0f0; font-size: 12px;
}
.history-item-row:last-child { border-bottom: none; }
.hf-match { flex: 1; color: #303133; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hf-amount { font-weight: 700; color: #0047AB; white-space: nowrap; }
.hf-time { font-size: 11px; color: #909399; white-space: nowrap; }

/* 确认弹窗 */
.confirm-content { padding: 4px 0; }
.confirm-match { text-align: center; font-size: 16px; font-weight: 700; color: #303133; }
.vs-small { color: #909399; font-weight: 400; margin: 0 6px; }

/* 响应式 */
@media (max-width: 992px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .title-wrapper h1 { font-size: 22px }
  .match-big-display { flex-direction: column; gap: 12px; }
  .team-block { flex-direction: row; }
  .spf-grid { grid-template-columns: repeat(3, 1fr); }
  .ttg-grid { grid-template-columns: repeat(4, 1fr); }
  .bet-calc { gap: 8px; }
}
@media (max-width: 768px) {
  .ttg-grid { grid-template-columns: repeat(4, 1fr); }
  .bqc-header, .bqc-row { grid-template-columns: 50px repeat(3, 1fr); }
  .bet-calc { flex-direction: column; align-items: stretch; }
  .bet-actions { flex-direction: column; }
  .confirm-btn { width: 100%; }
}
</style>

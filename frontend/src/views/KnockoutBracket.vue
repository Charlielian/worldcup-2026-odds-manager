<template>
  <div class="bracket-page" v-loading="loading">
    <div v-if="!loading && bracketData.length === 0" class="empty-state">
      <el-empty description="小组赛尚未结束，淘汰赛对阵待定" />
    </div>

    <div v-else-if="!loading" class="bracket-outer">
      <!-- 上半区 -->
      <div class="bracket-half top-half">
        <div class="half-header">
          <span class="half-icon">🔵</span>
          <span class="half-title">上半区</span>
        </div>
        <div class="half-body">
          <BracketHalf
            :rounds="topRounds"
            :connectors="topConnectors"
            :final-match="finalMatch"
            :third-place-match="thirdPlaceMatch"
            :champion="champion"
            :fourth-place="fourthPlace"
            :format-time="formatTime"
            :is-placeholder="isPlaceholder"
            :is-winner="isWinner"
            :show-center="false"
          />
        </div>
      </div>

      <!-- 下半区 -->
      <div class="bracket-half bottom-half">
        <div class="half-header">
          <span class="half-icon">🟢</span>
          <span class="half-title">下半区</span>
        </div>
        <div class="half-body">
          <BracketHalf
            :rounds="bottomRounds"
            :connectors="bottomConnectors"
            :final-match="finalMatch"
            :third-place-match="thirdPlaceMatch"
            :champion="champion"
            :fourth-place="fourthPlace"
            :format-time="formatTime"
            :is-placeholder="isPlaceholder"
            :is-winner="isWinner"
            :show-center="false"
          />
        </div>
      </div>

      <!-- 中间决赛区域（绝对定位） -->
      <div class="bracket-center">
        <div class="center-slot champion-area">
          <div class="center-label">🏆</div>
          <div class="center-value">{{ champion }}</div>
        </div>
        <div class="center-box final-area" v-if="finalMatch">
          <div class="center-box-header">🏆 决赛</div>
          <BracketMatchCard :match="finalMatch" :format-time="formatTime" :is-placeholder="isPlaceholder" :is-winner="isWinner" :compact="false" />
        </div>
        <div class="semi-bridge">
          <span class="bridge-text">半决赛负者</span>
        </div>
        <div class="center-box third-area" v-if="thirdPlaceMatch">
          <div class="center-box-header">🥉 三四名决赛</div>
          <BracketMatchCard :match="thirdPlaceMatch" :format-time="formatTime" :is-placeholder="isPlaceholder" :is-winner="isWinner" :compact="false" />
        </div>
        <div class="center-slot fourth-area">
          <div class="center-label">4th</div>
          <div class="center-value fourth-name">{{ fourthPlace }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { matchAPI } from '../api'
import BracketHalf from './bracket/BracketHalf.vue'
import BracketMatchCard from './bracket/BracketMatchCard.vue'

const loading = ref(true)
const bracketData = ref([])

// ── 布局常量 ──────────────────────────────
const CARD_H = 72        // 每张 match-card 高度 (px)
const GAP    = 14        // 卡片之间间距 (px)
const COL_H  = 780       // 每列总高度 (px)
const CONN_W = 64        // 连接线区域宽度 (px)

// ── 按 position 分类 ──────────────────────
const byPosition = computed(() => {
  const map = {}
  bracketData.value.forEach(m => { map[m.position] = m })
  return map
})

// 上半区轮次
const topRounds = computed(() => [
  {
    label: '1/16决赛',
    matches: [1,2,3,4,5,6,7,8].map(i => byPosition.value['r16_' + i]).filter(Boolean),
    padTop: 0,
  },
  {
    label: '1/8决赛',
    matches: [1,2,3,4].map(i => byPosition.value['r8_' + i]).filter(Boolean),
    padTop: 165,
  },
  {
    label: '1/4决赛',
    matches: [1,2].map(i => byPosition.value['qf_' + i]).filter(Boolean),
    padTop: 345,
  },
  {
    label: '半决赛',
    matches: [byPosition.value['sf_1']].filter(Boolean),
    padTop: 505,
  },
])

// 下半区轮次
const bottomRounds = computed(() => [
  {
    label: '半决赛',
    matches: [byPosition.value['sf_2']].filter(Boolean),
    padTop: 505,
  },
  {
    label: '1/4决赛',
    matches: [3,4].map(i => byPosition.value['qf_' + i]).filter(Boolean),
    padTop: 345,
  },
  {
    label: '1/8决赛',
    matches: [5,6,7,8].map(i => byPosition.value['r8_' + i]).filter(Boolean),
    padTop: 165,
  },
  {
    label: '1/16决赛',
    matches: [9,10,11,12,13,14,15,16].map(i => byPosition.value['r16_' + i]).filter(Boolean),
    padTop: 0,
  },
])

// 连接线计算
function yCenter(n) {
  // 第 n 个 match (0-based) 在列中的中心 Y
  return n * (CARD_H + GAP) + CARD_H / 2
}

const topConnectors = computed(() => {
  const lines = []
  const roundH = COL_H

  // R16 → R8 (8→4)
  for (let i = 0; i < 4; i++) {
    const r8y = yCenter(i) + 165
    lines.push({
      x1: 0, y1: yCenter(i * 2) + 0,
      x2: CONN_W, y2: r8y,
    })
    lines.push({
      x1: 0, y1: yCenter(i * 2 + 1) + 0,
      x2: CONN_W, y2: r8y,
    })
  }
  // R8 → QF (4→2)
  for (let i = 0; i < 2; i++) {
    const qfy = yCenter(i) + 345
    lines.push({
      x1: 0, y1: yCenter(i * 2) + 165,
      x2: CONN_W, y2: qfy,
    })
    lines.push({
      x1: 0, y1: yCenter(i * 2 + 1) + 165,
      x2: CONN_W, y2: qfy,
    })
  }
  // QF → SF (2→1)
  const sfy = yCenter(0) + 505
  for (let i = 0; i < 2; i++) {
    lines.push({
      x1: 0, y1: yCenter(i) + 345,
      x2: CONN_W, y2: sfy,
    })
  }
  return lines
})

const bottomConnectors = computed(() => {
  const lines = []
  // SF → QF (1→2)
  const sfy = yCenter(0) + 505
  for (let i = 0; i < 2; i++) {
    lines.push({
      x1: CONN_W, y1: sfy,
      x2: 0, y2: yCenter(i) + 345,
    })
  }
  // QF → R8 (2→4)
  for (let i = 0; i < 2; i++) {
    const qfy = yCenter(i) + 345
    for (let j = 0; j < 2; j++) {
      lines.push({
        x1: CONN_W, y1: qfy,
        x2: 0, y2: yCenter(i * 2 + j) + 165,
      })
    }
  }
  // R8 → R16 (4→8)
  for (let i = 0; i < 4; i++) {
    const r8y = yCenter(i) + 165
    for (let j = 0; j < 2; j++) {
      lines.push({
        x1: CONN_W, y1: r8y,
        x2: 0, y2: yCenter(i * 2 + j) + 0,
      })
    }
  }
  return lines
})

// 决赛
const finalMatch = computed(() => byPosition.value['final'])
const thirdPlaceMatch = computed(() => byPosition.value['third_place'])

const champion = computed(() => {
  if (finalMatch.value?.status === 'finished') {
    return finalMatch.value.score1 > finalMatch.value.score2
      ? finalMatch.value.team1 : finalMatch.value.team2
  }
  return '?'
})

const fourthPlace = computed(() => {
  if (thirdPlaceMatch.value?.status === 'finished') {
    return thirdPlaceMatch.value.score1 < thirdPlaceMatch.value.score2
      ? thirdPlaceMatch.value.team1 : thirdPlaceMatch.value.team2
  }
  return '?'
})

// 辅助函数
const isPlaceholder = (m) => {
  if (!m) return true
  const n = (name) => !name || /胜者|负者|待定|组第三名/.test(name)
  return n(m.team1) || n(m.team2)
}
const isWinner = (m, n) => {
  if (m?.status !== 'finished') return false
  return n === 1 ? m.score1 > m.score2 : m.score2 > m.score1
}
const formatTime = (t) => {
  if (!t) return ''
  const p = t.split(' ')
  if (p.length >= 2) {
    const d = p[0].split('-')
    if (d.length >= 3) return `${d[1]}-${d[2]} ${p[1].slice(0,5)}`
  }
  return t
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await matchAPI.getKnockoutBracket()
    bracketData.value = res.bracket_data || []
  } catch (e) {
    console.error('获取淘汰赛数据失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.bracket-page {
  padding: 16px;
  min-height: 100%;
  background: #f0f2f5;
  overflow-x: auto;
}

.empty-state {
  padding: 80px 0;
  text-align: center;
}

/* ── 主容器 ── */
.bracket-outer {
  display: flex;
  align-items: flex-start;
  gap: 0;
  min-width: max-content;
  position: relative;
}

/* ── 半区 ── */
.bracket-half {
  flex-shrink: 0;
  width: 600px;
}

.half-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 8px 8px 0 0;
}

.top-half .half-header {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-bottom: 2px solid #2563eb;
}
.bottom-half .half-header {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border-bottom: 2px solid #22c55e;
}

.half-icon { font-size: 16px; }
.half-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
}
.top-half .half-title { color: #1e40af; }
.bottom-half .half-title { color: #15803d; }

.half-body {
  background: #fff;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* ── 中间决赛区域 ── */
.bracket-center {
  flex-shrink: 0;
  width: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 80px 14px 0;
}

.center-slot {
  width: 100%;
  text-align: center;
  padding: 8px;
  border-radius: 8px;
}
.champion-area {
  background: linear-gradient(135deg, #fef9c3, #fde047);
  border: 2px solid #eab308;
}
.fourth-area {
  background: linear-gradient(135deg, #f3f4f6, #d1d5db);
  border: 2px solid #9ca3af;
}
.center-label {
  font-size: 20px;
  margin-bottom: 2px;
}
.center-value {
  font-size: 12px;
  font-weight: 700;
  color: #854d0e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fourth-name {
  color: #4b5563;
}

.center-box {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  overflow: hidden;
}
.final-area {
  border: 2px solid #f59e0b;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
}
.third-area {
  border: 1.5px solid #d97706;
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
}
.center-box-header {
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  padding: 7px 0 5px;
}
.final-area .center-box-header { color: #b45309; }
.third-area .center-box-header { color: #92400e; }

.semi-bridge {
  text-align: center;
  font-size: 10px;
  color: #9ca3af;
  padding: 2px 0;
}

/* ── 响应式 ── */
@media (max-width: 1100px) {
  .bracket-outer {
    flex-direction: column;
    align-items: center;
  }
  .bracket-half {
    width: 100%;
    max-width: 640px;
  }
  .bracket-center {
    width: 100%;
    max-width: 320px;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    padding-top: 0;
  }
}
</style>

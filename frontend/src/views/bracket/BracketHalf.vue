<template>
  <!-- 固定高度列，外层控制 padTop -->
  <div class="half-column">
    <!-- 连接线 SVG（absolute 覆盖全列） -->
    <div class="lines-overlay" v-if="connectors.length">
      <svg :width="connW" :height="totalH" class="lines-svg">
        <g v-for="(c, i) in connectors" :key="i">
          <path
            :d="connectorPath(c)"
            class="conn-path"
          />
        </g>
      </svg>
    </div>

    <!-- 轮次列 -->
    <div class="rounds-row">
      <div
        v-for="round in rounds"
        :key="round.label"
        class="round-col"
      >
        <div class="round-label">{{ round.label }}</div>
        <div class="round-matches" :style="{ paddingTop: round.padTop + 'px' }">
          <BracketMatchCard
            v-for="match in round.matches"
            :key="match.id"
            :match="match"
            :format-time="formatTime"
            :is-placeholder="isPlaceholder"
            :is-winner="isWinner"
            :compact="true"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const CARD_H = 72
const GAP    = 14
const COL_H  = 780
const CONN_W = 64
const connW  = CONN_W
const totalH = COL_H

const props = defineProps({
  rounds:       { type: Array,  default: () => [] },
  connectors:   { type: Array,  default: () => [] },
  formatTime:   { type: Function, required: true },
  isPlaceholder:{ type: Function, required: true },
  isWinner:     { type: Function, required: true },
})

function connectorPath(c) {
  const { x1, y1, x2, y2 } = c
  // 水平线 + 斜线：先水平到中点，再斜线，最后水平到目标
  const mx = (x1 + x2) / 2
  return `M ${x1} ${y1} L ${mx} ${y1} L ${mx} ${y2} L ${x2} ${y2}`
}
</script>

<style scoped>
.half-column {
  position: relative;
  height: 780px;
  display: flex;
  flex-direction: row;
  padding: 12px 10px 12px 12px;
  overflow: hidden;
}

.lines-overlay {
  position: absolute;
  left: 12px;
  top: 0;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.lines-svg {
  height: 100%;
  overflow: visible;
}

.conn-path {
  fill: none;
  stroke: #94a3b8;
  stroke-width: 1.5;
  stroke-linejoin: round;
}

.rounds-row {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 0;
}

.round-col {
  flex-shrink: 0;
  width: 110px;
  position: relative;
}

.round-label {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  padding: 4px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.round-matches {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>

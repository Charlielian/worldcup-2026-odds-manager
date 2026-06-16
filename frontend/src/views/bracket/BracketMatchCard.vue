<template>
  <div
    class="match-card"
    :class="{
      'is-finished': match.status === 'finished',
      'is-placeholder': placeholder,
      'is-compact': compact,
    }"
  >
    <!-- 上方队伍 -->
    <div class="match-team top-team" :class="{ 'is-winner': isW(1) }">
      <span class="team-flag">{{ match.flag1 || '' }}</span>
      <span class="team-name">{{ match.team1 }}</span>
      <span v-if="match.status === 'finished'" class="team-score">{{ match.score1 }}</span>
    </div>

    <!-- VS -->
    <div class="match-vs">VS</div>

    <!-- 下方队伍 -->
    <div class="match-team bot-team" :class="{ 'is-winner': isW(2) }">
      <span class="team-flag">{{ match.flag2 || '' }}</span>
      <span class="team-name">{{ match.team2 }}</span>
      <span v-if="match.status === 'finished'" class="team-score">{{ match.score2 }}</span>
    </div>

    <!-- 时间 -->
    <div class="match-time">{{ formatTime(match.match_time) }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  match:         { type: Object,  required: true },
  formatTime:    { type: Function, required: true },
  isPlaceholder: { type: Function, required: true },
  isWinner:      { type: Function, required: true },
  compact:       { type: Boolean, default: true },
})

const placeholder = computed(() => props.isPlaceholder(props.match))

function isW(n) {
  return props.isWinner(props.match, n)
}
</script>

<style scoped>
.match-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 5px 8px;
  width: 96px;
  transition: box-shadow 0.2s, transform 0.2s;
  flex-shrink: 0;
}

.match-card:hover {
  box-shadow: 0 3px 10px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.match-card.is-finished {
  border-color: #86efac;
  background: #f0fdf4;
}

.match-card.is-placeholder {
  opacity: 0.55;
  border-style: dashed;
}

.match-team {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 4px;
  border-radius: 4px;
}

.match-team.is-winner {
  background: #dcfce7;
}

.team-flag {
  font-size: 15px;
  flex-shrink: 0;
}

.team-name {
  flex: 1;
  font-size: 11px;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-score {
  font-size: 13px;
  font-weight: 800;
  color: #1e40af;
  min-width: 14px;
  text-align: right;
}

.match-vs {
  text-align: center;
  font-size: 9px;
  color: #94a3b8;
  padding: 1px 0;
  letter-spacing: 0.5px;
}

.match-time {
  text-align: center;
  font-size: 9px;
  color: #94a3b8;
  padding-top: 3px;
  margin-top: 2px;
  border-top: 1px dashed #e2e8f0;
}
</style>

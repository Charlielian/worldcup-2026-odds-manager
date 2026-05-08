<template>
  <div class="group-stage-container">
    <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane
        v-for="group in groupLabels"
        :key="group.value"
        :label="group.label"
        :name="group.value"
      />
    </el-tabs>

    <div v-loading="loading" class="match-content">
      <template v-if="!loading && filteredMatches.length > 0">
        <el-table
          :data="filteredMatches"
          stripe
          style="width: 100%"
          row-key="id"
          :default-sort="{ prop: 'match_time', order: 'ascending' }"
        >
          <el-table-column label="比赛时间" prop="match_time" width="180" sortable>
            <template #default="{ row }">
              <span class="match-time-text">{{ formatTime(row.match_time) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="队伍1" min-width="160">
            <template #default="{ row }">
              <span class="team-cell">
                <span class="flag-emoji">{{ row.flag1 || '' }}</span>
                <span class="team-name-text">{{ row.team1 }}</span>
              </span>
            </template>
          </el-table-column>

          <el-table-column label="比分" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.status === 'finished'" class="score-text">
                {{ row.score1 }} - {{ row.score2 }}
              </span>
              <el-tag v-else type="info" size="small">VS</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="队伍2" min-width="160">
            <template #default="{ row }">
              <span class="team-cell">
                <span class="flag-emoji">{{ row.flag2 || '' }}</span>
                <span class="team-name-text">{{ row.team2 }}</span>
              </span>
            </template>
          </el-table-column>

          <el-table-column label="阶段" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="primary">{{ row.stage }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'finished' ? 'success' : 'info'"
                size="small"
              >
                {{ row.status === 'finished' ? '已结束' : '未开始' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="赔率" width="200" align="center">
            <template #default="{ row }">
              <span v-if="row.odds" class="odds-cell">
                <span class="odds-item">
                  <span class="odds-label">胜</span>
                  <span class="odds-value">{{ row.odds.win_odds }}</span>
                </span>
                <span class="odds-divider">/</span>
                <span class="odds-item">
                  <span class="odds-label">平</span>
                  <span class="odds-value">{{ row.odds.draw_odds }}</span>
                </span>
                <span class="odds-divider">/</span>
                <span class="odds-item">
                  <span class="odds-label">负</span>
                  <span class="odds-value">{{ row.odds.lose_odds }}</span>
                </span>
              </span>
              <span v-else class="no-odds">--</span>
            </template>
          </el-table-column>

          <!-- 可展开行：赔率详细信息 -->
          <el-table-column type="expand" width="50">
            <template #default="{ row }">
              <div v-if="row.odds" class="expand-odds-detail">
                <el-descriptions :column="3" border size="small">
                  <el-descriptions-item label="主胜赔率">
                    <span class="odds-detail-value win">{{ row.odds.win_odds }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="平局赔率">
                    <span class="odds-detail-value draw">{{ row.odds.draw_odds }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="客胜赔率">
                    <span class="odds-detail-value lose">{{ row.odds.lose_odds }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="赔率更新时间" :span="3">
                    {{ row.odds.update_time || '--' }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
              <div v-else class="expand-no-odds">
                <el-empty description="暂无赔率数据" :image-size="60" />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <el-empty
        v-else-if="!loading"
        description="暂无比赛数据"
        :image-size="120"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { matchAPI } from '../api'

const route = useRoute()
const router = useRouter()

// 小组标签列表 A-L
const groupLabels = Array.from({ length: 12 }, (_, i) => ({
  label: `${String.fromCharCode(65 + i)} 组`,
  value: String.fromCharCode(65 + i)
}))

const loading = ref(false)
const matches = ref([])
const activeTab = ref('all')

// 根据当前选中的 tab 过滤比赛
const filteredMatches = computed(() => {
  if (activeTab.value === 'all') {
    return matches.value
  }
  return matches.value.filter(m => m.group_name === activeTab.value)
})

// 格式化时间显示
const formatTime = (timeStr) => {
  if (!timeStr) return '--'
  return timeStr
}

// 获取小组赛比赛数据
const fetchMatches = async (group) => {
  try {
    loading.value = true
    const data = await matchAPI.getGroupMatches(group)
    matches.value = data.matches || []
  } catch (error) {
    console.error('获取小组赛数据失败:', error)
    matches.value = []
  } finally {
    loading.value = false
  }
}

// Tab 切换处理
const handleTabChange = (tabName) => {
  if (tabName === 'all') {
    router.push('/group_stage')
  } else {
    router.push(`/group_stage/${tabName}`)
  }
}

// 监听路由参数变化，重新获取数据
watch(
  () => route.params.group,
  (newGroup) => {
    const group = newGroup || undefined
    activeTab.value = group || 'all'
    fetchMatches(group)
  },
  { immediate: true }
)

onMounted(() => {
  const group = route.params.group || undefined
  activeTab.value = group || 'all'
  fetchMatches(group)
})
</script>

<style scoped>
.group-stage-container {
  padding: 20px;
}

.match-content {
  min-height: 200px;
  margin-top: 16px;
}

.match-time-text {
  font-size: 14px;
  color: #606266;
}

.team-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.flag-emoji {
  font-size: 20px;
  line-height: 1;
}

.team-name-text {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.score-text {
  font-size: 18px;
  font-weight: 700;
  color: #e63946;
}

.odds-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.odds-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.odds-label {
  font-size: 11px;
  color: #909399;
}

.odds-value {
  font-weight: 600;
  color: #303133;
}

.odds-divider {
  color: #dcdfe6;
  margin: 0 2px;
}

.no-odds {
  color: #c0c4cc;
  font-size: 13px;
}

.expand-odds-detail {
  padding: 12px 24px;
}

.odds-detail-value {
  font-weight: 700;
  font-size: 15px;
}

.odds-detail-value.win {
  color: #67c23a;
}

.odds-detail-value.draw {
  color: #e6a23c;
}

.odds-detail-value.lose {
  color: #f56c6c;
}

.expand-no-odds {
  padding: 8px 24px;
}

/* 深度选择器：调整 el-table 斑马纹颜色 */
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: #fafbfc;
}

:deep(.el-tabs--border-card) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

:deep(.el-tabs__item.is-active) {
  font-weight: 600;
}
</style>

<template>
  <div class="rankings-container">
    <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane
        v-for="group in groupLabels"
        :key="group.value"
        :label="group.label"
        :name="group.value"
      />
    </el-tabs>

    <div v-loading="loading" class="rankings-content">
      <template v-if="!loading && displayGroups.length > 0">
        <div
          v-for="groupData in displayGroups"
          :key="groupData.group_id"
          class="group-section"
        >
          <div class="group-title">
            <el-tag type="primary" size="large" effect="dark">
              {{ groupData.group_name }}
            </el-tag>
          </div>

          <el-table
            :data="groupData.teams"
            stripe
            style="width: 100%"
            :row-class-name="getRowClassName"
            row-key="team_id"
            :default-sort="{ prop: 'points', order: 'descending' }"
          >
            <el-table-column label="排名" width="80" align="center">
              <template #default="{ row, $index }">
                <span class="rank-cell">
                  <span
                    v-if="$index === 0"
                    class="rank-badge rank-gold"
                  >1</span>
                  <span
                    v-else-if="$index === 1"
                    class="rank-badge rank-silver"
                  >2</span>
                  <span
                    v-else-if="$index === 2"
                    class="rank-badge rank-bronze"
                  >3</span>
                  <span v-else class="rank-number">{{ $index + 1 }}</span>
                </span>
              </template>
            </el-table-column>

            <el-table-column label="队伍" min-width="160">
              <template #default="{ row }">
                <span class="team-cell">
                  <span class="flag-emoji">{{ row.flag || getTeamFlag(row.team_name) }}</span>
                  <span class="team-name-text">{{ row.team_name }}</span>
                </span>
              </template>
            </el-table-column>

            <el-table-column label="场次" prop="played" width="80" align="center" />
            <el-table-column label="胜" prop="won" width="70" align="center" />
            <el-table-column label="平" prop="drawn" width="70" align="center" />
            <el-table-column label="负" prop="lost" width="70" align="center" />
            <el-table-column label="进球" prop="goals_for" width="80" align="center" />
            <el-table-column label="失球" prop="goals_against" width="80" align="center" />

            <el-table-column label="净胜球" width="90" align="center">
              <template #default="{ row }">
                <span
                  :class="{
                    'gd-positive': row.goal_difference > 0,
                    'gd-negative': row.goal_difference < 0,
                    'gd-zero': row.goal_difference === 0
                  }"
                >
                  {{ row.goal_difference > 0 ? '+' : '' }}{{ row.goal_difference }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="积分" width="90" align="center">
              <template #default="{ row }">
                <span class="points-cell">{{ row.points }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>

      <el-empty
        v-else-if="!loading"
        description="暂无排名数据"
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
const rankings = ref([])
const activeTab = ref('all')

// 国旗映射（从API动态获取）
const flagMap = ref({})

// 获取队伍国旗
const getTeamFlag = (teamName) => {
  return flagMap.value[teamName] || ''
}

// 根据当前选中的 tab 过滤小组
const displayGroups = computed(() => {
  if (activeTab.value === 'all') {
    return rankings.value
  }
  // 兼容 "A" 和 "A组" 两种格式
  return rankings.value.filter(g => 
    g.group_name === activeTab.value || 
    g.group_name === `${activeTab.value}组`
  )
})

// 行样式：前2名绿色背景（出线），第3名黄橙色背景（最佳第三）
const getRowClassName = ({ row, rowIndex }) => {
  if (rowIndex === 0 || rowIndex === 1) {
    return 'qualify-row'
  }
  if (rowIndex === 2) {
    return 'best-third-row'
  }
  return ''
}

// 获取排名数据
const fetchRankings = async (group) => {
  try {
    loading.value = true
    const data = await matchAPI.getRankings(group)
    rankings.value = data.rankings || []
  } catch (error) {
    console.error('获取排名数据失败:', error)
    rankings.value = []
  } finally {
    loading.value = false
  }
}

// Tab 切换处理
const handleTabChange = (tabName) => {
  if (tabName === 'all') {
    router.push('/rankings')
  } else {
    router.push(`/rankings/${tabName}`)
  }
}

// 监听路由参数变化，重新获取数据
watch(
  () => route.params.group,
  (newGroup) => {
    const group = newGroup || undefined
    activeTab.value = group || 'all'
    fetchRankings(group)
  },
  { immediate: true }
)

onMounted(async () => {
  // 从API获取国旗数据
  try {
    const data = await matchAPI.getFlags()
    flagMap.value = data
  } catch (e) {
    console.error('获取国旗数据失败:', e)
  }

  // 获取排名数据
  const group = route.params.group || undefined
  activeTab.value = group || 'all'
  fetchRankings(group)
})
</script>

<style scoped>
.rankings-container {
  padding: 20px;
}

.rankings-content {
  min-height: 200px;
  margin-top: 16px;
}

.group-section {
  margin-bottom: 32px;
}

.group-title {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.team-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.flag-emoji {
  font-size: 22px;
  line-height: 1;
}

.team-name-text {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

/* 排名徽章 */
.rank-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.rank-gold {
  background: linear-gradient(135deg, #ffd700, #ffb300);
  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.4);
}

.rank-silver {
  background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
  box-shadow: 0 2px 6px rgba(192, 192, 192, 0.4);
}

.rank-bronze {
  background: linear-gradient(135deg, #cd7f32, #b8682a);
  box-shadow: 0 2px 6px rgba(205, 127, 50, 0.4);
}

.rank-number {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

/* 净胜球颜色 */
.gd-positive {
  color: #67c23a;
  font-weight: 600;
}

.gd-negative {
  color: #f56c6c;
  font-weight: 600;
}

.gd-zero {
  color: #909399;
}

/* 积分高亮 */
.points-cell {
  font-size: 16px;
  font-weight: 700;
  color: #e63946;
}

/* 出线行 - 绿色背景 */
:deep(.qualify-row td.el-table__cell) {
  background-color: #f0f9eb !important;
}

/* 最佳第三行 - 黄橙色背景 */
:deep(.best-third-row td.el-table__cell) {
  background-color: #fdf6ec !important;
}

/* 深度选择器：调整 el-table 斑马纹颜色 */
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: #fafbfc;
}

/* 出线行和最佳第三行的 hover 效果 */
:deep(.qualify-row:hover > td.el-table__cell) {
  background-color: #e1f3d8 !important;
}

:deep(.best-third-row:hover > td.el-table__cell) {
  background-color: #faecd8 !important;
}

:deep(.el-tabs--border-card) {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

:deep(.el-tabs__item.is-active) {
  font-weight: 600;
}
</style>

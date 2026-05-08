<template>
  <div class="group-team-management" v-loading="loading">
    <div class="page-header">
      <h2>小组队伍管理</h2>
      <p class="page-desc">管理各小组的参赛队伍</p>
    </div>

    <el-collapse v-model="activeGroups" class="group-collapse">
      <el-collapse-item
        v-for="group in groups"
        :key="group.id"
        :name="group.id"
      >
        <template #title>
          <div class="group-header">
            <el-tag type="primary" effect="dark" size="large">{{ group.group_name }}</el-tag>
            <el-tag size="small" type="info">
              {{ (groupTeams[group.id] || []).length }} 支队伍
            </el-tag>
          </div>
        </template>

        <div class="group-content">
          <!-- 队伍列表 -->
          <el-table
            :data="groupTeams[group.id] || []"
            stripe
            style="width: 100%"
            empty-text="暂无队伍"
          >
            <el-table-column prop="team_name" label="队伍名称" min-width="200" />
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleDeleteTeam(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 添加队伍表单 -->
          <div class="add-team-form">
            <el-input
              v-model="newTeamNames[group.id]"
              placeholder="输入队伍名称"
              clearable
              style="width: 300px"
              @keyup.enter="handleAddTeam(group.id)"
            >
              <template #prefix>
                <el-icon><Plus /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              @click="handleAddTeam(group.id)"
              :disabled="!newTeamNames[group.id] || !newTeamNames[group.id].trim()"
            >
              添加队伍
            </el-button>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(true)
const groups = ref([])
const groupTeams = ref({})
const activeGroups = ref([])
const newTeamNames = reactive({})

const fetchGroups = async () => {
  try {
    loading.value = true
    const res = await adminAPI.getGroups()
    groups.value = res.groups || []
    groupTeams.value = res.group_teams || {}
    // 默认展开第一个小组
    if (groups.value.length > 0) {
      activeGroups.value = [groups.value[0].id]
    }
  } catch (error) {
    console.error('获取小组数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAddTeam = async (groupId) => {
  const teamName = (newTeamNames[groupId] || '').trim()
  if (!teamName) return

  try {
    await adminAPI.addTeam(teamName, groupId)
    ElMessage.success(`队伍 "${teamName}" 添加成功`)
    newTeamNames[groupId] = ''
    await fetchGroups()
  } catch (error) {
    // Error is handled by interceptor
  }
}

const handleDeleteTeam = async (team) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除队伍 "${team.team_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await adminAPI.deleteTeam(team.id)
    ElMessage.success(`队伍 "${team.team_name}" 已删除`)
    await fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除队伍失败:', error)
    }
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style scoped>
.group-team-management {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.group-collapse {
  border: none;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-content {
  padding: 16px 0 8px 0;
}

.add-team-form {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>

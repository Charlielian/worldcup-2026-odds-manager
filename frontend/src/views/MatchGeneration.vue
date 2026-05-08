<template>
  <div class="match-generation" v-loading="loading">
    <div class="page-header">
      <h2>比赛生成</h2>
      <p class="page-desc">为各小组自动生成循环赛赛程，或手动添加比赛</p>
    </div>

    <!-- 小组卡片 -->
    <div class="group-cards">
      <el-card
        v-for="group in groups"
        :key="group.id"
        class="group-card"
        shadow="hover"
      >
        <template #header>
          <div class="group-card-header">
            <el-tag type="primary" effect="dark" size="large">{{ group.group_name }}</el-tag>
            <el-tag size="small" type="info">
              {{ (groupTeams[group.id] || []).length }} 支队伍
            </el-tag>
          </div>
        </template>

        <div class="group-teams-list">
          <div
            v-for="team in (groupTeams[group.id] || [])"
            :key="team.id"
            class="team-item"
          >
            <el-icon color="#0047AB"><User /></el-icon>
            <span>{{ team.team_name }}</span>
          </div>
          <div v-if="!groupTeams[group.id] || groupTeams[group.id].length === 0" class="no-teams">
            暂无队伍，请先在队伍管理中添加
          </div>
        </div>

        <div class="group-card-footer">
          <el-button
            type="primary"
            @click="handleGenerate(group)"
            :disabled="!groupTeams[group.id] || groupTeams[group.id].length < 2"
            :loading="generatingGroupId === group.id"
          >
            <el-icon><SetUp /></el-icon>
            生成比赛
          </el-button>
          <span v-if="!groupTeams[group.id] || groupTeams[group.id].length < 2" class="tip-text">
            至少需要2支队伍
          </span>
        </div>
      </el-card>
    </div>

    <!-- 手动添加比赛 -->
    <el-card class="manual-card" shadow="hover">
      <template #header>
        <div class="manual-header">
          <span class="manual-title">手动添加小组赛</span>
        </div>
      </template>

      <el-form
        ref="manualFormRef"
        :model="manualForm"
        :rules="manualRules"
        label-width="90px"
        label-position="right"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="队伍1" prop="team1">
              <el-input v-model="manualForm.team1" placeholder="请输入队伍1名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="队伍2" prop="team2">
              <el-input v-model="manualForm.team2" placeholder="请输入队伍2名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="比赛时间" prop="match_time">
              <el-date-picker
                v-model="manualForm.match_time"
                type="datetime"
                placeholder="选择比赛时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="小组" prop="group_name">
              <el-select v-model="manualForm.group_name" placeholder="选择小组" style="width: 100%">
                <el-option
                  v-for="group in groups"
                  :key="group.id"
                  :label="group.group_name"
                  :value="group.group_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button
            type="success"
            @click="handleAddMatch"
            :loading="addingMatch"
          >
            <el-icon><CirclePlus /></el-icon>
            添加比赛
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SetUp, CirclePlus } from '@element-plus/icons-vue'

const loading = ref(true)
const generatingGroupId = ref(null)
const addingMatch = ref(false)
const groups = ref([])
const groupTeams = ref({})
const manualFormRef = ref(null)

const manualForm = reactive({
  team1: '',
  team2: '',
  match_time: '',
  group_name: ''
})

const manualRules = {
  team1: [{ required: true, message: '请输入队伍1名称', trigger: 'blur' }],
  team2: [{ required: true, message: '请输入队伍2名称', trigger: 'blur' }],
  match_time: [{ required: true, message: '请选择比赛时间', trigger: 'change' }],
  group_name: [{ required: true, message: '请选择小组', trigger: 'change' }]
}

const fetchGroups = async () => {
  try {
    loading.value = true
    const res = await adminAPI.getGroups()
    groups.value = res.groups || []
    groupTeams.value = res.group_teams || {}
  } catch (error) {
    console.error('获取小组数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleGenerate = async (group) => {
  const teamCount = (groupTeams.value[group.id] || []).length
  try {
    await ElMessageBox.confirm(
      `确定要为 ${group.group_name}（${teamCount} 支队伍）生成循环赛赛程吗？`,
      '确认生成',
      {
        confirmButtonText: '确定生成',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    generatingGroupId.value = group.id
    await adminAPI.generateMatches(group.id)
    ElMessage.success(`${group.group_name} 比赛生成成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('生成比赛失败:', error)
    }
  } finally {
    generatingGroupId.value = null
  }
}

const handleAddMatch = async () => {
  if (!manualFormRef.value) return

  try {
    await manualFormRef.value.validate()
  } catch {
    return
  }

  try {
    addingMatch.value = true
    await adminAPI.addGroupMatch(
      manualForm.team1,
      manualForm.team2,
      manualForm.match_time,
      manualForm.group_name
    )
    ElMessage.success('比赛添加成功')
    // 重置表单
    manualForm.team1 = ''
    manualForm.team2 = ''
    manualForm.match_time = ''
    manualForm.group_name = ''
    manualFormRef.value.resetFields()
  } catch (error) {
    // Error is handled by interceptor
  } finally {
    addingMatch.value = false
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style scoped>
.match-generation {
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

.group-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.group-card {
  border-radius: 12px;
}

.group-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.group-teams-list {
  min-height: 60px;
  margin-bottom: 16px;
}

.team-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 14px;
  color: #606266;
}

.no-teams {
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 16px 0;
}

.group-card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.tip-text {
  font-size: 12px;
  color: #909399;
}

.manual-card {
  border-radius: 12px;
}

.manual-header {
  display: flex;
  align-items: center;
}

.manual-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 768px) {
  .group-cards {
    grid-template-columns: 1fr;
  }
}
</style>

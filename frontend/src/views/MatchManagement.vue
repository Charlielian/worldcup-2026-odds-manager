<template>
  <div class="match-management" v-loading="loading">
    <div class="page-header">
      <h2>比赛管理</h2>
      <p class="page-desc">管理所有小组赛比赛信息</p>
    </div>

    <el-table
      :data="matches"
      stripe
      style="width: 100%"
      empty-text="暂无比赛数据"
      max-height="600"
    >
      <el-table-column prop="id" label="ID" width="70" align="center" />
      <el-table-column prop="team1" label="队伍1" min-width="120" />
      <el-table-column prop="team2" label="队伍2" min-width="120" />
      <el-table-column label="比赛时间" min-width="160">
        <template #default="{ row }">
          {{ row.match_time || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="group_name" label="小组" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.group_name" size="small" type="primary" effect="plain">
            {{ row.group_name }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.status === 'finished' ? 'success' : 'warning'"
            size="small"
            effect="dark"
          >
            {{ row.status === 'finished' ? '已结束' : '未开始' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="比分" width="80" align="center">
        <template #default="{ row }">
          <span v-if="row.status === 'finished' && row.score1 !== null && row.score2 !== null">
            {{ row.score1 }} : {{ row.score2 }}
          </span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            text
            @click="openEditDialog(row)"
          >
            编辑
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑比赛"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
        label-position="right"
      >
        <el-form-item label="队伍1" prop="team1">
          <el-input v-model="editForm.team1" placeholder="请输入队伍1名称" />
        </el-form-item>
        <el-form-item label="队伍2" prop="team2">
          <el-input v-model="editForm.team2" placeholder="请输入队伍2名称" />
        </el-form-item>
        <el-form-item label="比赛时间" prop="match_time">
          <el-date-picker
            v-model="editForm.match_time"
            type="datetime"
            placeholder="选择比赛时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="小组" prop="group_name">
          <el-select v-model="editForm.group_name" placeholder="选择小组" style="width: 100%">
            <el-option
              v-for="g in groupOptions"
              :key="g"
              :label="g"
              :value="g"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="选择状态" style="width: 100%">
            <el-option label="未开始" value="upcoming" />
            <el-option label="已结束" value="finished" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.status === 'finished'" label="比分1" prop="score1">
          <el-input-number v-model="editForm.score1" :min="0" :max="99" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="editForm.status === 'finished'" label="比分2" prop="score2">
          <el-input-number v-model="editForm.score2" :min="0" :max="99" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { adminAPI } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(true)
const saving = ref(false)
const matches = ref([])
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editingMatchId = ref(null)

const groupOptions = [
  'A组', 'B组', 'C组', 'D组', 'E组', 'F组', 'G组', 'H组',
  'I组', 'J组', 'K组', 'L组'
]

const editForm = reactive({
  team1: '',
  team2: '',
  match_time: '',
  group_name: '',
  status: 'upcoming',
  score1: 0,
  score2: 0
})

const editRules = {
  team1: [{ required: true, message: '请输入队伍1名称', trigger: 'blur' }],
  team2: [{ required: true, message: '请输入队伍2名称', trigger: 'blur' }],
  match_time: [{ required: true, message: '请选择比赛时间', trigger: 'change' }],
  group_name: [{ required: true, message: '请选择小组', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const fetchMatches = async () => {
  try {
    loading.value = true
    const res = await adminAPI.getMatches()
    matches.value = res.matches || []
  } catch (error) {
    console.error('获取比赛数据失败:', error)
  } finally {
    loading.value = false
  }
}

const openEditDialog = (row) => {
  editingMatchId.value = row.id
  editForm.team1 = row.team1 || ''
  editForm.team2 = row.team2 || ''
  editForm.match_time = row.match_time || ''
  editForm.group_name = row.group_name || ''
  editForm.status = row.status || 'upcoming'
  editForm.score1 = row.score1 ?? 0
  editForm.score2 = row.score2 ?? 0
  editDialogVisible.value = true
}

const handleSave = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
  } catch {
    return
  }

  try {
    saving.value = true
    const data = {
      team1: editForm.team1,
      team2: editForm.team2,
      match_time: editForm.match_time,
      group_name: editForm.group_name,
      status: editForm.status
    }
    if (editForm.status === 'finished') {
      data.score1 = editForm.score1
      data.score2 = editForm.score2
    }
    await adminAPI.updateMatch(editingMatchId.value, data)
    ElMessage.success('比赛信息更新成功')
    editDialogVisible.value = false
    await fetchMatches()
  } catch (error) {
    // Error is handled by interceptor
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchMatches()
})
</script>

<style scoped>
.match-management {
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

.text-muted {
  color: #c0c4cc;
}
</style>

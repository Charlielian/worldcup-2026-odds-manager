<template>
  <el-container class="app-container">
    <!-- 顶部标题栏 -->
    <el-header class="app-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <el-icon :size="28" class="header-icon"><Trophy /></el-icon>
          <h1 class="header-title">2026世界杯赛事对战+足彩赔率管理系统</h1>
        </div>
        <div class="header-right">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期查看赛程"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="navigateToDate"
            style="width: 200px;"
          >
            <template #prefix>
              <el-icon><Calendar /></el-icon>
            </template>
          </el-date-picker>
        </div>
      </div>
    </el-header>

    <!-- 水平导航菜单 -->
    <el-menu
      :default-active="route.path"
      mode="horizontal"
      class="app-menu"
      :ellipsis="false"
      router
    >
      <el-menu-item index="/">
        <el-icon><Soccer /></el-icon>
        <span>主页</span>
      </el-menu-item>
      <el-menu-item index="/live">
        <el-icon><Clock /></el-icon>
        <span>实时赔率</span>
      </el-menu-item>
      <el-menu-item index="/group_stage">
        <el-icon><Trophy /></el-icon>
        <span>小组赛</span>
      </el-menu-item>
      <el-sub-menu index="knockout">
        <template #title>
          <el-icon><Trophy /></el-icon>
          <span>淘汰赛</span>
        </template>
        <el-menu-item index="/knockout">淘汰赛赛程</el-menu-item>
        <el-menu-item index="/knockout/bracket">赛程图</el-menu-item>
      </el-sub-menu>
      <el-menu-item index="/rankings">
        <el-icon><DataAnalysis /></el-icon>
        <span>排名</span>
      </el-menu-item>
      <el-sub-menu index="admin">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>管理</span>
        </template>
        <el-menu-item index="/admin/group_team_management">小组队伍管理</el-menu-item>
        <el-menu-item index="/admin/match_management">比赛管理</el-menu-item>
        <el-menu-item index="/admin/match_generation">比赛生成</el-menu-item>
      </el-sub-menu>
    </el-menu>

    <!-- 主内容区域 -->
    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Calendar, Trophy, Soccer, DataAnalysis, Setting, Menu, Clock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const selectedDate = ref('')

const today = computed(() => {
  const now = new Date()
  return now.toISOString().split('T')[0]
})

onMounted(() => {
  selectedDate.value = route.query.date || today.value
})

watch(() => route.query.date, (newDate) => {
  if (newDate) {
    selectedDate.value = newDate
  }
})

const navigateToDate = (date) => {
  if (date) {
    router.push({ path: '/', query: { date } })
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #001f5c 0%, #0047AB 50%, #003366 100%);
  padding: 16px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  color: #ffc107;
}

.header-title {
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
  white-space: nowrap;
}

.header-right {
  flex-shrink: 0;
}

.app-menu {
  background: linear-gradient(180deg, #002244 0%, #001a33 100%);
  border-bottom: 2px solid #ffc107;
  display: flex;
  justify-content: center;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 99;
}

.app-menu :deep(.el-menu-item),
.app-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  font-weight: 500;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}

.app-menu :deep(.el-menu-item:hover),
.app-menu :deep(.el-sub-menu__title:hover) {
  color: #ffc107;
  background-color: rgba(255, 255, 255, 0.08);
}

.app-menu :deep(.el-menu-item.is-active) {
  color: #ffc107;
  border-bottom-color: #ffc107;
  background-color: rgba(255, 193, 7, 0.1);
  font-weight: 600;
}

.app-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: #ffc107;
  border-bottom-color: #ffc107;
}

.app-menu :deep(.el-sub-menu .el-menu) {
  background-color: #002244;
}

.app-menu :deep(.el-sub-menu .el-menu-item) {
  color: rgba(255, 255, 255, 0.85);
  min-width: 180px;
}

.app-menu :deep(.el-sub-menu .el-menu-item:hover) {
  color: #ffc107;
  background-color: rgba(255, 255, 255, 0.08);
}

.app-menu :deep(.el-sub-menu .el-menu-item.is-active) {
  color: #ffc107;
  background-color: rgba(255, 193, 7, 0.1);
}

.app-main {
  background-color: #f0f2f5;
  min-height: calc(100vh - 140px);
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 路由切换过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 日期选择器深色主题适配 */
.header-right :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: none;
}

.header-right :deep(.el-input__wrapper:hover) {
  border-color: #ffc107;
}

.header-right :deep(.el-input__wrapper.is-focus) {
  border-color: #ffc107;
  box-shadow: 0 0 0 1px rgba(255, 193, 7, 0.3);
}

.header-right :deep(.el-input__inner) {
  color: #ffffff;
}

.header-right :deep(.el-input__prefix .el-icon) {
  color: #ffc107;
}

.header-right :deep(.el-input__suffix .el-icon) {
  color: rgba(255, 255, 255, 0.7);
}

/* 响应式 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
  }

  .header-title {
    font-size: 16px;
    text-align: center;
  }

  .header-right {
    width: 100%;
  }

  .header-right :deep(.el-date-editor) {
    width: 100% !important;
  }

  .app-main {
    padding: 16px;
  }
}
</style>

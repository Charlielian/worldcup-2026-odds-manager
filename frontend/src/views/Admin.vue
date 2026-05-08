<template>
  <div class="admin-layout">
    <el-container class="admin-container">
      <el-aside width="220px" class="admin-aside">
        <div class="aside-header">
          <el-icon :size="24" color="#0047AB"><Setting /></el-icon>
          <span class="aside-title">管理后台</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="admin-menu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#0047AB"
        >
          <el-menu-item index="/admin/group_team_management">
            <el-icon><User /></el-icon>
            <span>小组队伍管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/match_management">
            <el-icon><List /></el-icon>
            <span>比赛管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/match_generation">
            <el-icon><Plus /></el-icon>
            <span>比赛生成</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Setting, User, List, Plus } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.admin-layout {
  min-height: 100%;
}

.admin-container {
  min-height: calc(100vh - 160px);
}

.admin-aside {
  background-color: #304156;
  border-radius: 8px;
  overflow: hidden;
  margin-right: 16px;
}

.aside-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.aside-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.admin-menu {
  border-right: none;
}

.admin-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  font-size: 14px;
}

.admin-menu .el-menu-item:hover {
  background-color: #263445 !important;
}

.admin-menu .el-menu-item.is-active {
  background-color: #263445 !important;
  border-right: 3px solid #0047AB;
}

.admin-main {
  background-color: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  min-height: calc(100vh - 200px);
}
</style>

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/betting',
    name: 'Betting',
    component: () => import('../views/Betting.vue')
  },
  {
    path: '/live',
    name: 'LiveMatches',
    component: () => import('../views/LiveMatches.vue')
  },
  {
    path: '/group_stage',
    name: 'GroupStage',
    component: () => import('../views/GroupStage.vue')
  },
  {
    path: '/group_stage/:group',
    name: 'GroupStageWithGroup',
    component: () => import('../views/GroupStage.vue')
  },
  {
    path: '/knockout',
    name: 'Knockout',
    component: () => import('../views/Knockout.vue')
  },
  {
    path: '/knockout/bracket',
    name: 'KnockoutBracket',
    component: () => import('../views/KnockoutBracket.vue')
  },
  {
    path: '/rankings',
    name: 'Rankings',
    component: () => import('../views/Rankings.vue')
  },
  {
    path: '/rankings/:group',
    name: 'RankingsWithGroup',
    component: () => import('../views/Rankings.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin.vue'),
    children: [
      {
        path: 'group_team_management',
        name: 'GroupTeamManagement',
        component: () => import('../views/GroupTeamManagement.vue')
      },
      {
        path: 'match_management',
        name: 'MatchManagement',
        component: () => import('../views/MatchManagement.vue')
      },
      {
        path: 'match_generation',
        name: 'MatchGeneration',
        component: () => import('../views/MatchGeneration.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
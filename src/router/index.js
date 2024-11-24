// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import MonitoringView from '../views/MonitoringView.vue'

// Add debug logging
console.log('Router initialization')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: MonitoringView,
      // Add navigation guard for debugging
      beforeEnter: (to, from, next) => {
        console.log('Entering monitor route')
        next()
      }
    }
  ]
})

// Add global navigation debugging
router.beforeEach((to, from, next) => {
  console.log('Navigation:', {
    to: to.path,
    name: to.name
  })
  next()
})

export default router
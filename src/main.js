// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import '@fortawesome/fontawesome-free/css/all.css'

// Create the app instance
const app = createApp(App)

// Create the Pinia instance
const pinia = createPinia()

// Use plugins
app.use(pinia)  // Changed from app.use(createPinia())
app.use(router)

// Mount the app
app.mount('#app')
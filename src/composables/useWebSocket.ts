// src/composables/useWebSocket.ts
import { useSessionStore } from '../stores/sessionStore'
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface WebSocketMessage {
    type: string;
    timestamp: string;
    [key: string]: any;
  }

export const useWebSocket = (url: string) => {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const lastError = ref<string | null>(null)
  const sessionStore = useSessionStore()
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY = 1000 // 1 second
  const ERROR_STATES = {
    CONNECTION_LOST: '[החיבור נותק]{dir="rtl"}',
    MAX_ATTEMPTS: '[נכשל להתחבר לאחר מספר ניסיונות]{dir="rtl"}',
    INVALID_SESSION: '[פג תוקף החיבור]{dir="rtl"}'
  } as const
  let reconnectTimeout: NodeJS.Timeout | null = null
  let pingInterval: NodeJS.Timeout | null = null


 
  const connect = () => {
    if (ws.value?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket already connected')
      return
    }

    try {
      
      if (ws.value) {
        ws.value.close(1000, 'Closing before reconnect')
        ws.value = null
        }

      const wsUrl = sessionStore.sessionToken 
        ? `${url}?token=${sessionStore.sessionToken}`
        : url

      ws.value = new WebSocket(url)
      
      
      ws.value.onopen = () => {
        console.log('WebSocket connected')
        isConnected.value = true
        reconnectAttempts.value = 0
        startPingInterval()
        
        // Send initial session data
        const sessionData = {
          type: 'session_start',
          customerId: sessionStore.customerId,
          timestamp: new Date().toISOString()
        }
        send(sessionData)
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
          lastError.value = '[שגיאה בקבלת נתונים]{dir="rtl"}'
        }
      }

      ws.value.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        isConnected.value = false
        stopPingInterval()
        
        if (event.code !== 1000 && event.code !== 1001 ) { // Not a normal closure
          lastError.value = '[החיבור נסגר]{dir="rtl"}'
          handleReconnect()
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        isConnected.value = false
        lastError.value = '[שגיאה בחיבור]{dir="rtl"}'
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      lastError.value = '[שגיאה ביצירת חיבור]{dir="rtl"}'
    }
  }

  const disconnect = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      // Send cleanup message
      const cleanupData = {
        type: 'session_end',
        sessionId: sessionStore.sessionToken,
        timestamp: new Date().toISOString()
      }
      send(cleanupData)
      
      ws.value.close(1000, 'Normal closure')
    }
    
    stopPingInterval()
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
  }

  const handleReconnect = () => {
    if (reconnectAttempts.value >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached')
      lastError.value = '[נכשל להתחבר לאחר מספר ניסיונות]{dir="rtl"}'
      return
    }

    reconnectAttempts.value++
    console.log(`Attempting to reconnect (${reconnectAttempts.value}/${MAX_RECONNECT_ATTEMPTS})`)
    
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    
    reconnectTimeout = setTimeout(() => {
      connect()
    }, RECONNECT_DELAY * Math.min(reconnectAttempts.value, 5))
  }

  const send = (data: any) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  const startPingInterval = () => {
    stopPingInterval() // Clear any existing interval
    pingInterval = setInterval(() => {
      send({ type: 'ping', timestamp: new Date().toISOString() })
    }, 30000) // 30 seconds
  }

  const stopPingInterval = () => {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
  }

  const handleMessage = (data: any) => {
    switch (data.type) {
      case 'pong':
        // Handle ping response
        sessionStore.updateLastActivity()
        break
      case 'session_update':
        if (sessionStore.validateSession()) {
          sessionStore.updateLastActivity()
        } else {
          disconnect()
        }
        break
      case 'metrics_update':
        // Emit metrics update event
        window.dispatchEvent(new CustomEvent('metrics_update', { detail: data }))
        break
      default:
        console.log('Unhandled message type:', data.type)
    }
  }

  // Watch for session changes
  watch(() => sessionStore.sessionToken, (newToken) => {
    if (newToken && isConnected.value) {
      send({
        type: 'session_update',
        sessionId: newToken,
        timestamp: new Date().toISOString()
      })
    }
  })

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    lastError,
    send,
    connect,
    disconnect
  }
}

export default useWebSocket
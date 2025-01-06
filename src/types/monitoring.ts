// src/types/monitoring.ts
import { ref, onMounted, onUnmounted } from 'vue'

// Define interface locally
interface WebSocketError {
  message: string;
  code?: number;
}

export function useWebSocket(customerId: string) {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const lastMessage = ref<any>(null)
  const error = ref<WebSocketError | null>(null)

  // Rest of your WebSocket code...
}
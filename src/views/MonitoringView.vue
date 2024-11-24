// MonitoringView.vue
<script setup>
import { ref, computed, onMounted, onUnmounted, watch, watchEffect, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import LineChart from '../components/LineChart.vue'
import SessionDetailsModal from '../components/SessionDetailsModal.vue'
import { useSessionStore } from '../stores/sessionStore'
import { chatService } from '@/services/api'


const sessionTime = ref('00:00');
const sessionStartTime = ref(new Date());
const sessionTimerInterval = ref(null);

const SESSION_STORAGE_KEY = 'activeSessions';
// Router and Store setup
const router = useRouter()
const sessionStore = useSessionStore()

// Basic state
const isLoading = ref(false)
const error = ref(null)
const intervals = ref([])

// UI state
const activeTab = ref('realtime')
const searchQuery = ref('')
const filterStatus = ref('all')
const isModalOpen = ref(false)
const selectedSession = ref(null)

// Session state
const activeSessions = ref([])
const hasCleanedUp = ref(false);


// Chart setup
const chartData = ref({
  labels: ['00:00'],
  datasets: [{
    label: 'Session Activity',
    data: [0],
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    tension: 0.4,
    fill: true
  }]
})

// Tabs configuration
const tabs = [
  { id: 'realtime', label: 'Realtime' },
  { id: 'historical', label: 'Historical' },
  { id: 'alerts', label: 'Alerts' }
]

// Stats computation
const stats = computed(() => {
  const sessionCount = activeSessions.value.length;
  
  return [
    {
      label: 'Active Sessions',
      value: sessionCount.toString(),
      icon: 'fa-users',
      iconClass: sessionCount > 0 ? 'text-green-500' : 'text-gray-500'
    },
    {
      label: 'Session Time',
      value: sessionTime.value,
      icon: 'fa-clock',
      iconClass: 'text-blue-500'
    },
    {
      label: 'Customer Plan',
      value: sessionStore.customerData?.plan || 'Standard Plan',
      icon: 'fa-star',
      iconClass: 'text-yellow-500'
    }
  ];
});


const generateSessionId = (customerId) => {
  return `session_${customerId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const currentTabId = ref(Math.random().toString(36).substr(2, 9));

const sessionDebug = computed(() => {
  return {
    activeSessionsCount: activeSessions.value.length,
    hasSessionToken: !!sessionStore.sessionToken,
    hasCustomerId: !!sessionStore.customerId,
    currentTabId: currentTabId.value,
    storedSessions: getStoredSessions().length
  };
});

const startSessionTimer = () => {
  // Clear any existing timer
  if (sessionTimerInterval.value) {
    clearInterval(sessionTimerInterval.value);
  }

  // Reset start time
  sessionStartTime.value = new Date();
  
  // Start new timer
  sessionTimerInterval.value = setInterval(() => {
    const now = new Date();
    const diff = Math.floor((now - sessionStartTime.value) / 1000);
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    sessionTime.value = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }, 1000);

  // Add to intervals for cleanup
  intervals.value.push(sessionTimerInterval.value);
};


const filteredSessions = computed(() => {
  if (!activeSessions.value) return []
  
  return activeSessions.value.filter(session => {
    if (!session.customerId) return false
    
    const matchesSearch = session.customerId.toString()
      .toLowerCase()
      .includes(searchQuery.value.toLowerCase())
      
    const matchesStatus = filterStatus.value === 'all' || 
      session.status.toLowerCase() === filterStatus.value.toLowerCase()
      
    return matchesSearch && matchesStatus
  })
})



const getStoredSessions = () => {
  try {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error getting stored sessions:', error);
    return [];
  }
};

const addOrUpdateSession = (newSession) => {
  try {
    console.group('Adding/Updating Session');
    const sessions = getStoredSessions();
    
    // Add tab ID and ensure proper start time
    const sessionWithTab = {
      ...newSession,
      tabId: currentTabId.value,
      startTime: newSession.startTime || new Date().toISOString(), // Ensure start time exists
      lastActivity: new Date().toISOString()
    };

    // Check if session exists for this tab
    const existingIndex = sessions.findIndex(s => s.tabId === currentTabId.value);
    
    if (existingIndex >= 0) {
      // Update existing session but preserve original start time
      sessions[existingIndex] = {
        ...sessions[existingIndex],
        ...sessionWithTab,
        startTime: sessions[existingIndex].startTime, // Keep original start time
        lastActivity: new Date().toISOString()
      };
    } else {
      // Add new session with current time as start time
      sessions.push(sessionWithTab);
    }

    console.log('Updated sessions array:', sessions);
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
    return sessions;
  } catch (error) {
    console.error('Error updating sessions:', error);
    return [];
  } finally {
    console.groupEnd();
  }
};

// Core functions

const cleanupSession = () => {
  try {
    if (hasCleanedUp.value) return;
    
    console.log('Cleaning up session for tab:', currentTabId.value);
    const sessions = getStoredSessions();
    const updatedSessions = sessions.filter(s => s.tabId !== currentTabId.value);
    
    // Update localStorage
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(updatedSessions));
    
    // Clear session timer
    if (sessionTimerInterval.value) {
      clearInterval(sessionTimerInterval.value);
    }
    
    // Force UI update by dispatching storage event
    window.dispatchEvent(new StorageEvent('storage', {
      key: SESSION_STORAGE_KEY,
      newValue: JSON.stringify(updatedSessions)
    }));

    hasCleanedUp.value = true;
    
    // Update active sessions directly
    activeSessions.value = activeSessions.value.filter(s => s.tabId !== currentTabId.value);
    
    console.log('Remaining sessions after cleanup:', updatedSessions.length);
  } catch (error) {
    console.error('Error cleaning up session:', error);
  }
};


const updateSessionData = () => {
  try {
    console.group('===== Updating Session Data =====');
    
    const sessions = getStoredSessions();
    console.log('Retrieved stored sessions:', sessions);
    
    const now = new Date();
    const fiveMinutesAgo = new Date(now - 5 * 60 * 1000);

    // Clean up stale sessions first
    const activeAndValidSessions = sessions.filter(session => {
      if (!session || !session.lastActivity) return false;
      
      const lastActive = new Date(session.lastActivity);
      const isActive = !isNaN(lastActive) && lastActive >= fiveMinutesAgo;
      
      if (!isActive) {
        console.log('Removing stale session:', session.id);
      }
      
      return isActive;
    });

    // Update storage with only active sessions
    if (activeAndValidSessions.length !== sessions.length) {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(activeAndValidSessions));
      console.log('Cleaned up stale sessions. Remaining:', activeAndValidSessions.length);
    }

    // Process active sessions for display
    const processedSessions = activeAndValidSessions.map(session => ({
      id: session.id,
      customerId: session.customerId,
      customerName: session.customerName || 'Unknown',
      duration: calculateDuration(new Date(session.startTime)),
      status: 'Active',
      lastActivity: new Date(session.lastActivity).toLocaleTimeString(),
      plan: session.plan || 'Standard Plan',
      tabId: session.tabId
    }));

    console.log('Final processed sessions:', processedSessions);
    activeSessions.value = processedSessions;

  } catch (error) {
    console.error('Error in updateSessionData:', error);
  } finally {
    console.groupEnd();
  }
};

// Add storage event handler
  const handleStorageChange = (event) => {
    if (event.key === SESSION_STORAGE_KEY) {
      console.log('Storage event triggered - updating sessions');
      // Check if our session was removed by another tab
      const sessions = getStoredSessions();
      const hasOurSession = sessions.some(s => s.tabId === currentTabId.value);
      
      if (!hasOurSession && sessionStore.sessionToken) {
        // Our session was removed, re-add it
        const currentSession = {
          id: generateSessionId(sessionStore.customerId),
          customerId: sessionStore.customerId,
          customerName: sessionStore.customerData?.name || 'Loading...',
          startTime: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          plan: sessionStore.customerData?.plan || 'Standard Plan',
          tabId: currentTabId.value
        };
        
        addOrUpdateSession(currentSession);
      } else {
        updateSessionData();
      }
    }
  };

const updateChartData = () => {
  const now = new Date().toLocaleTimeString()
  const sessionCount = activeSessions.value.length

  chartData.value = {
    ...chartData.value,
    labels: [...(chartData.value.labels || []), now].slice(-10),
    datasets: [{
      ...chartData.value.datasets[0],
      data: [...(chartData.value.datasets[0].data || []), sessionCount].slice(-10)
    }]
  }
}

// Helper functions
const calculateDuration = (startTime) => {
  try {
    const start = startTime ? new Date(startTime) : sessionStartTime.value;
    if (isNaN(start.getTime())) {
      console.warn('Invalid start time, using session start time');
      start = sessionStartTime.value;
    }

    const now = new Date();
    const diff = Math.max(0, Math.floor((now - start) / 1000));
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  } catch (error) {
    console.error('Error calculating duration:', error);
    return '00:00';
  }
};

const getSessionDuration = () => {
  const start = sessionStartTime.value;
  const now = new Date();
  const diff = Math.max(0, Math.floor((now - start) / 1000));
  const mins = Math.floor(diff / 60);
  const secs = diff % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};



const getStatusClass = (status) => {
  return status === 'Active' 
    ? 'bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full'
    : 'bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full'
}

const showSessionDetails = (session) => {
  selectedSession.value = {
    ...session,
    activities: [
      `Session started at ${new Date(sessionStore.lastActivity).toLocaleTimeString()}`,
      `Last activity: ${session.lastActivity}`,
      `Customer Plan: ${session.customerName}`
    ]
  }
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedSession.value = null
}

const refreshSessions = () => {
  console.log('Manually refreshing sessions...');
  updateSessionData();
};

// Lifecycle hooks
onMounted(async () => {
  try {
    console.group('Mounting Monitor Component');
    isLoading.value = true;

    // Start session timer
    startSessionTimer();

    // Add beforeunload listener
    window.addEventListener('beforeunload', cleanupSession);
    
    // Add visibility change listener to handle tab close
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        cleanupSession();
      }
    });

    // Initial data load and setup remaining intervals
    await updateSessionData();
    
    const updateInterval = setInterval(() => {
      updateSessionData();
    }, 3000);

    intervals.value.push(updateInterval);

  } catch (error) {
    console.error('Mount error:', error);
    error.value = 'Failed to initialize monitoring';
  } finally {
    isLoading.value = false;
    console.groupEnd();
  }
});




const debugSessionCount = () => {
  console.group('Session Count Debug');
  try {
    const rawSessions = localStorage.getItem('activeSessions');
    console.log('Raw localStorage:', rawSessions);
    
    if (rawSessions) {
      const parsed = JSON.parse(rawSessions);
      console.log('Parsed sessions:', parsed);
      console.log('Is array?', Array.isArray(parsed));
      console.log('Length:', Array.isArray(parsed) ? parsed.length : 'not an array');
      
      // Check each session's validity
      if (Array.isArray(parsed)) {
        parsed.forEach((session, index) => {
          console.log(`Session ${index}:`, {
            id: session.id,
            customerId: session.customerId,
            lastActivity: session.lastActivity,
            isValid: session.id && session.customerId && session.lastActivity
          });
        });
      }
    }
  } catch (error) {
    console.error('Debug error:', error);
  }
  console.groupEnd();
};


onUnmounted(() => {
  try {
    // Clean up session
    cleanupSession();
    
    // Clear session timer specifically
    if (sessionTimerInterval.value) {
      clearInterval(sessionTimerInterval.value);
    }
    
    // Clean up event listeners
    window.removeEventListener('beforeunload', cleanupSession);
    document.removeEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        cleanupSession();
      }
    });
    window.removeEventListener('storage', handleStorageChange);
    
    // Clear all intervals
    intervals.value.forEach(clearInterval);
  } catch (error) {
    console.error('Error in unmount cleanup:', error);
  }
});

// Watchers
watch(() => sessionStore.isActive, (active) => {
  console.log('Session active state changed:', active);
  if (active) {
    updateSessionData();
  }
});

watch(() => sessionStore.sessionToken, (newToken) => {
  console.log('Session token changed:', newToken);
});

watch(() => activeSessions.value, (newSessions) => {
  console.log('Active sessions changed:', {
    length: newSessions.length,
    sessions: newSessions
  });
}, { deep: true });


watch(activeSessions, (newSessions) => {
  console.log('Active sessions changed:', {
    count: newSessions.length,
    sessions: newSessions
  });
}, { deep: true });

watch(activeSessions, () => {
  debugSessionCount();
}, { deep: true });

watch([() => sessionStore.sessionToken, () => sessionStore.customerId], 
  ([newToken, newCustomerId]) => {
    if (newToken && newCustomerId) {
      console.log('Session store updated:', { newToken, newCustomerId });
      
      const newSession = {
        id: generateSessionId(newCustomerId),
        customerId: newCustomerId,
        customerName: sessionStore.customerData?.name || 'Loading...',
        startTime: new Date().toISOString(), // Explicit start time
        lastActivity: new Date().toISOString(),
        plan: sessionStore.customerData?.plan || 'Standard Plan',
        tabId: currentTabId.value
      };

      addOrUpdateSession(newSession);
      nextTick(() => {
        updateSessionData();
      });
    }
  }, { immediate: true }
);

</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Debug Panel -->
    <div class="bg-white p-4 mb-4 rounded-lg shadow">
      <div class="flex justify-between items-center">
        <div class="space-y-2">
          <div class="text-sm">
            <strong>Active Sessions:</strong> {{ activeSessions.length }}
          </div>
          <div class="text-sm">
            <strong>Last Update:</strong> {{ new Date().toLocaleTimeString() }}
          </div>
        </div>
        <button 
          @click="refreshSessions"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh Sessions
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 p-4 border-l-4 border-red-500">
      <div class="flex">
        <div class="flex-shrink-0">
          <i class="fas fa-exclamation-circle text-red-400"></i>
        </div>
        <div class="ml-3">
          <p class="text-sm text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    </div>

    <!-- Header -->
    <div class="bg-white border-b border-gray-200 p-4">
      <h1 class="text-2xl font-bold text-gray-800">System Monitoring</h1>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
      <!-- Quick Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div v-for="(stat, index) in stats" 
             :key="index" 
             class="bg-white p-4 rounded-lg shadow">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">{{ stat.label }}</p>
              <p class="text-2xl font-bold">{{ stat.value }}</p>
            </div>
            <i :class="['fas', stat.icon, stat.iconClass]"></i>
          </div>
        </div>
      </div>

      <!-- Chart Section -->
      <div class="bg-white rounded-lg shadow mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex space-x-4 px-4">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'px-3 py-2 text-sm font-medium',
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <div class="p-4">
          <div class="h-64">
            <LineChart :chart-data="chartData" />
          </div>
        </div>
      </div>

      <!-- Session List -->
      <div class="bg-white rounded-lg shadow">
        <div class="px-4 py-3 border-b border-gray-200">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium">Active Sessions</h3>
            <div class="flex space-x-4">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search by Customer ID"
                class="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                v-model="filterStatus"
                class="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        <div class="p-4">
          <table class="min-w-full">
            <thead>
              <tr>
                <th class="text-left text-sm font-medium text-gray-500 pb-3">Customer ID</th>
                <th class="text-left text-sm font-medium text-gray-500 pb-3">Duration</th>
                <th class="text-left text-sm font-medium text-gray-500 pb-3">Status</th>
                <th class="text-left text-sm font-medium text-gray-500 pb-3">Last Activity</th>
                <th class="text-left text-sm font-medium text-gray-500 pb-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="activeSessions.length === 0">
                <td colspan="5" class="py-4 text-center text-gray-500">
                  No active sessions
                </td>
              </tr>
              <tr v-else v-for="session in filteredSessions" 
                  :key="session.id" 
                  class="border-t border-gray-100 hover:bg-gray-50">
                <td class="py-2">{{ session.customerId }}</td>
                <td>{{ session.duration }}</td>
                <td>
                  <span :class="getStatusClass(session.status)">
                    {{ session.status }}
                  </span>
                </td>
                <td>{{ session.lastActivity }}</td>
                <td>
                  <button 
                    @click="showSessionDetails(session)"
                    class="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Session Details Modal -->
    <SessionDetailsModal
      v-if="selectedSession"
      :session="selectedSession"
      :isOpen="isModalOpen"
      @close="closeModal"
    />
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  gap: 1rem;
}
</style>
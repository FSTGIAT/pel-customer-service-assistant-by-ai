// src/stores/sessionStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessionToken = ref(localStorage.getItem('sessionToken') || null)
  const customerId = ref(localStorage.getItem('customerId') || null) 
  const startTime = ref(localStorage.getItem('startTime') ? new Date(localStorage.getItem('startTime')) : null)
  const lastActivity = ref(localStorage.getItem('lastActivity') || null)
  const customerData = ref(JSON.parse(localStorage.getItem('customerData') || '{"id":null,"name":null,"plan":"Standard Plan"}'))
  const pdfFiles = ref([])
  const currentPdfIndex = ref(0)
  

  const getSessionToken = computed(() => sessionToken.value)

  const getActiveSession = async () => {
    const activeSessions = JSON.parse(localStorage.getItem('activeSessions') || '[]')
    return activeSessions.find(session => session.id === sessionToken.value)
  }

  const validateSession = () => {
    if (!sessionToken.value) {
      console.warn('No active session token')
      return false
    }
    return true
  }

  // Getters
  const isActive = computed(() => !!sessionToken.value)
  const sessionDuration = computed(() => {
    if (!startTime.value) return '00:00'
    const diff = Math.floor((Date.now() - new Date(startTime.value)) / 1000)
    const mins = Math.floor(diff / 60)
    const secs = diff % 60
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  })



  function initializeSession(sessionInfo) {
    console.log('===== Initialize Session =====');
    console.log('Initializing session with:', sessionInfo);
    
    if (!sessionInfo || !sessionInfo.customerId) {
      console.error('Invalid session info:', sessionInfo);
      throw new Error('Invalid session info provided');
    }
    
    // Create session ID if not provided
    const sessionId = sessionInfo.id || `session_${sessionInfo.customerId}_${Date.now()}`;
    const currentTime = new Date().toISOString();
    
    // Update store state
    sessionToken.value = sessionId;
    customerId.value = sessionInfo.customerId;
    startTime.value = new Date();
    lastActivity.value = currentTime;
    customerData.value = {
      id: sessionInfo.customerId,
      name: sessionInfo.customerName || 'Loading...',
      plan: sessionInfo.plan || 'Standard Plan'
    };
  
    // Create full session info
    const fullSessionInfo = {
      id: sessionId,
      customerId: sessionInfo.customerId,
      customerName: sessionInfo.customerName || 'Loading...',
      plan: sessionInfo.plan || 'Standard Plan',
      startTime: startTime.value.toISOString(),
      lastActivity: currentTime,
      status: 'Active'
    };
  
    // Save to localStorage
    localStorage.setItem('sessionToken', sessionId);
    localStorage.setItem('customerId', sessionInfo.customerId);
    localStorage.setItem('startTime', startTime.value.toISOString());
    localStorage.setItem('lastActivity', lastActivity.value);
    localStorage.setItem('customerData', JSON.stringify(customerData.value));
  
    // Update active sessions
    try {
      const sessions = JSON.parse(localStorage.getItem('activeSessions') || '[]');
      const filteredSessions = sessions.filter(s => s.customerId !== sessionInfo.customerId);
      filteredSessions.push(fullSessionInfo);
      localStorage.setItem('activeSessions', JSON.stringify(filteredSessions));
      
      console.log('Session initialization complete:', fullSessionInfo);
      console.log('Updated active sessions:', filteredSessions);
    } catch (error) {
      console.error('Error saving session:', error);
    }
  
    return fullSessionInfo;
  }

  function logSessionState() {
    console.log('Current Session State:', {
      token: sessionToken.value,
      customerId: customerId.value,
      startTime: startTime.value,
      lastActivity: lastActivity.value,
      activeSessions: JSON.parse(localStorage.getItem('activeSessions') || '[]')
    });
  }

  function updateLastActivity() {
    lastActivity.value = new Date().toISOString()
    localStorage.setItem('lastActivity', lastActivity.value)
    
    // Update in active sessions
    const sessions = JSON.parse(localStorage.getItem('activeSessions') || '[]')
    const updatedSessions = sessions.map(session => {
      if (session.id === sessionToken.value) {
        return { ...session, lastActivity: lastActivity.value }
      }
      return session
    })
    localStorage.setItem('activeSessions', JSON.stringify(updatedSessions))
  }

  function setPdfFiles(files) {
    console.log('Setting PDF files in store:', files);
    pdfFiles.value = files
  }

  function getCurrentPdf() {
    if (!pdfFiles.value.length) return null;
    return pdfFiles.value[currentPdfIndex.value];
  }

  function setCurrentPdfIndex(index) {
    if (index >= 0 && index < pdfFiles.value.length) {
      currentPdfIndex.value = index;
    }
  }




  function clearSession() {
    sessionToken.value = null
    customerId.value = null
    startTime.value = null
    lastActivity.value = null
    customerData.value = {
      id: null,
      name: null,
      plan: 'Standard Plan'
    }
    pdfFiles.value = []

    // Clear localStorage
    localStorage.removeItem('sessionToken')
    localStorage.removeItem('customerId')
    localStorage.removeItem('startTime')
    localStorage.removeItem('lastActivity')
    localStorage.removeItem('customerData')
  }

  function endSession() {
    // Remove from active sessions
    const sessions = JSON.parse(localStorage.getItem('activeSessions') || '[]')
    const updatedSessions = sessions.filter(s => s.id !== sessionToken.value)
    localStorage.setItem('activeSessions', JSON.stringify(updatedSessions))
    
    // Clear session
    clearSession()
  }

    // Get debug state function
    function getDebugState() {
      return {
        sessionToken: sessionToken.value,
        customerId: customerId.value,
        startTime: startTime.value,
        lastActivity: lastActivity.value,
        customerData: customerData.value,
        activeSessions: JSON.parse(localStorage.getItem('activeSessions') || '[]')
      }
    } 

  return {
    // State
    sessionToken,
    customerId,
    startTime,
    lastActivity,
    customerData,
    pdfFiles,  
    currentPdfIndex,
    getSessionToken,


    // Getters
    isActive,
    sessionDuration,

    // Actions
    getDebugState,
    initializeSession,
    updateLastActivity,
    setPdfFiles,
    getCurrentPdf,
    setCurrentPdfIndex,
    clearSession,
    endSession,
    getActiveSession,
    validateSession
    
  }
})
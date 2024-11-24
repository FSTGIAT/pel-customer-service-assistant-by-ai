<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { chatService } from '@/services/api'
import VuePdfEmbed from 'vue-pdf-embed'
import { useSessionStore } from '@/stores/sessionStore'

const headerSessionTime = ref('00:00');
const headerSessionStartTime = ref(new Date());
const headerTimerInterval = ref(null);

const startHeaderTimer = () => {
  // Clear any existing timer
  if (headerTimerInterval.value) {
    clearInterval(headerTimerInterval.value);
  }

  // Reset start time
  headerSessionStartTime.value = new Date();
  headerSessionTime.value = '00:00';

  // Start new timer
  headerTimerInterval.value = setInterval(() => {
    const now = new Date();
    const diff = Math.floor((now - headerSessionStartTime.value) / 1000);
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    headerSessionTime.value = `${mins}:${String(secs).padStart(2, '0')}`;
  }, 1000);
  return headerTimerInterval.value;
};


const updateSessionStorage = () => {
  const currentSession = {
    id: sessionStore.sessionToken,
    customerId: customerId.value,
    customerName: customerInfo.value?.name || 'Unknown',
    startTime: sessionStore.startTime || new Date().toISOString(),
    lastActivity: new Date().toISOString(),
    plan: customerInfo.value?.plan || 'Standard Plan'
  };

  try {
    const sessions = JSON.parse(localStorage.getItem('activeSessions') || '[]');
    const sessionIndex = sessions.findIndex(s => s.id === currentSession.id);
    
    if (sessionIndex >= 0) {
      sessions[sessionIndex] = currentSession;
    } else {
      sessions.push(currentSession);
    }
    
    localStorage.setItem('activeSessions', JSON.stringify(sessions));
    console.log('Updated sessions storage:', sessions);
  } catch (error) {
    console.error('Error updating session storage:', error);
  }
 }

// Session management
const sessionStore = useSessionStore()
const sessionError = ref(null)
const isSessionExpired = ref(false)
const reconnectAttempts = ref(0)
const MAX_RECONNECT_ATTEMPTS = 3
const lastActivityTime = ref(Date.now())
const SESSION_TIMEOUT = 5 * 60 * 1000 // 5 minutes

// Existing state (keeping your current state)
const messages = ref([])
const input = ref('')
const isLoading = ref(false)
const customerId = ref('3694388')
const customerInfo = ref(null)
const sessionTime = ref('0:00')
const error = ref(null)

// PDF state (keeping your current PDF state)
const pdfFiles = ref([])
const currentPdfIndex = ref(0)
const isLoadingPdf = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const scale = ref(1)
const pdfLoaded = ref(false)

// Your existing computed PDF URL
const currentPdfUrl = computed(() => {
  const currentPdf = pdfFiles.value[currentPdfIndex.value];
  if (!currentPdf) return null;
  
  // Only load if it's the current PDF
  if (!currentPdf.loaded) {
    console.log('Loading PDF:', currentPdf.url);
    currentPdf.loaded = true;
  }
  
  return currentPdf.fullUrl;
});

const loadPdfMetadata = async (pdf) => {
  if (pdf.loaded || pdf.loading) return;
  
  try {
    pdf.loading = true;
    const info = await chatService.getPdfInfo(customerId.value, pdf.name);
    pdf.totalPages = info.pages || 1;
    pdf.loaded = true;
    pdf.loading = false;
  } catch (error) {
    console.error('Error loading PDF metadata:', error);
    pdf.error = error.message;
    pdf.loading = false;
  }
};


const isSessionValid = computed(() => {
  return sessionStore.validateSession();
});

// Add watcher for session validity
watch(isSessionValid, (valid) => {
  if (!valid) {
    handleSessionExpiration();
  }
});

// Enhanced initialize chat with session handling
// Update only the part where we set customerInfo in your existing initializeChat method

// Add this new method for async customer info loading
const loadCustomerInfo = async (pdfFile) => {
  try {
    const infoQuery = `מתוך החשבונית, אנא ספק את:
1. שם הלקוח המלא
2. תכנית/מסלול החבילה
השב בפורמט JSON בלבד עם השדות name ו-plan.`;

    // Create properly formatted context
    const context = [
      {
        type: 'system',
        content: 'Analyzing customer bill'
      }
    ];

    console.log('Requesting customer info with PDF:', pdfFile);
    
    const response = await chatService.sendMessage(
      infoQuery,
      customerId.value,
      context,
      pdfFile.path
    );

    console.log('Customer info response:', response);

    if (response && response.response) {
      try {
        const extractedInfo = JSON.parse(response.response);
        customerInfo.value = {
          id: customerId.value,
          name: extractedInfo.name || 'לא זוהה',
          plan: extractedInfo.plan || 'לא זוהה'
        };
      } catch (parseError) {
        console.error('Error parsing customer info:', parseError);
        throw new Error('Error parsing customer data');
      }
    } else {
      throw new Error('Invalid response format');
    }

  } catch (error) {
    console.error('Error getting customer info:', error);
    customerInfo.value = {
      id: customerId.value,
      name: 'לא זוהה',
      plan: 'לא זוהה'
    };
  }
};

// Modified initializeChat method
const initializeChat = async () => {
  try {
    isLoading.value = true;
    isLoadingPdf.value = true;

    // Initialize messages early for better UX
    messages.value = [
      {
        type: 'system',
        content: 'מחובר למערכת שירות לקוחות פלאפון'
      },
      {
        type: 'bot',
        content: 'שלום! אני בודק את חשבון החיוב שלך. כיצד אוכל לעזור?'
      }
    ];

    // Set initial customer info state
    customerInfo.value = {
      id: customerId.value,
      name: 'טוען...',
      plan: 'טוען...'
    };

    // Get PDFs using chatService
    const response = await chatService.getPdfList(customerId.value);
    console.log('Raw PDF response:', response);

    if (response?.pdf_files?.length) {
      const processedPdfs = response.pdf_files.map(pdf => ({
        ...pdf,
        totalPages: pdf.pages || 1,
        fullUrl: `http://127.0.0.1:8000${pdf.url}`,
        loaded: false,
        loading: false,
        error: null
      }));

      console.log('Processed PDFs:', processedPdfs);
      
      pdfFiles.value = processedPdfs;
      
      if (processedPdfs.length > 0) {
        const firstPdf = processedPdfs[0];
        firstPdf.loading = true;

        // Set initial PDF state immediately
        totalPages.value = firstPdf.totalPages;
        currentPage.value = 1;
        scale.value = 1;

        console.log('Initial PDF setup:', firstPdf);

        // Start customer info loading in background
        loadCustomerInfo(firstPdf)
          .catch(error => {
            console.warn('Customer info loading error:', error);
            // Error already sets fallback values in loadCustomerInfo
          })
          .finally(() => {
            // Mark PDF as loaded regardless of customer info success
            firstPdf.loaded = true;
            firstPdf.loading = false;
          });

        // Don't wait for customer info - mark PDF as ready
        firstPdf.loaded = true;
        firstPdf.loading = false;
      }
    } else {
      console.warn('Invalid PDF response structure:', response);
      throw new Error('Invalid PDF response structure');
    }
  } catch (err) {
    console.error('Initialization error:', err);
    error.value = 'שגיאה בטעינת המסמכים. חלק מהתכונות עשויות שלא לעבוד.';
  } finally {
    isLoading.value = false;
    isLoadingPdf.value = false;
  }
};


const extractCustomerInfo = async (pdfText) => {
  try {
    const infoQuery = `אנא חלץ את הפרטים הבאים מהחשבונית:
1. שם הלקוח המלא
2. תכנית/מסלול החבילה
השב בפורמט JSON בלבד עם השדות name ו-plan.
דוגמה לפורמט הרצוי:
{
  "name": "שם הלקוח",
  "plan": "שם התכנית"
}`

    const response = await chatService.sendMessage(
      infoQuery,
      customerId.value,
      [],
      pdfText,
      await sessionStore.getSessionToken()
    );

    try {
      const parsedInfo = JSON.parse(response.response);
      return parsedInfo;
    } catch (parseError) {
      console.error('Error parsing customer info:', parseError);
      return null;
    }
  } catch (error) {
    console.error('Error extracting customer info:', error);
    return null;
  }
};

// Enhanced error handling
const handleError = (err) => {
  console.error('Error:', err);
  
  if (err.response?.status === 401) {
    sessionError.value = 'פג תוקף החיבור למערכת. מתחבר מחדש...'
    handleSessionExpiration();
  } else if (err.response?.status === 429) {
    error.value = 'נא להמתין מספר דקות ולנסות שוב'
  } else {
    error.value = err.message || 'Failed to initialize chat. Please try again.';
  }
};

// Session management methods
const handleSessionExpiration = async () => {
  isSessionExpired.value = true;
  
  if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
    reconnectAttempts.value++;
    try {
      await sessionStore.refreshSession();
      isSessionExpired.value = false;
      sessionError.value = null;
      reconnectAttempts.value = 0;
    } catch (err) {
      console.error('Session refresh failed:', err);
      sessionError.value = 'החיבור למערכת נכשל. מנסה שוב...'
    }
  } else {
    sessionError.value = 'לא ניתן להתחבר למערכת. נא לטעון את הדף מחדש'
  }
};

const startSessionMonitoring = () => {
  setInterval(() => {
    const timeSinceLastActivity = Date.now() - lastActivityTime.value;
    if (timeSinceLastActivity > SESSION_TIMEOUT) {
      handleSessionExpiration();
    }
  }, 30000); // Check every 30 seconds
};

const updateActivity = () => {
  lastActivityTime.value = Date.now();
  sessionStore.updateLastActivity();
};

// Enhanced message sending with session handling
const sendMessage = async () => {
  if (!input.value.trim() || isLoading.value) return;
  
  const messageText = input.value;
  input.value = ''; // Clear input immediately


  

  // Add user message
  messages.value.push({
    type: 'user',
    content: messageText
  });

  try {
    isLoading.value = true;

    // Get current PDF context
    const currentPdf = pdfFiles.value[currentPdfIndex.value];
    const pdfPath = currentPdf?.path || null;

    // Format context properly
    const recentContext = messages.value
      .slice(-5)
      .map(msg => ({
        type: msg.type,
        content: msg.content
      }));

    console.log('Sending to API with context:', {
      messageText,
      customerId: customerId.value,
      pdfPath,
      contextLength: recentContext.length
    });

    const response = await chatService.sendMessage(
      messageText,
      customerId.value,
      recentContext,
      pdfPath
    );



    

    console.log('Received response:', response);

    if (response && response.response) {
      messages.value.push({
        type: 'bot',
        content: response.response
      });
    } else {
      throw new Error('Invalid response format');
    }

    // Update session activity
    sessionStore.updateLastActivity();
    updateSessionStorage();

  } catch (err) {
    console.error('Chat error:', err);
    messages.value.push({
      type: 'system',
      content: 'אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב.'
    });
  } finally {
    isLoading.value = false;
  }
};

// Enhanced session timer with auto-refresh
const startSessionTimer = () => {
  setInterval(() => {
    if (sessionStore.isActive) {
      const duration = sessionStore.sessionDuration;
      sessionTime.value = duration;
      sessionStore.updateLastActivity();
    }
  }, 1000);
};

// Cleanup
onUnmounted(() => {
  if (headerTimerInterval.value) {
    clearInterval(headerTimerInterval.value);
  }
  sessionStore.cleanup();
});

// Initialize
onMounted(async () => {
  await initializeChat();
  startHeaderTimer();
  updateSessionStorage();
  
  // Log initial session state
  console.log('Initial session state:', sessionStore.getDebugState());
});


// Watch for session errors
watch(() => sessionStore.sessionError, (newError) => {
  if (newError) {
    sessionError.value = newError;
  }
});

watch(() => sessionStore.isActive, (active) => {
  console.log('Session active state changed:', active);
  if (!active) {
    console.warn('Session is not active');
  }
});

// Keeping your existing PDF control methods
const onPdfRendered = async (e) => {
  console.log('PDF rendered event:', e);
  if (e.pdf) {
    const numPages = e.pdf.numPages;
    console.log(`PDF rendered successfully with ${numPages} pages`);
    totalPages.value = numPages;
    
    // Update PDF metadata in store
    const currentPdfsCopy = [...pdfFiles.value];
    if (currentPdfsCopy[currentPdfIndex.value]) {
      currentPdfsCopy[currentPdfIndex.value].totalPages = numPages;
      sessionStore.setPdfFiles(currentPdfsCopy);
    }
  }
};

watch(error, (newError) => {
  if (newError) {
    console.error('PDF Error occurred:', newError);
  }
});

// Keeping your existing PDF navigation methods
const navigatePdf = async (direction) => {
  const newIndex = currentPdfIndex.value + direction;
  if (newIndex >= 0 && newIndex < pdfFiles.value.length) {
    currentPdfIndex.value = newIndex;
    currentPage.value = 1;
    
    const nextPdf = pdfFiles.value[newIndex];
    if (!nextPdf.loaded) {
      isLoadingPdf.value = true;
      await loadPdfMetadata(nextPdf);
      isLoadingPdf.value = false;
    }
    
    totalPages.value = nextPdf.totalPages || 1;
    console.log(`Switched to PDF ${newIndex} with ${totalPages.value} pages`);
  }
};

// Keeping your existing zoom controls
const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.1, 2);
};

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.1, 0.5);
};

// Keeping your existing page navigation
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
};

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
};
</script>

<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Session Error Alert -->
    <div 
      v-if="sessionError" 
      class="absolute top-0 left-0 right-0 z-50 bg-red-50 p-4 text-red-700 text-center"
    >
      {{ sessionError }}
    </div>

    <!-- Left Panel - PDF Viewer -->
    <div class="w-1/2 p-4 bg-white border-r border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold">Customer Bill</h2>
        
        <!-- PDF Controls -->
        <div class="flex items-center space-x-4">
          <!-- Bill Navigation -->
          <div class="flex items-center space-x-2">
            <button 
              @click="() => navigatePdf(-1)"
              :disabled="currentPdfIndex === 0"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <span class="text-sm text-gray-600" v-if="pdfFiles.length">
              Bill {{ currentPdfIndex + 1 }} of {{ pdfFiles.length }} 
              ({{ totalPages }} pages)
            </span>
            <button 
              @click="() => navigatePdf(1)"
              :disabled="currentPdfIndex === pdfFiles.length - 1"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>

          <!-- Page Navigation -->
          <div class="flex items-center space-x-2">
            <button 
              @click="previousPage"
              :disabled="currentPage <= 1"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              <i class="fas fa-arrow-left"></i>
            </button>
            <span class="text-sm text-gray-600">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button 
              @click="nextPage"
              :disabled="currentPage >= totalPages"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              <i class="fas fa-arrow-right"></i>
            </button>
          </div>

          <!-- Zoom Controls -->
          <div class="flex items-center space-x-2">
            <button 
              @click="zoomOut"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded"
            >
              <i class="fas fa-search-minus"></i>
            </button>
            <span class="text-sm text-gray-600">{{ Math.round(scale * 100) }}%</span>
            <button 
              @click="zoomIn"
              class="px-2 py-1 text-gray-600 hover:bg-gray-100 rounded"
            >
              <i class="fas fa-search-plus"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- PDF Display -->
      <div class="h-[calc(100vh-8rem)] rounded-lg overflow-auto bg-gray-50">
        <div v-if="isLoadingPdf" class="flex items-center justify-center h-full">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
        
        <div v-else-if="currentPdfUrl" class="relative">
          <VuePdfEmbed
            :source="currentPdfUrl"
            :page="currentPage"
            @rendered="onPdfRendered"
            @error="(error) => {
            console.error('PDF Error:', error);
            error = 'Error loading PDF document';
          }"
            :style="{
              transform: `scale(${scale})`,
              transformOrigin: 'top left'
            }"
            
          />
        </div>
        
        <div v-else class="flex items-center justify-center h-full">
          <div class="text-center">
            <i class="fas fa-file-text text-4xl text-gray-400 mb-2"></i>
            <p class="text-gray-500">{{ error || 'No billing document available' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel - Chat Interface -->
    <div class="w-1/2 flex flex-col">
      <!-- Customer Info Header -->
      <div class="bg-white p-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold">
              Customer #{{ customerInfo?.id || customerId }}
            </h2>
      <p class="text-sm text-gray-500">
        <span v-if="customerInfo?.name">
          {{ customerInfo.name }} • {{ customerInfo.plan || 'Standard Plan' }}
        </span>
        <span v-else>Loading...</span>
      </p>
          </div>
          <div class="flex items-center space-x-2 text-sm text-gray-500">
            <i class="fas fa-clock w-4 h-4"></i>
            <span>Session: {{ sessionTime }}</span>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="bg-red-50 p-4 border-b border-red-100">
        <p class="text-red-600 text-sm">{{ error }}</p>
      </div>

      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-for="(message, index) in messages"
             :key="index"
             :class="['flex', message.type === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['flex items-start space-x-2 max-w-[80%]',
                       message.type === 'system' ? 'justify-center w-full' : '']">
            <div v-if="message.type === 'bot'"
                 class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <i class="fas fa-robot w-5 h-5 text-blue-600"></i>
            </div>
            <div :class="['p-3 rounded-lg',
                         message.type === 'user' ? 'bg-blue-600 text-white' :
                         message.type === 'bot' ? 'bg-gray-100 text-gray-800' :
                         'bg-gray-100 text-gray-500 text-sm w-full text-center']">
              {{ message.content }}
            </div>
            <div v-if="message.type === 'user'"
                 class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <i class="fas fa-user w-5 h-5 text-gray-600"></i>
            </div>
          </div>
        </div>

        <!-- Loading Indicator -->
        <div v-if="isLoading" class="flex justify-center">
          <div class="animate-pulse text-gray-400">
            AI is thinking...
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 bg-white border-t border-gray-200">
        <div class="flex items-center space-x-2">
          <input
            v-model="input"
            type="text"
            placeholder="Type your message..."
            class="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          />
          <button
            @click="sendMessage"
            class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none disabled:opacity-50"
            :disabled="isLoading || !input.trim()"
          >
            <i class="fas fa-paper-plane w-5 h-5"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transform-origin-top-left {
  transform-origin: top left;
}

.vue-pdf-embed {
  transition: transform 0.2s ease-in-out;
}
</style>
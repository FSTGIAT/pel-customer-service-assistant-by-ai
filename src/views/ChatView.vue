<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { chatService } from '@/services/api'
import VuePdfEmbed from 'vue-pdf-embed'
import { useSessionStore } from '@/stores/session'

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
const customerId = ref('3694388_07012024')
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
  if (!pdfFiles.value.length) {
    console.log('No PDFs available');
    return null;
  }
  
  const currentPdf = pdfFiles.value[currentPdfIndex.value];
  const url = `http://127.0.0.1:8000${currentPdf.url}`;
  console.log('Current PDF URL:', url);
  return url;
});

// Enhanced initialize chat with session handling
const initializeChat = async () => {
  try {
    isLoading.value = true;
    isLoadingPdf.value = true;
    console.log('Starting chat initialization...')
    console.log('Using customer ID:', customerId.value)

    // Initialize session first
    await sessionStore.initializeSession(customerId.value)

    // Load PDFs with session token
    const pdfResponse = await chatService.getPdfList(
      customerId.value, 
      await sessionStore.getSessionToken()
    );
    
    console.log('Raw PDF response:', pdfResponse);

    if (pdfResponse && pdfResponse.pdf_files && Array.isArray(pdfResponse.pdf_files)) {
      if (pdfResponse.pdf_files.length === 0) {
        console.warn('No PDFs available for customer:', customerId.value)
        error.value = 'No billing documents available'
      } else {
        pdfFiles.value = pdfResponse.pdf_files
        
        // Set initial total pages if there are PDFs
        if (pdfFiles.value.length > 0) {
          const firstPdf = pdfFiles.value[0]
          totalPages.value = firstPdf.pages || 1
          console.log('Initial PDF loaded:', firstPdf)
          console.log('Total pages:', totalPages.value)
        }
        console.log('Processed PDF files:', pdfFiles.value)
      }
    } else {
      console.warn('Invalid PDF response structure:', pdfResponse)
      throw new Error('Invalid PDF response structure')
    }

    // Set customer info from session
    customerInfo.value = {
      id: customerId.value,
      name: await sessionStore.getCustomerName(),
      plan: await sessionStore.getCustomerPlan()
    };

    // Add initial messages
    messages.value = [
      {
        type: 'system',
        content: 'מחובר למערכת שירות לקוחות פלאפון'
      },
      {
        type: 'bot',
        content: `שלום! אני בודק את חשבון החיוב שלך. כיצד אוכל לעזור?`
      }
    ];

    startSessionMonitoring();
  } catch (err) {
    console.error('Initialization error:', err)
    handleError(err);  // Changed from error.value assignment to using handleError
  } finally {
    isLoading.value = false;
    isLoadingPdf.value = false;
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
  
  updateActivity();
  const messageText = input.value;
  input.value = '';

  messages.value.push({
    type: 'user',
    content: messageText
  });

  try {
    isLoading.value = true;
    
    const currentPdf = pdfFiles.value[currentPdfIndex.value];
    const response = await chatService.sendMessage(
      messageText,
      customerId.value,
      messages.value.slice(-5),
      currentPdf?.path,
      await sessionStore.getSessionToken()
    );

    messages.value.push({
      type: 'bot',
      content: response.response
    });
  } catch (err) {
    console.error('Chat error:', err);
    messages.value.push({
      type: 'system',
      content: 'Sorry, I encountered an error. Please try again.'
    });
  } finally {
    isLoading.value = false;
  }
};

// Enhanced session timer with auto-refresh
const startSessionTimer = () => {
  let seconds = 0;
  setInterval(() => {
    seconds++;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    sessionTime.value = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    
    // Refresh session if needed
    if (minutes > 0 && minutes % 4 === 0 && remainingSeconds === 0) {
      sessionStore.refreshSession();
    }
  }, 1000);
};

// Cleanup
onUnmounted(() => {
  sessionStore.cleanup();
});

// Initialize
onMounted(() => {
  initializeChat();
  startSessionTimer();
});

// Watch for session errors
watch(() => sessionStore.sessionError, (newError) => {
  if (newError) {
    sessionError.value = newError;
  }
});

// Keeping your existing PDF control methods
const onPdfRendered = async (e) => {
  if (e.pdf) {
    const numPages = e.pdf.numPages;
    totalPages.value = numPages;
    if (pdfFiles.value[currentPdfIndex.value]) {
      pdfFiles.value[currentPdfIndex.value].totalPages = numPages;
    }
    console.log(`PDF rendered with ${numPages} pages`);
  }
};

// Keeping your existing PDF navigation methods
const navigatePdf = async (direction) => {
  const newIndex = currentPdfIndex.value + direction;
  if (newIndex >= 0 && newIndex < pdfFiles.value.length) {
    currentPdfIndex.value = newIndex;
    currentPage.value = 1;
    totalPages.value = pdfFiles.value[newIndex].totalPages || 1;
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
            @error="error => console.error('PDF Error:', error)"
            :style="{
              transform: `scale(${scale})`,
              transformOrigin: 'top left'
            }"
          />
        </div>
        
        <div v-else class="flex items-center justify-center h-full">
          <i class="fas fa-file-text w-16 h-16 text-gray-400"></i>
          <p class="text-gray-500 ml-2">No billing document available</p>
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
              {{ customerInfo?.name || 'Loading...' }} •
              {{ customerInfo?.plan || 'Standard Plan' }}
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
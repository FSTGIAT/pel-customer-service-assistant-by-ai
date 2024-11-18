import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

const apiClient = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// Response interceptor for better error handling
apiClient.interceptors.response.use(
    response => response.data,
    error => {
        if (error.response) {
            console.error('Response error:', {
                data: error.response.data,
                status: error.response.status,
                headers: error.response.headers
            });
        } else if (error.request) {
            console.error('Request error:', error.request);
        } else {
            console.error('Error:', error.message);
        }
        throw error;
    }
);

export const chatService = {
    async getPdfList(customerId) {
        try {
            console.log('Fetching PDFs for customer:', customerId);
            const response = await apiClient.post('/legacy/trigger', {
                customer_id: customerId
            });
            console.log('PDF Response:', response); // Note: response is already response.data due to interceptor
            
            // Validate response structure
            if (response && response.pdf_files && Array.isArray(response.pdf_files)) {
                // Map additional metadata if needed
                const enhancedPdfs = response.pdf_files.map(pdf => ({
                    ...pdf,
                    totalPages: pdf.pages || 1,
                    fullUrl: `http://127.0.0.1:8000${pdf.url}`
                }));
                
                return {
                    ...response,
                    pdf_files: enhancedPdfs
                };
            } else {
                throw new Error('Invalid PDF response structure');
            }
        } catch (error) {
            console.error('Error fetching PDFs:', error);
            throw error;
        }
    },

    async sendMessage(message, customerId, context, pdfPath = null) {
        try {
            const response = await apiClient.post('/chat', {
                message,
                customerId,
                context,
                pdf_path: pdfPath
            });
            return response; // Already transformed by interceptor
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },

    async getPdfInfo(customerId, filename) {
        try {
            const response = await apiClient.get(`/pdf/info/${customerId}/${filename}`);
            return response; // Already transformed by interceptor
        } catch (error) {
            console.error('Error getting PDF info:', error);
            return null;
        }
    },

    async getPdfText(filename, page = null) {
        try {
            const url = `/pdf/text/${filename}${page ? `?page=${page}` : ''}`;
            const response = await apiClient.get(url);
            return response; // Already transformed by interceptor
        } catch (error) {
            console.error('Error getting PDF text:', error);
            throw error;
        }
    },

    // New helper methods
    async getCurrentPdfContent(customerId, filename) {
        try {
            const text = await this.getPdfText(filename);
            return text?.content || '';
        } catch (error) {
            console.error('Error getting PDF content:', error);
            return '';
        }
    },

    async getPdfPages(customerId, filename) {
        try {
            const info = await this.getPdfInfo(customerId, filename);
            return info?.pages || 1;
        } catch (error) {
            console.error('Error getting PDF pages:', error);
            return 1;
        }
    },

    // Utility method to check if a response is valid
    isValidResponse(response) {
        return response && typeof response === 'object' && !response.error;
    }
};

// For debugging purposes in development
if (process.env.NODE_ENV === 'development') {
    window.chatService = chatService;
    window.apiClient = apiClient;
}
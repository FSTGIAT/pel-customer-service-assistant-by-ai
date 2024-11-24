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
            // Change from '/api/legacy/trigger' to '/legacy/trigger'
            const response = await apiClient.post('/legacy/trigger', {  // CHANGED THIS LINE
                customer_id: customerId
            }, {
                // Add timeout specifically for PDF loading
                timeout: 60000, // 60 seconds for PDF loading
            });
            
            console.log('PDF Response:', response);
            
            if (response && response.pdf_files && Array.isArray(response.pdf_files)) {
                const enhancedPdfs = response.pdf_files.map(pdf => ({
                    ...pdf,
                    totalPages: pdf.pages || 1,
                    fullUrl: `${API_URL}${pdf.url}`
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
            console.log('Sending message to API:', {
                message,
                customerId,
                contextLength: context?.length,
                hasPdfPath: !!pdfPath
            });

            // Format the request body according to your FastAPI model
            const requestBody = {
                message: message,
                customerId: customerId,  // Make sure this matches your Pydantic model
                context: context ? context.map(msg => ({
                    type: msg.type,
                    content: msg.content
                })) : [],
                pdf_path: pdfPath || null
            };

            console.log('Request body:', requestBody);  // Debug log

            const response = await apiClient.post('/chat', requestBody);

            console.log('API Response:', response);
            
            if (response && response.response) {
                return response;
            } else {
                throw new Error('Invalid API response format');
            }
        } catch (error) {
            console.error('Error in sendMessage:', {
                error,
                requestData: error.config?.data,
                response: error.response?.data
            });
            throw error;
        }
    },

    // Also update these methods if you're using them
    async getPdfInfo(customerId, filename) {
        try {
            // Change from '/api/pdf/info' to '/pdf/info'
            const response = await apiClient.get(`/pdf/info/${customerId}/${filename}`);  // CHANGED THIS LINE
            return response;
        } catch (error) {
            console.error('Error getting PDF info:', error);
            return null;
        }
    },

    async getPdfText(filename, page = null) {
        try {
            // Change from '/api/pdf/text' to '/pdf/text'
            const url = `/pdf/text/${filename}${page ? `?page=${page}` : ''}`;  // CHANGED THIS LINE
            const response = await apiClient.get(url);
            return response;
        } catch (error) {
            console.error('Error getting PDF text:', error);
            throw error;
        }
    }
};


// For debugging purposes in development
if (process.env.NODE_ENV === 'development') {
    window.chatService = chatService;
    window.apiClient = apiClient;
}
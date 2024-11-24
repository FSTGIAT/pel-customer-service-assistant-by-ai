// tests/mocks/api.js
export const mockPdfResponse = {
  status: "success",
  customer_id: "3694388",
  pdf_files: [
    {
      path: "/root/telecom-customer-service/pdf-test/3694388_07012024.pdf",
      name: "3694388_07012024.pdf",
      url: "/api/pdf/view/3694388_07012024.pdf",
      pages: 3,
      date: "2024-01-07T00:00:00"
    }
  ]
};

export const mockChatService = {
  getPdfList: vi.fn().mockResolvedValue(mockPdfResponse),
  sendMessage: vi.fn().mockResolvedValue({ 
    response: "איך אוכל לעזור?" 
  }),
  getPdfInfo: vi.fn().mockResolvedValue({
    pages: 3,
    text_sample: "Sample text"
  }),
  getPdfText: vi.fn().mockResolvedValue({
    content: "Sample PDF content"
  })
};
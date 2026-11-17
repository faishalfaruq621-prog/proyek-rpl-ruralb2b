import axiosInstance from './axios'

export const aiService = {
  chatStandard: (messages) =>
    axiosInstance.post('/ai/chat/standard', { messages }),
  chatPlus: (messages, businessContext) =>
    axiosInstance.post('/ai/chat/plus', { messages, business_context: businessContext }),
  recommendations: (data) =>
    axiosInstance.post('/ai/recommendations', data),
  recommendationsByCategory: (categoryId, params) =>
    axiosInstance.get(`/ai/recommendations/category/${categoryId}`, { params }),
  businessSummary: () => axiosInstance.get('/ai/insights/summary'),
  businessTransactions: () => axiosInstance.get('/ai/insights/transactions'),
  businessProducts: () => axiosInstance.get('/ai/insights/products'),
  businessAnalysis: () => axiosInstance.post('/ai/insights/analyze'),
  status: () => axiosInstance.get('/ai/status'),
}

import axiosInstance from './axios'

export const authService = {
  register: (data) => axiosInstance.post('/auth/register', data),
  login: (data) => axiosInstance.post('/auth/login', data),
  logout: () => axiosInstance.post('/auth/logout'),
  me: () => axiosInstance.get('/auth/me'),
  changePassword: (data) => axiosInstance.post('/auth/change-password', data),
}

export const businessProfileService = {
  getProfile: () => axiosInstance.get('/business/profile'),
  updateProfile: (data) => axiosInstance.patch('/business/profile', data),
  submitVerification: (data) => axiosInstance.post('/business/verifications', data),
  getVerifications: (params) => axiosInstance.get('/business/verifications', { params }),
  getVerificationDetail: (id) => axiosInstance.get('/business/verifications/' + id),
  uploadDocument: (verificationId, formData) =>
    axiosInstance.post('/business/verifications/' + verificationId + '/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

export const productService = {
  getProducts: (params) => axiosInstance.get('/products', { params }),
  getCategories: (params) => axiosInstance.get('/categories', { params }),
  getProduct: (id) => axiosInstance.get('/products/' + id),
  createProduct: (data) => axiosInstance.post('/products', data),
  updateProduct: (id, data) => axiosInstance.patch('/products/' + id, data),
  deleteProduct: (id) => axiosInstance.delete('/products/' + id),
  uploadImage: (productId, formData) =>
    axiosInstance.post('/products/' + productId + '/images', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteImage: (productId, imageId) =>
    axiosInstance.delete('/products/' + productId + '/images/' + imageId),
  getMyProducts: (params) => axiosInstance.get('/business/products', { params }),
  getMyProduct: (id) => axiosInstance.get('/business/products/' + id),
  getInventory: () => axiosInstance.get('/business/inventory'),
  updateInventory: (productId, data) =>
    axiosInstance.patch('/business/inventory/' + productId, data),
}

export const adminService = {
  getVerifications: (params) => axiosInstance.get('/admin/verifications', { params }),
  getVerificationDetail: (id) => axiosInstance.get('/admin/verifications/' + id),
  approveVerification: (id, data) =>
    axiosInstance.post('/admin/verifications/' + id + '/approve', data),
  rejectVerification: (id, data) =>
    axiosInstance.post('/admin/verifications/' + id + '/reject', data),
  getVerificationLogs: (id) =>
    axiosInstance.get('/admin/verifications/' + id + '/logs'),
  getStats: () => axiosInstance.get('/admin/stats'),
  getUsers: (params) => axiosInstance.get('/admin/users', { params }),
  updateUser: (id, data) => axiosInstance.patch('/admin/users/' + id, data),
  getCategories: (params) => axiosInstance.get('/admin/categories', { params }),
  createCategory: (data) => axiosInstance.post('/admin/categories', data),
  updateCategory: (id, data) => axiosInstance.patch('/admin/categories/' + id, data),
  deleteCategory: (id) => axiosInstance.delete('/admin/categories/' + id),
  getOrders: (params) => axiosInstance.get('/admin/orders', { params }),
  // Integrasi Telegram (hanya admin; token tidak pernah dikembalikan backend)
  getTelegramStatus: () => axiosInstance.get('/admin/telegram/status'),
  testTelegramConnection: () => axiosInstance.post('/admin/telegram/test-connection'),
  sendTelegramTestMessage: () => axiosInstance.post('/admin/telegram/send-test-message'),
  getTelegramLogs: (params) => axiosInstance.get('/admin/telegram/logs', { params }),
}

export const notificationService = {
  getNotifications: (params) => axiosInstance.get('/notifications', { params }),
  getUnreadCount: () => axiosInstance.get('/notifications/unread-count'),
  markRead: (ids) => axiosInstance.patch('/notifications/read', { ids }),
  markAllRead: () => axiosInstance.post('/notifications/read-all'),
}

export const chatService = {
  startConversation: (data) => axiosInstance.post('/chat/conversations', data),
  getConversations: (params) => axiosInstance.get('/chat/conversations', { params }),
  getConversation: (id) => axiosInstance.get('/chat/conversations/' + id),
  getMessages: (id, params) =>
    axiosInstance.get('/chat/conversations/' + id + '/messages', { params }),
  sendMessage: (id, data) =>
    axiosInstance.post('/chat/conversations/' + id + '/messages', data),
}

export const cartService = {
  getCart: () => axiosInstance.get('/cart'),
  addItem: (data) => axiosInstance.post('/cart/items', data),
  updateItem: (itemId, data) => axiosInstance.patch('/cart/items/' + itemId, data),
  deleteItem: (itemId) => axiosInstance.delete('/cart/items/' + itemId),
}

export const orderService = {
  checkout: (data) => axiosInstance.post('/orders/checkout', data),
  getMyOrders: (params) => axiosInstance.get('/orders', { params }),
  getMyOrder: (id) => axiosInstance.get('/orders/' + id),
  cancelOrder: (id, data) => axiosInstance.post('/orders/' + id + '/cancel', data),
  getMyPayment: (id) => axiosInstance.get('/orders/' + id + '/payment'),
  submitPayment: (id, data) => axiosInstance.patch('/orders/' + id + '/payment', data),
  uploadProof: (id, formData) =>
    axiosInstance.post('/orders/' + id + '/payment/proof', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  downloadProof: (id) =>
    axiosInstance.get('/orders/' + id + '/payment/proof/download', {
      responseType: 'blob',
    }),
  getSellerOrders: (params) => axiosInstance.get('/seller/orders', { params }),
  getSellerOrder: (id) => axiosInstance.get('/seller/orders/' + id),
  updateOrderStatus: (id, data) =>
    axiosInstance.patch('/seller/orders/' + id + '/status', data),
  confirmPayment: (id, data) =>
    axiosInstance.post('/seller/orders/' + id + '/payment/confirm', data),
  downloadSellerProof: (id) =>
    axiosInstance.get('/seller/orders/' + id + '/payment/proof/download', {
      responseType: 'blob',
    }),
  receiveOrder: (id) => axiosInstance.post('/orders/' + id + '/receive'),
}

export const healthService = {
  check: () => axiosInstance.get('/health'),
}

import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboard = () => api.get('/dashboard').then(r => r.data)
export const getSuppliers = () => api.get('/suppliers').then(r => r.data)
export const getSupplier = (id) => api.get(`/suppliers/${id}`).then(r => r.data)

export const getPRs = () => api.get('/purchase-requests').then(r => r.data)
export const getPR = (id) => api.get(`/purchase-requests/${id}`).then(r => r.data)
export const createPR = (body) => api.post('/purchase-requests', body).then(r => r.data)
export const approvePR = (id) => api.patch(`/purchase-requests/${id}/approve`).then(r => r.data)
export const rejectPR = (id) => api.patch(`/purchase-requests/${id}/reject`).then(r => r.data)

export const getPOs = () => api.get('/purchase-orders').then(r => r.data)
export const getPO = (id) => api.get(`/purchase-orders/${id}`).then(r => r.data)

export const getInvoices = (status) => api.get('/invoices', { params: status ? { status } : {} }).then(r => r.data)
export const getInvoice = (id) => api.get(`/invoices/${id}`).then(r => r.data)
export const approveInvoice = (id) => api.patch(`/invoices/${id}/approve`).then(r => r.data)
export const rejectInvoice = (id) => api.patch(`/invoices/${id}/reject`).then(r => r.data)
export const processInvoice = (id) => api.post(`/invoices/${id}/simulate-processing`).then(r => r.data)

export const getGSTCache = () => api.get('/gst-cache').then(r => r.data)
export const syncGST = () => api.post('/gst-cache/sync').then(r => r.data)

export const getMSME = () => api.get('/msme-compliance').then(r => r.data)
export const getEBSEvents = () => api.get('/oracle-ebs/events').then(r => r.data)
export const retryEBSEvent = (id) => api.post(`/oracle-ebs/events/${id}/retry`).then(r => r.data)

export const getAIInsights = () => api.get('/ai-agents/insights').then(r => r.data)
export const applyAIInsight = (id) => api.post(`/ai-agents/insights/${id}/apply`).then(r => r.data)

export const getVendorEvents = () => api.get('/vendor-portal/events').then(r => r.data)
export const getSpendAnalytics = () => api.get('/analytics/spend').then(r => r.data)
export const getBudgets = () => api.get('/budgets').then(r => r.data)
export const checkBudget = (dept, amount) => api.post('/budgets/check', null, { params: { dept, amount } }).then(r => r.data)

export default api

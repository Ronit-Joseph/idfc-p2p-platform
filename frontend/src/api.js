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

// Workflow / Approvals
export const getApprovalMatrices = () => api.get('/workflow/matrices').then(r => r.data)
export const getPendingApprovals = (role) => api.get('/workflow/pending', { params: role ? { approver_role: role } : {} }).then(r => r.data)
export const getApprovalInstance = (id) => api.get(`/workflow/approvals/${id}`).then(r => r.data)
export const createApprovalRequest = (body) => api.post('/workflow/request', body).then(r => r.data)
export const approveStep = (instanceId, body) => api.post(`/workflow/approvals/${instanceId}/approve`, body).then(r => r.data)
export const rejectStep = (instanceId, body) => api.post(`/workflow/approvals/${instanceId}/reject`, body).then(r => r.data)

// Audit
export const getAuditLogs = (params) => api.get('/audit', { params }).then(r => r.data)
export const getAuditSummary = () => api.get('/audit/summary').then(r => r.data)
export const getEntityHistory = (entityType, entityId) => api.get(`/audit/entity/${entityType}/${entityId}`).then(r => r.data)

// Notifications
export const getNotifications = (params) => api.get('/notifications', { params }).then(r => r.data)
export const getUnreadCount = () => api.get('/notifications/unread-count').then(r => r.data)
export const markNotificationRead = (id) => api.patch(`/notifications/${id}/read`).then(r => r.data)
export const markAllNotificationsRead = () => api.post('/notifications/mark-all-read').then(r => r.data)

// Matching
export const getMatchResults = () => api.get('/matching/results').then(r => r.data)
export const getMatchSummary = () => api.get('/matching/summary').then(r => r.data)
export const runMatch = (body) => api.post('/matching/run', body).then(r => r.data)
export const getMatchExceptions = () => api.get('/matching/exceptions').then(r => r.data)
export const resolveMatchException = (id, body) => api.post(`/matching/exceptions/${id}/resolve`, body).then(r => r.data)

// Payments
export const getPayments = () => api.get('/payments').then(r => r.data)
export const getPaymentSummary = () => api.get('/payments/summary').then(r => r.data)
export const getPaymentRuns = () => api.get('/payments/runs').then(r => r.data)
export const createPaymentRun = (body) => api.post('/payments/runs', body).then(r => r.data)
export const processPaymentRun = (runId) => api.post(`/payments/runs/${runId}/process`).then(r => r.data)

// TDS
export const getTDSDeductions = () => api.get('/tds').then(r => r.data)
export const getTDSSummary = () => api.get('/tds/summary').then(r => r.data)
export const getTDSRates = () => api.get('/tds/rates').then(r => r.data)
export const createTDSDeduction = (body) => api.post('/tds', body).then(r => r.data)

// Documents
export const getDocuments = (params) => api.get('/documents', { params }).then(r => r.data)
export const getDocumentSummary = () => api.get('/documents/summary').then(r => r.data)
export const createDocument = (body) => api.post('/documents', body).then(r => r.data)
export const deleteDocument = (id) => api.delete(`/documents/${id}`).then(r => r.data)

export default api

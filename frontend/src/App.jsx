import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import PurchaseRequests from './pages/PurchaseRequests'
import PurchaseOrders from './pages/PurchaseOrders'
import Invoices from './pages/Invoices'
import InvoiceDetail from './pages/InvoiceDetail'
import GSTCache from './pages/GSTCache'
import MSMECompliance from './pages/MSMECompliance'
import EBSIntegration from './pages/EBSIntegration'
import AIAgents from './pages/AIAgents'
import SpendAnalytics from './pages/SpendAnalytics'
import Suppliers from './pages/Suppliers'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="purchase-requests" element={<PurchaseRequests />} />
          <Route path="purchase-orders" element={<PurchaseOrders />} />
          <Route path="invoices" element={<Invoices />} />
          <Route path="invoices/:id" element={<InvoiceDetail />} />
          <Route path="gst-cache" element={<GSTCache />} />
          <Route path="msme" element={<MSMECompliance />} />
          <Route path="ebs" element={<EBSIntegration />} />
          <Route path="ai-agents" element={<AIAgents />} />
          <Route path="analytics" element={<SpendAnalytics />} />
          <Route path="suppliers" element={<Suppliers />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

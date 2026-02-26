import { useEffect, useState } from 'react'
import { getDocuments, getDocumentSummary } from '../api'
import { FileText, FolderOpen, HardDrive, File, RefreshCw } from 'lucide-react'

const fmtSize = (bytes) => {
  if (!bytes) return '—'
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

const DOC_TYPE_ICON = {
  INVOICE_PDF: '📄',
  PO_COPY: '📋',
  GRN_PHOTO: '📸',
  TAX_CERTIFICATE: '📜',
  CONTRACT: '📝',
  RECEIPT: '🧾',
}

const ENTITY_COLOR = {
  INVOICE: 'bg-blue-100 text-blue-800',
  PURCHASE_ORDER: 'bg-purple-100 text-purple-800',
  GRN: 'bg-green-100 text-green-800',
  SUPPLIER: 'bg-orange-100 text-orange-800',
  CONTRACT: 'bg-yellow-100 text-yellow-800',
}

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [summary, setSummary] = useState(null)
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([getDocuments(), getDocumentSummary()])
      .then(([d, s]) => { setDocuments(d); setSummary(s); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  const entityTypes = ['ALL', ...new Set(documents.map(d => d.entity_type))]
  const filtered = filter === 'ALL' ? documents : documents.filter(d => d.entity_type === filter)

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading documents…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Document Management</h1>
          <p className="text-sm text-gray-500 mt-0.5">Invoice PDFs, PO copies, GRN photos, tax certificates · Versioned & checksummed</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-blue-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Total Documents</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_documents}</p>
              </div>
              <div className="bg-blue-50 p-2.5 rounded-lg"><FileText className="w-5 h-5 text-blue-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Total Size</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{fmtSize(summary.total_size_bytes)}</p>
              </div>
              <div className="bg-green-50 p-2.5 rounded-lg"><HardDrive className="w-5 h-5 text-green-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-purple-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Entity Types</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{Object.keys(summary.by_entity_type || {}).length}</p>
              </div>
              <div className="bg-purple-50 p-2.5 rounded-lg"><FolderOpen className="w-5 h-5 text-purple-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-yellow-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Doc Types</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{Object.keys(summary.by_document_type || {}).length}</p>
              </div>
              <div className="bg-yellow-50 p-2.5 rounded-lg"><File className="w-5 h-5 text-yellow-600" /></div>
            </div>
          </div>
        </div>
      )}

      {/* By entity type breakdown */}
      {summary && summary.by_entity_type && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Documents by Entity Type</h3>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(summary.by_entity_type).map(([type, count]) => (
              <div key={type} className={`rounded-lg px-4 py-2 text-xs font-medium ${ENTITY_COLOR[type] || 'bg-gray-100 text-gray-800'}`}>
                {type}: <span className="font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {entityTypes.map(t => (
          <button key={t}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === t ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            onClick={() => setFilter(t)}>
            {t === 'ALL' ? `All (${documents.length})` : `${t} (${documents.filter(d => d.entity_type === t).length})`}
          </button>
        ))}
      </div>

      {/* Document table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['', 'File Name', 'Entity', 'Entity ID', 'Type', 'Size', 'Version', 'Uploaded By', 'Date'].map(h => (
                <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.length === 0 ? (
              <tr><td colSpan={9} className="px-3 py-8 text-center text-gray-400 text-sm">No documents found</td></tr>
            ) : filtered.map(d => (
              <tr key={d.id} className="table-row-hover">
                <td className="px-3 py-3 text-lg">{DOC_TYPE_ICON[d.document_type] || '📎'}</td>
                <td className="px-3 py-3">
                  <div className="font-medium text-gray-800 text-xs">{d.file_name}</div>
                  <div className="text-[10px] text-gray-400 font-mono">{d.mime_type}</div>
                </td>
                <td className="px-3 py-3">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${ENTITY_COLOR[d.entity_type] || 'bg-gray-100 text-gray-800'}`}>
                    {d.entity_type}
                  </span>
                </td>
                <td className="px-3 py-3 font-mono text-xs text-blue-700">{d.entity_id}</td>
                <td className="px-3 py-3 text-xs text-gray-600">{d.document_type?.replace(/_/g, ' ')}</td>
                <td className="px-3 py-3 text-xs text-gray-500">{fmtSize(d.file_size)}</td>
                <td className="px-3 py-3"><span className="badge badge-blue text-[10px]">v{d.version}</span></td>
                <td className="px-3 py-3 text-xs text-gray-500">{d.uploaded_by || '—'}</td>
                <td className="px-3 py-3 text-xs text-gray-400">{d.created_at ? new Date(d.created_at).toLocaleDateString('en-IN') : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

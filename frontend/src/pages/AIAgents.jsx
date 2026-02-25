import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAIInsights, applyAIInsight } from '../api'
import { Bot, CheckCircle, AlertTriangle, Shield, Zap, TrendingDown } from 'lucide-react'

const AGENT_ICON = {
  InvoiceCodingAgent: { Icon: Bot, color: 'text-purple-500', bg: 'bg-purple-50' },
  FraudDetectionAgent: { Icon: Shield, color: 'text-red-500', bg: 'bg-red-50' },
  SLAPredictionAgent: { Icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50' },
  CashOptimizationAgent: { Icon: TrendingDown, color: 'text-green-500', bg: 'bg-green-50' },
  RiskAgent: { Icon: Zap, color: 'text-orange-500', bg: 'bg-orange-50' },
}

const TYPE_BADGE = {
  GL_CODING:        'badge badge-purple',
  FRAUD_ALERT:      'badge badge-red',
  MSME_SLA_RISK:    'badge badge-yellow',
  MSME_SLA_BREACH:  'badge badge-red',
  EARLY_PAYMENT:    'badge badge-green',
  SUPPLIER_RISK:    'badge badge-orange',
}

function ConfidenceBar({ value }) {
  const color = value >= 90 ? 'bg-green-500' : value >= 70 ? 'bg-blue-500' : 'bg-yellow-500'
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">Confidence</span>
        <span className="font-bold text-gray-700">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export default function AIAgents() {
  const [data, setData] = useState(null)
  const [applying, setApplying] = useState(null)
  const nav = useNavigate()
  const load = () => getAIInsights().then(setData)
  useEffect(() => { load() }, [])

  const doApply = async (id) => {
    setApplying(id)
    await applyAIInsight(id)
    await load()
    setApplying(null)
  }

  if (!data) return <div className="text-gray-400 py-8 text-center">Loading…</div>

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">AI Agent Layer</h1>
        <p className="text-sm text-gray-500 mt-0.5">5 specialized agents · Each subscribes to domain events · Emits recommendations with confidence scoring</p>
      </div>

      {/* Agent status cards */}
      <div className="grid grid-cols-5 gap-3">
        {data.agents.map(agent => {
          const { Icon, color, bg } = AGENT_ICON[agent.name] || { Icon: Bot, color: 'text-gray-500', bg: 'bg-gray-50' }
          return (
            <div key={agent.name} className={`rounded-xl border p-4 ${bg} border-opacity-50`}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <span className={`w-2 h-2 rounded-full ${agent.status === 'ACTIVE' ? 'bg-green-400' : 'bg-gray-300'}`}></span>
              </div>
              <div className="font-semibold text-gray-800 text-xs leading-tight">{agent.name}</div>
              <div className="text-[10px] text-gray-400 mt-1 font-mono">{agent.model}</div>
              <div className="mt-3 space-y-1 text-[10px] text-gray-600">
                <div>Avg Confidence: <strong>{agent.avg_confidence}%</strong></div>
                {agent.invoices_coded_mtd && <div>Invoices coded: <strong>{agent.invoices_coded_mtd}</strong></div>}
                {agent.flags_raised_mtd !== undefined && <div>Flags MTD: <strong>{agent.flags_raised_mtd}</strong></div>}
                {agent.alerts_raised_mtd !== undefined && <div>Alerts MTD: <strong>{agent.alerts_raised_mtd}</strong></div>}
                {agent.savings_identified && <div>Savings ID: <strong>₹{(agent.savings_identified/1000).toFixed(0)}K</strong></div>}
              </div>
            </div>
          )
        })}
      </div>

      {/* How AI layer works */}
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 text-sm">
        <div className="font-semibold text-purple-900 mb-2">🤖 AI Agent Architecture</div>
        <div className="flex items-center gap-2 text-xs text-purple-800 flex-wrap">
          <span className="bg-purple-100 px-2 py-1 rounded">Domain Event (e.g. InvoiceCaptured)</span>
          <span>→</span>
          <span className="bg-purple-100 px-2 py-1 rounded">Agent subscribes via Kafka</span>
          <span>→</span>
          <span className="bg-purple-100 px-2 py-1 rounded">Model inference on structured data</span>
          <span>→</span>
          <span className="bg-purple-100 px-2 py-1 rounded">Emits RecommendationEvent (confidence + reasoning)</span>
          <span>→</span>
          <span className="bg-purple-100 px-2 py-1 rounded">AI Orchestrator aggregates signals</span>
          <span>→</span>
          <span className="bg-purple-100 px-2 py-1 rounded">Auto-apply or human review</span>
        </div>
      </div>

      {/* Insights */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-700">Agent Insights — Current Period</h2>
        {data.insights.map(ai => {
          const { Icon, color, bg } = AGENT_ICON[ai.agent] || { Icon: Bot, color: 'text-gray-500', bg: 'bg-gray-50' }
          return (
            <div key={ai.id} className={`card border ${
              ai.type === 'FRAUD_ALERT' ? 'border-red-200' :
              ai.type.includes('MSME') ? 'border-yellow-200' :
              ai.type === 'GL_CODING' ? 'border-purple-200' : 'border-gray-200'}`}>
              <div className="flex gap-4">
                <div className={`${bg} rounded-xl p-3 flex-shrink-0 flex items-center justify-center`}>
                  <Icon className={`w-5 h-5 ${color}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-xs font-bold text-gray-600 uppercase">{ai.agent}</span>
                    <span className={TYPE_BADGE[ai.type] || 'badge badge-gray'}>{ai.type.replace(/_/g,' ')}</span>
                    <span className={`badge text-[10px] ${ai.applied ? 'badge-green' : 'badge-yellow'}`}>{ai.status}</span>
                    {ai.invoice_id && (
                      <button
                        className="text-xs text-blue-600 hover:underline"
                        onClick={() => nav(`/invoices/${ai.invoice_id}`)}>
                        View Invoice →
                      </button>
                    )}
                  </div>
                  <p className="text-sm font-semibold text-gray-800 mb-1">{ai.recommendation}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{ai.reasoning}</p>
                  {ai.applied_at && (
                    <p className="text-xs text-green-600 mt-1">Applied: {new Date(ai.applied_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>
                  )}
                </div>
                <div className="w-32 flex-shrink-0">
                  <ConfidenceBar value={ai.confidence} />
                  {!ai.applied && (
                    <button
                      className="btn-primary w-full text-xs mt-2 py-1.5"
                      disabled={applying === ai.id}
                      onClick={() => doApply(ai.id)}>
                      {applying === ai.id ? '…' : 'Apply'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// AgentStatusBar.jsx – Real-time agent health display
import { Shield, Activity, Target, Database, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

const AGENTS = [
    { key: 'risk', label: 'Risk Guardian', icon: Shield },
    { key: 'drift', label: 'Drift Monitor', icon: Activity },
    { key: 'threshold', label: 'Threshold Opt', icon: Target },
    { key: 'data', label: 'Data Integrity', icon: Database },
]

function StatusIcon({ healthy }) {
    if (healthy === true) return <CheckCircle size={14} className="text-accent-green" />
    if (healthy === false) return <XCircle size={14} className="text-accent-red" />
    return <AlertCircle size={14} className="text-accent-gold" />
}

export default function AgentStatusBar({ agentStatus }) {
    const risk = agentStatus?.risk || {}
    const drift = agentStatus?.drift || {}
    const threshold = agentStatus?.threshold || {}

    const agentHealthMap = {
        risk: !risk.hold_mode,
        drift: !drift.drift_detected,
        threshold: true,
        data: true,
    }

    const overallHealthy = agentStatus?.overall_healthy

    return (
        <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-text-secondary uppercase tracking-wider">Agent Status</p>
                <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${overallHealthy
                    ? 'bg-accent-green/10 text-accent-green'
                    : 'bg-accent-red/10 text-accent-red'
                    }`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${overallHealthy ? 'animate-pulse bg-accent-green' : 'bg-accent-red'}`} />
                    {overallHealthy ? 'All Systems OK' : 'Attention Required'}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {AGENTS.map(({ key, label, icon: Icon }) => {
                    const healthy = agentHealthMap[key]
                    return (
                        <div key={key} className="bg-bg-secondary rounded-xl p-3 flex items-center gap-2">
                            <Icon size={16} className="text-text-secondary flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                                <p className="text-xs text-text-secondary truncate">{label}</p>
                                <p className={`text-xs font-bold mt-0.5 ${healthy ? 'text-accent-green' : 'text-accent-red'}`}>
                                    {healthy ? 'OK' : 'ALERT'}
                                </p>
                            </div>
                            <StatusIcon healthy={healthy} />
                        </div>
                    )
                })}
            </div>

            {/* Risk detail */}
            {risk.hold_mode && (
                <div className="mt-3 bg-accent-red/10 border border-accent-red/30 rounded-xl px-4 py-2 text-xs text-accent-red flex items-center gap-1.5">
                    <Shield size={12} /> {risk.hold_reason}
                </div>
            )}

            {/* Drift detail */}
            {drift.retrain_triggered && (
                <div className="mt-2 bg-accent-gold/10 border border-accent-gold/30 rounded-xl px-4 py-2 text-xs text-accent-gold flex items-center gap-1.5">
                    <Activity size={12} /> Retrain triggered: {drift.reason}
                </div>
            )}

            {/* Metrics row */}
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                <div>
                    <p className="text-xs text-text-muted">Trades Today</p>
                    <p className="text-sm font-bold text-text-primary font-mono">
                        {risk.trades_today ?? '—'}/{risk.max_trades ?? 2}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-text-muted">Drawdown</p>
                    <p className={`text-sm font-bold font-mono ${(risk.drawdown_pct || 0) > 1.5 ? 'text-accent-red' : 'text-accent-green'}`}>
                        {risk.drawdown_pct ?? '0.00'}%
                    </p>
                </div>
                <div>
                    <p className="text-xs text-text-muted">Threshold</p>
                    <p className="text-sm font-bold text-accent-blue font-mono">
                        {threshold.current_threshold ? `${(threshold.current_threshold * 100).toFixed(0)}%` : '70%'}
                    </p>
                </div>
            </div>
        </div>
    )
}

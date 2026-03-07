// OpportunityRecovery.jsx – AI Opportunity Recovery Engine panel
import { useState, useEffect } from 'react'
import { Clock, TrendingUp, TrendingDown, Target, ShieldAlert, Crosshair, CheckCircle, AlertTriangle, AlertCircle, RefreshCw } from 'lucide-react'
import { getRecoveryOpportunities } from '../services/api.js'

export default function OpportunityRecovery({ instrument }) {
    const [opportunities, setOpportunities] = useState([])
    const [loading, setLoading] = useState(true)

    const fetchOps = () => {
        setLoading(true)
        getRecoveryOpportunities(instrument)
            .then(data => {
                setOpportunities(data.opportunities || [])
            })
            .catch(err => console.error("Error fetching recovery ops:", err))
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        fetchOps()
    }, [instrument])

    if (loading) {
        return (
            <div className="glass-card p-4 animate-fade-in flex flex-col items-center justify-center min-h-[300px]">
                <Clock className="animate-spin text-text-muted mb-4 opacity-50" size={32} />
                <p className="text-sm font-semibold text-text-muted">Analyzing past signals...</p>
                <p className="text-xs text-text-secondary mt-2">Checking if missed opportunities are still valid</p>
            </div>
        )
    }

    if (opportunities.length === 0) {
        return (
            <div className="glass-card p-6 min-h-[300px] flex flex-col items-center justify-center animate-fade-in text-center">
                <div className="w-16 h-16 rounded-full bg-slate-500/10 flex items-center justify-center mb-4">
                    <CheckCircle className="text-text-muted opacity-40" size={32} />
                </div>
                <h3 className="text-sm font-bold text-text-primary">No Missed Opportunities</h3>
                <p className="text-xs text-text-secondary mt-2 max-w-xs">
                    You are caught up on all high-confidence signals for {instrument.replace('_', '/')}.
                    Wait for new AI setups to form.
                </p>
                <button
                    onClick={fetchOps}
                    className="mt-6 px-4 py-2 rounded-lg bg-bg-secondary text-xs font-semibold text-text-primary hover:bg-bg-tertiary transition-colors flex items-center gap-2"
                >
                    <RefreshCw size={14} /> Refresh Analysis
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Header / Intro */}
            <div className="glass-card p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-accent-blue/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
                <div className="flex items-start gap-4 relative z-10">
                    <div className="w-10 h-10 rounded-xl bg-accent-blue/10 flex items-center justify-center shrink-0 border border-accent-blue/20">
                        <Clock className="text-accent-blue" size={20} />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-text-primary mb-1 tracking-tight">AI Market Intelligence Report</h2>
                        <p className="text-xs text-text-secondary leading-relaxed">
                            Our AI detected <strong className="text-text-primary">{opportunities.length} high-confidence signals</strong> recently.
                            Here is the instant analysis on whether these opportunities are still actionable based on live market conditions.
                        </p>
                    </div>
                    <button onClick={fetchOps} className="ml-auto text-text-muted hover:text-text-primary transition-colors p-2 rounded-lg hover:bg-bg-secondary">
                        <RefreshCw size={16} />
                    </button>
                </div>
            </div>

            {/* List of Opportunities */}
            <div className="grid grid-cols-1 gap-4">
                {opportunities.map((op, i) => {
                    const isBuy = op.direction === 'BUY'
                    const StatusIcon = op.status === 'VALID' ? CheckCircle : op.status === 'RISKY' ? AlertTriangle : Crosshair

                    return (
                        <div key={i} className="glass-card p-5 border-l-4 transition-all hover:bg-bg-card/80"
                            style={{ borderLeftColor: op.color }}>
                            {/* Card Header (Pair, Direction, Time) */}
                            <div className="flex items-center justify-between mb-4 pb-4 border-b border-border/50">
                                <div className="flex items-center gap-3">
                                    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold ${isBuy ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'}`}>
                                        {isBuy ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                        {op.direction} {op.pair.replace('_', '/')}
                                    </div>
                                    <span className="text-xs font-semibold text-text-muted flex items-center gap-1.5">
                                        <Clock size={12} /> {op.time_text}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2" style={{ color: op.color }}>
                                    <StatusIcon size={14} />
                                    <span className="text-xs font-bold tracking-wide uppercase">{op.status_text}</span>
                                </div>
                            </div>

                            {/* Body (Assessment & Recommendation) */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <div>
                                    <h4 className="text-[10px] uppercase tracking-widest text-text-muted mb-2 font-bold flex items-center gap-1.5">
                                        <Target size={12} className="opacity-70" /> AI Assessment
                                    </h4>
                                    <p className="text-xs text-text-secondary leading-relaxed">
                                        {op.assessment}
                                    </p>
                                </div>
                                <div className="pl-0 lg:pl-4 border-l-0 lg:border-l border-border/50 flex flex-col justify-center">
                                    <div className="flex items-start gap-2 p-3 rounded-lg" style={{ background: `${op.color}10`, border: `1px solid ${op.color}25` }}>
                                        <AlertCircle size={14} style={{ color: op.color, marginTop: 1, shrink: 0 }} />
                                        <p className="text-xs font-medium leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                                            {op.recommendation}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

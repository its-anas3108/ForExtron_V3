// SignalTimeline.jsx – Vertical timeline of past signals with expandable details
import { useState } from 'react'
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp, History } from 'lucide-react'

const DECISION_COLORS = {
    BUY: { bg: 'var(--accent-green)', text: 'var(--accent-green)' },
    SELL: { bg: 'var(--accent-red)', text: 'var(--accent-red)' },
    HOLD: { bg: 'var(--accent-gold)', text: 'var(--accent-gold)' },
}

const DECISION_ICONS = { BUY: TrendingUp, SELL: TrendingDown, HOLD: Minus }

function formatTime(ts) {
    if (!ts) return '—'
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatDate(ts) {
    if (!ts) return ''
    const d = new Date(ts)
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

function TimelineEntry({ signal, isLast }) {
    const [expanded, setExpanded] = useState(false)
    const decision = signal.decision || 'HOLD'
    const colors = DECISION_COLORS[decision] || DECISION_COLORS.HOLD
    const Icon = DECISION_ICONS[decision] || Minus
    const prob = ((signal.ensemble_probability || 0) * 100).toFixed(1)

    return (
        <div className="flex gap-3 relative">
            {/* Dot + line */}
            <div className="flex flex-col items-center" style={{ width: 24 }}>
                <div
                    className="timeline-dot"
                    style={{ background: colors.bg }}
                />
                {!isLast && (
                    <div style={{
                        width: 2, flex: 1, minHeight: 20,
                        background: `linear-gradient(to bottom, var(--border), transparent)`,
                    }} />
                )}
            </div>

            {/* Content */}
            <div className="timeline-entry flex-1 mb-1" onClick={() => setExpanded(!expanded)}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Icon size={14} style={{ color: colors.text }} />
                        <span style={{
                            fontSize: '0.8rem', fontWeight: 700, color: colors.text,
                        }}>
                            {decision}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                            {prob}%
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                            {formatTime(signal.timestamp)}
                        </span>
                        {expanded ? <ChevronUp size={12} style={{ color: 'var(--text-muted)' }} />
                            : <ChevronDown size={12} style={{ color: 'var(--text-muted)' }} />}
                    </div>
                </div>

                {/* Expanded details */}
                {expanded && (
                    <div className="mt-2 animate-fade-in" style={{ fontSize: '0.7rem' }}>
                        <div style={{
                            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8,
                            background: 'var(--bg-secondary)', borderRadius: 8, padding: '0.5rem',
                        }}>
                            <div>
                                <span style={{ color: 'var(--text-muted)' }}>SL</span>
                                <br />
                                <span style={{ color: 'var(--accent-red)', fontFamily: 'monospace', fontWeight: 600 }}>
                                    {signal.sl?.toFixed(5) || '—'}
                                </span>
                            </div>
                            <div>
                                <span style={{ color: 'var(--text-muted)' }}>TP</span>
                                <br />
                                <span style={{ color: 'var(--accent-green)', fontFamily: 'monospace', fontWeight: 600 }}>
                                    {signal.tp?.toFixed(5) || '—'}
                                </span>
                            </div>
                            <div>
                                <span style={{ color: 'var(--text-muted)' }}>R:R</span>
                                <br />
                                <span style={{ color: 'var(--accent-blue)', fontFamily: 'monospace', fontWeight: 600 }}>
                                    1:{signal.rr?.toFixed(1) || '—'}
                                </span>
                            </div>
                        </div>

                        {/* Gate summary */}
                        {signal.gate_log && (
                            <div className="mt-2 flex flex-wrap gap-1">
                                {Object.entries(signal.gate_log).filter(([k]) => !k.includes('reason')).map(([gate, passed]) => (
                                    <span key={gate} style={{
                                        fontSize: '0.6rem', padding: '2px 6px', borderRadius: 4,
                                        background: passed ? 'rgba(5,150,105,0.1)' : 'rgba(220,38,38,0.1)',
                                        color: passed ? 'var(--accent-green)' : 'var(--accent-red)',
                                        fontWeight: 600,
                                    }}>
                                        {passed ? 'PASS' : 'FAIL'} {gate.replace(/_/g, ' ')}
                                    </span>
                                ))}
                            </div>
                        )}

                        {signal.demo && (
                            <span style={{
                                display: 'inline-block', marginTop: 4, fontSize: '0.6rem', padding: '1px 6px',
                                borderRadius: 4, background: 'rgba(96,165,250,0.12)', color: 'var(--accent-blue)',
                            }}>
                                DEMO
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

export default function SignalTimeline({ signalHistory = [] }) {
    const entries = signalHistory.slice(0, 20)

    if (entries.length === 0) {
        return (
            <div className="glass-card p-4 text-center" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                <History className="mx-auto mb-2 opacity-50" size={24} />
                <p>No signal history yet</p>
                <p style={{ fontSize: '0.7rem', marginTop: 4 }}>Signals will appear here as they're generated</p>
            </div>
        )
    }

    return (
        <div className="glass-card p-4">
            <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                <History size={14} /> Signal Timeline
            </h3>
            <div style={{ maxHeight: 320, overflowY: 'auto', paddingRight: 4 }}>
                {entries.map((sig, i) => (
                    <TimelineEntry key={sig.timestamp || i} signal={sig} isLast={i === entries.length - 1} />
                ))}
            </div>
        </div>
    )
}

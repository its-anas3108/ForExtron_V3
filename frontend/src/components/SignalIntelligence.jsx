// SignalIntelligence.jsx -- XAI Signal Intelligence Engine
// Transforms black-box trade signals into transparent, analyst-grade reasoning panels
import { useState, useEffect } from 'react'
import { Brain, Shield, AlertTriangle, CheckCircle, XCircle, Target, TrendingUp, TrendingDown, Eye, Crosshair, Award } from 'lucide-react'
import { getSignalIntelligence } from '../services/api.js'

const GRADE_BG = {
    'A+': 'rgba(34,197,94,0.12)', A: 'rgba(34,197,94,0.10)',
    'B+': 'rgba(59,130,246,0.10)', B: 'rgba(245,158,11,0.10)',
    C: 'rgba(249,115,22,0.10)', D: 'rgba(239,68,68,0.10)',
}

function GradeBadge({ grade, color }) {
    return (
        <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: GRADE_BG[grade] || 'rgba(148,163,184,0.1)',
            border: `2px solid ${color}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column',
        }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 900, color, lineHeight: 1 }}>{grade}</span>
            <span style={{ fontSize: '0.45rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Grade</span>
        </div>
    )
}

function ReasoningFactor({ factor, index }) {
    return (
        <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 10px',
            borderRadius: 8, marginBottom: 4,
            background: factor.passed ? 'rgba(34,197,94,0.04)' : 'rgba(239,68,68,0.04)',
            borderLeft: `3px solid ${factor.passed ? '#22c55e' : '#ef4444'}`,
            transition: 'transform 0.2s',
        }}>
            <div style={{ marginTop: 2, flexShrink: 0 }}>
                {factor.passed
                    ? <CheckCircle size={14} style={{ color: '#22c55e' }} />
                    : <XCircle size={14} style={{ color: '#ef4444' }} />
                }
            </div>
            <div style={{ flex: 1 }}>
                <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
                    {factor.label}
                    <span style={{
                        marginLeft: 6, fontSize: '0.5rem', fontWeight: 700, padding: '1px 5px',
                        borderRadius: 3, color: 'white',
                        background: factor.passed ? '#22c55e' : '#ef4444',
                    }}>{factor.passed ? 'PASS' : 'FAIL'}</span>
                </p>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    {factor.detail}
                </p>
            </div>
        </div>
    )
}

function ModelVoteBar({ vote }) {
    const barWidth = Math.max(vote.probability * 100, 5)
    const barColor = vote.agrees ? '#22c55e' : '#ef4444'
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
            <span style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-secondary)', width: 110, flexShrink: 0, textAlign: 'right' }}>
                {vote.model}
            </span>
            <div style={{ flex: 1, height: 14, borderRadius: 7, background: 'rgba(148,163,184,0.1)', position: 'relative', overflow: 'hidden' }}>
                <div style={{
                    width: `${barWidth}%`, height: '100%', borderRadius: 7,
                    background: `linear-gradient(90deg, ${barColor}aa, ${barColor})`,
                    transition: 'width 0.8s ease',
                }} />
                <span style={{
                    position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
                    fontSize: '0.5rem', fontWeight: 700, color: 'var(--text-primary)',
                }}>{(vote.probability * 100).toFixed(1)}%</span>
            </div>
            <span style={{
                fontSize: '0.5rem', fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                color: 'white', background: barColor, flexShrink: 0, minWidth: 30, textAlign: 'center',
            }}>{vote.vote}</span>
        </div>
    )
}

export default function SignalIntelligence({ signal }) {
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (signal && signal.decision && signal.decision !== 'HOLD') {
            setLoading(true)
            getSignalIntelligence(signal)
                .then(data => {
                    if (data.available) setAnalysis(data)
                })
                .catch(err => console.error('XAI error:', err))
                .finally(() => setLoading(false))
        } else {
            setAnalysis(null)
        }
    }, [signal?.decision, signal?.pair, signal?.timestamp])

    if (loading) {
        return (
            <div className="glass-card p-4 animate-fade-in">
                <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <Brain size={22} className="animate-spin" style={{ margin: '0 auto 8px', display: 'block' }} />
                    Analyzing signal intelligence...
                </div>
            </div>
        )
    }

    if (!analysis) {
        return (
            <div className="glass-card p-4 animate-fade-in">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                    <Eye size={16} />
                    <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>Signal Intelligence</h3>
                </div>
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                    <Eye size={28} style={{ margin: '0 auto 8px', display: 'block', color: 'var(--text-muted)', opacity: 0.5 }} />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Generate a BUY or SELL signal to see AI reasoning.
                    </p>
                    <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>
                        The engine will explain why the trade was triggered and what could invalidate it.
                    </p>
                </div>
            </div>
        )
    }

    const dirIcon = analysis.direction === 'BUY'
        ? <TrendingUp size={16} style={{ color: '#22c55e' }} />
        : <TrendingDown size={16} style={{ color: '#ef4444' }} />

    const dirColor = analysis.direction === 'BUY' ? '#22c55e' : '#ef4444'

    return (
        <div className="glass-card p-4 animate-fade-in">
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <Eye size={16} /> Signal Intelligence
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                        {analysis.factors_passed}/{analysis.factors_total} Factors Aligned
                    </span>
                </div>
            </div>

            {/* Signal Summary + Grade */}
            <div style={{
                display: 'flex', gap: 12, alignItems: 'center', marginBottom: 14,
                padding: 12, borderRadius: 12,
                background: `linear-gradient(135deg, ${GRADE_BG[analysis.grade] || 'rgba(148,163,184,0.05)'}, transparent)`,
                border: `1px solid ${analysis.grade_color}25`,
            }}>
                <GradeBadge grade={analysis.grade} color={analysis.grade_color} />
                <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        {dirIcon}
                        <span style={{ fontSize: '1rem', fontWeight: 800, color: dirColor }}>{analysis.direction}</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            {analysis.pair?.replace('_', '/')}
                        </span>
                    </div>
                    <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                        Confidence: {(analysis.confidence * 100).toFixed(1)}%
                        &nbsp; | &nbsp; R:R {analysis.rr}:1
                        &nbsp; | &nbsp; RSI {analysis.rsi?.toFixed(1)}
                        &nbsp; | &nbsp; Regime: {analysis.regime?.replace('_', ' ')}
                    </p>
                </div>
            </div>

            {/* WHY THIS TRADE? - Reasoning factors */}
            <div style={{ marginBottom: 14 }}>
                <p style={{
                    fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 8,
                    display: 'flex', alignItems: 'center', gap: 6,
                }}>
                    <Brain size={12} /> Why This Trade?
                </p>
                {analysis.factors.map((f, i) => (
                    <ReasoningFactor key={i} factor={f} index={i} />
                ))}
            </div>

            {/* Model Vote Breakdown */}
            <div style={{ marginBottom: 14 }}>
                <p style={{
                    fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)',
                    textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 8,
                    display: 'flex', alignItems: 'center', gap: 6,
                }}>
                    <Award size={12} /> Model Votes
                </p>
                <div style={{ padding: '8px 0' }}>
                    {analysis.model_votes.map((v, i) => (
                        <ModelVoteBar key={i} vote={v} />
                    ))}
                </div>
            </div>

            {/* Invalidation Alert */}
            <div style={{
                padding: '10px 14px', borderRadius: 10, marginBottom: 10,
                background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Crosshair size={14} style={{ color: '#ef4444' }} />
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        Invalidation Level
                    </span>
                    <span style={{
                        marginLeft: 'auto', fontSize: '0.8rem', fontWeight: 800, color: '#ef4444',
                        fontFamily: 'JetBrains Mono, monospace',
                    }}>
                        {analysis.invalidation.price?.toFixed(5)}
                    </span>
                </div>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {analysis.invalidation.description}
                </p>
            </div>

            {/* Market Context */}
            <div style={{
                padding: '10px 14px', borderRadius: 10, marginBottom: 10,
                background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Target size={14} style={{ color: '#3b82f6' }} />
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        Market Context
                    </span>
                </div>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {analysis.market_context}
                </p>
            </div>

            {/* AI Recommendation */}
            <div style={{
                padding: '10px 14px', borderRadius: 10,
                background: `${analysis.recommendation.risk_color}10`,
                border: `1px solid ${analysis.recommendation.risk_color}25`,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <Shield size={14} style={{ color: analysis.recommendation.risk_color }} />
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: analysis.recommendation.risk_color, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        AI Recommendation
                    </span>
                    <span style={{
                        marginLeft: 'auto', fontSize: '0.55rem', fontWeight: 800,
                        padding: '2px 8px', borderRadius: 4,
                        color: 'white', background: analysis.recommendation.risk_color,
                    }}>
                        {analysis.recommendation.risk_level} RISK
                    </span>
                </div>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {analysis.recommendation.text}
                </p>
            </div>
        </div>
    )
}

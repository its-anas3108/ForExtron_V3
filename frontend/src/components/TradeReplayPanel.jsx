// TradeReplayPanel.jsx – AI Trade Replay Engine with post-trade analysis
import { useState, useEffect } from 'react'
import { Repeat, Brain, Lightbulb, CheckCircle, XCircle, Target, Shield, BarChart3 } from 'lucide-react'
import { analyzeTradeReplay } from '../services/api.js'

const IMPORTANCE_COLORS = {
    high: '#ef4444',
    medium: '#f59e0b',
    low: '#22c55e',
}

function FactorCard({ factor, index }) {
    const color = IMPORTANCE_COLORS[factor.importance] || '#94a3b8'
    return (
        <div style={{
            padding: '10px 12px', borderRadius: 10, marginBottom: 6,
            background: 'var(--bg-secondary)',
            borderLeft: `3px solid ${color}`,
            transition: 'transform 0.2s',
        }}
            className="hover:scale-[1.01]"
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                <span style={{
                    fontSize: '0.55rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
                    padding: '1px 5px', borderRadius: 3, color: 'white',
                    background: color,
                }}>
                    {factor.importance}
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)' }}>{factor.category}</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>{factor.detail}</p>
        </div>
    )
}

export default function TradeReplayPanel({ signal, signalHistory }) {
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)
    const [selectedTrade, setSelectedTrade] = useState(null)

    // Build a trade from the latest signal for demo analysis
    const analyzeTrade = async (trade) => {
        setLoading(true)
        try {
            // Extract gate_log properly — it may be nested or missing
            let gateLog = trade.gate_log
            if (!gateLog || Object.keys(gateLog).length === 0) {
                gateLog = {
                    regime_ok: true,
                    structure_bullish: true,
                    liquidity_sweep_ok: Math.random() > 0.5,
                    probability_ok: true,
                    rsi_ok: true,
                    rr_ok: true,
                    guardian_ok: true,
                }
            }

            let modelContribs = trade.model_contributions
            if (!modelContribs || Object.keys(modelContribs).length === 0) {
                const conf = trade.ensemble_probability || trade.confidence || 0.72
                modelContribs = {
                    logistic: Math.max(0.4, conf - 0.15 + Math.random() * 0.1),
                    dnn: Math.max(0.4, conf - 0.05 + Math.random() * 0.1),
                    gru: Math.max(0.4, conf + Math.random() * 0.1),
                    cnn: Math.max(0.4, conf - 0.08 + Math.random() * 0.1),
                    transformer: Math.max(0.4, conf - 0.12 + Math.random() * 0.1),
                }
            }

            const res = await analyzeTradeReplay({
                pair: trade.pair || 'EUR_USD',
                direction: trade.decision || trade.direction || 'BUY',
                entry: trade.entry || trade.price || 1.0850,
                sl: trade.sl || 1.0820,
                tp: trade.tp || 1.0910,
                result: trade.pnl > 0 ? 'win' : 'loss',
                pnl: trade.pnl || -15.0,
                regime: trade.regime || 'expansion',
                confidence: trade.ensemble_probability || trade.confidence || 0.72,
                gate_log: gateLog,
                model_contributions: modelContribs,
                duration_minutes: trade.duration_minutes || 45,
            })
            setAnalysis(res)
            setSelectedTrade(trade)
        } catch (err) {
            console.error('Replay analysis error:', err)
        } finally {
            setLoading(false)
        }
    }

    // Auto-analyze the latest completed signal or replay a historical one
    useEffect(() => {
        if (signal && signal.decision !== 'HOLD' && selectedTrade?.timestamp !== signal.timestamp) {
            const demoPnl = signal.decision === 'BUY'
                ? Math.round((Math.random() * 60 - 20) * 10) / 10
                : Math.round((Math.random() * 60 - 20) * 10) / 10
            analyzeTrade({ ...signal, pnl: demoPnl })
        } else if (!selectedTrade && signalHistory && signalHistory.length > 0) {
            const lastActive = signalHistory.find(s => s.decision !== 'HOLD')
            if (lastActive) {
                const demoPnl = lastActive.decision === 'BUY'
                    ? Math.round((Math.random() * 60 - 20) * 10) / 10
                    : Math.round((Math.random() * 60 - 20) * 10) / 10
                analyzeTrade({ ...lastActive, pnl: demoPnl })
            }
        }
    }, [signal?.timestamp, signalHistory?.length])

    return (
        <div className="glass-card p-4 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <Repeat size={16} /> AI Trade Replay
                </h3>
                {signalHistory && signalHistory.filter(s => s.decision !== 'HOLD').length > 0 && (
                    <select
                        onChange={(e) => {
                            const selected = signalHistory.find(s => s.timestamp === e.target.value)
                            if (selected) {
                                const demoPnl = selected.decision === 'BUY'
                                    ? Math.round((Math.random() * 60 - 20) * 10) / 10
                                    : Math.round((Math.random() * 60 - 20) * 10) / 10
                                analyzeTrade({ ...selected, pnl: demoPnl })
                            }
                        }}
                        style={{
                            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)', borderRadius: 6, padding: '4px 8px',
                            fontSize: '0.75rem', outline: 'none', cursor: 'pointer'
                        }}
                        value={selectedTrade?.timestamp || ''}
                    >
                        <option value="" disabled>Select historical trade...</option>
                        {signalHistory.filter(s => s.decision !== 'HOLD').slice(0, 10).map(s => (
                            <option key={s.timestamp} value={s.timestamp}>
                                {new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {s.pair.replace('_', '/')} {s.decision}
                            </option>
                        ))}
                    </select>
                )}
            </div>

            {!analysis && !loading && (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                    <Repeat size={28} style={{ margin: '0 auto 8px', display: 'block', color: 'var(--text-muted)', opacity: 0.5 }} />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Generate a signal to see post-trade AI analysis.
                    </p>
                    <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>
                        The engine will explain why trades succeed or fail.
                    </p>
                </div>
            )}

            {loading && (
                <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <Brain size={20} className="animate-spin" style={{ margin: '0 auto 8px', display: 'block' }} />
                    Analyzing trade outcome...
                </div>
            )}

            {analysis && !loading && (
                <>
                    {/* Trade result summary */}
                    <div style={{
                        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 12,
                        padding: 10, borderRadius: 10,
                        background: analysis.result === 'win' ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
                        border: `1px solid ${analysis.result === 'win' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>Result</p>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                                {analysis.result === 'win'
                                    ? <CheckCircle size={14} style={{ color: '#22c55e' }} />
                                    : <XCircle size={14} style={{ color: '#ef4444' }} />
                                }
                                <span style={{ fontSize: '0.9rem', fontWeight: 800, color: analysis.result === 'win' ? '#22c55e' : '#ef4444' }}>
                                    {analysis.result.toUpperCase()}
                                </span>
                            </div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>P&L</p>
                            <p style={{ fontSize: '0.9rem', fontWeight: 800, color: analysis.pnl >= 0 ? '#22c55e' : '#ef4444' }}>
                                {analysis.pnl >= 0 ? '+' : ''}{analysis.pnl}
                            </p>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>Gates</p>
                            <p style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                                {analysis.gates_passed}/{analysis.total_gates}
                            </p>
                        </div>
                    </div>

                    {/* Trade details row */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6, marginBottom: 12 }}>
                        {[
                            { label: 'Pair', value: analysis.pair?.replace('_', '/') },
                            { label: 'Direction', value: analysis.direction },
                            { label: 'Regime', value: analysis.regime },
                            { label: 'Confidence', value: `${(analysis.confidence * 100).toFixed(0)}%` },
                        ].map((item) => (
                            <div key={item.label} className="glass-card" style={{ padding: '6px 8px', textAlign: 'center' }}>
                                <p style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>{item.label}</p>
                                <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>{item.value}</p>
                            </div>
                        ))}
                    </div>

                    {/* Contributing Factors */}
                    <div style={{ marginBottom: 12 }}>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
                            Contributing Factors
                        </p>
                        {analysis.factors.map((f, i) => (
                            <FactorCard key={i} factor={f} index={i} />
                        ))}
                    </div>

                    {/* AI Insight */}
                    <div style={{
                        padding: '12px 14px', borderRadius: 10, marginBottom: 10,
                        background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                            <Brain size={14} style={{ color: '#3b82f6' }} />
                            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase', letterSpacing: 0.5 }}>AI Insight</span>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{analysis.ai_insight}</p>
                    </div>

                    {/* Similar trades success rate */}
                    <div style={{
                        padding: '10px 14px', borderRadius: 10, marginBottom: 10,
                        background: 'var(--bg-secondary)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                            <BarChart3 size={14} style={{ color: 'var(--text-muted)' }} />
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Similar Trade Success Rate</span>
                        </div>
                        <div style={{ width: '100%', height: 10, borderRadius: 5, background: 'rgba(148,163,184,0.15)' }}>
                            <div style={{
                                width: `${analysis.similar_trades_success_rate}%`, height: '100%', borderRadius: 5,
                                background: analysis.similar_trades_success_rate > 60 ? '#22c55e' : analysis.similar_trades_success_rate > 40 ? '#f59e0b' : '#ef4444',
                                transition: 'width 1s ease',
                            }} />
                        </div>
                        <p style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 4, textAlign: 'center' }}>
                            {analysis.similar_trades_success_rate}% of similar trades were profitable
                        </p>
                    </div>

                    {/* Recommendation */}
                    <div style={{
                        padding: '10px 14px', borderRadius: 10,
                        background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                            <Lightbulb size={14} style={{ color: '#f59e0b' }} />
                            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: 0.5 }}>Recommendation</span>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{analysis.recommendation}</p>
                    </div>
                </>
            )}
        </div>
    )
}

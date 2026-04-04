// SignalCard.jsx – Main BUY/SELL/HOLD signal display card + Demo Trade button
import { useState, useEffect, useMemo } from 'react'
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts'
import { TrendingUp, TrendingDown, Minus, Shield, Brain, AlertTriangle, Zap, X, CheckCircle } from 'lucide-react'
import { executeTrade } from '../services/api.js'
import { addTradeToJournal } from './TradeJournal.jsx'
import { useToast } from './ToastProvider.jsx'

const DECISION_CONFIG = {
    BUY: {
        icon: TrendingUp,
        className: 'signal-buy',
        label: 'BUY',
        glow: 'rgba(5, 150, 105, 0.1)',
    },
    SELL: {
        icon: TrendingDown,
        className: 'signal-sell',
        label: 'SELL',
        glow: 'rgba(220, 38, 38, 0.1)',
    },
    HOLD: {
        icon: Minus,
        className: 'signal-hold',
        label: 'HOLD',
        glow: 'rgba(217, 119, 6, 0.08)',
    },
}

function GateRow({ label, passed, value }) {
    return (
        <div className="flex items-center justify-between py-1">
            <span className="text-xs text-text-secondary">{label}</span>
            <div className="flex items-center gap-2">
                {value && <span className="text-xs text-text-muted font-mono">{value}</span>}
                {passed !== undefined && (
                    <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-full ${passed === true
                            ? 'bg-accent-green/10 text-accent-green'
                            : passed === false
                                ? 'bg-accent-red/10 text-accent-red'
                                : 'bg-text-muted/10 text-text-muted'
                            }`}
                    >
                        {passed === true ? 'PASS' : passed === false ? 'FAIL' : '—'}
                    </span>
                )}
            </div>
        </div>
    )
}

function TradeHistoryChart({ pair }) {
    const [data, setData] = useState([]);
    
    useEffect(() => {
        const updateData = () => {
            try {
                const allTrades = JSON.parse(localStorage.getItem('fxguru_trade_journal') || '[]');
                const pairTrades = allTrades.filter(t => t.pair === pair).slice().reverse();
                
                let cumulative = 0;
                const chartData = pairTrades.map((t, idx) => {
                    cumulative += (t.pnl || 0);
                    return {
                        index: idx,
                        pnl: t.pnl,
                        balance: cumulative
                    };
                });
                
                if (chartData.length > 0) {
                    chartData.unshift({ index: -1, pnl: 0, balance: 0 });
                }
                
                setData(chartData);
            } catch (err) {
                console.error(err);
            }
        };
        
        updateData();
        
        window.addEventListener('journal-update', updateData);
        window.addEventListener('storage', updateData);
        return () => {
            window.removeEventListener('journal-update', updateData);
            window.removeEventListener('storage', updateData);
        };
    }, [pair]);

    if (data.length <= 1) {
        return null;
    }

    const isProfit = data[data.length - 1].balance >= 0;
    const color = isProfit ? '#10B981' : '#EF4444'; // accent-green / accent-red

    return (
        <div className="mb-5">
            <p className="text-xs text-text-secondary mb-2 uppercase tracking-wider">Trades P&L History ({pair.replace('_', '/')})</p>
            <div className="h-24 w-full bg-bg-secondary/30 rounded border border-white/5 overflow-hidden p-1">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id={`colorPnL-${pair}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                                <stop offset="95%" stopColor={color} stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <YAxis domain={['dataMin', 'dataMax']} hide={true} />
                        <Area 
                            type="monotone" 
                            dataKey="balance" 
                            stroke={color} 
                            strokeWidth={2}
                            fillOpacity={1} 
                            fill={`url(#colorPnL-${pair})`} 
                            isAnimationActive={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
            <div className="flex justify-between mt-1 px-1">
                <span className="text-[10px] text-text-muted">Start</span>
                <span className={`text-xs font-bold ${isProfit ? 'text-accent-green' : 'text-accent-red'}`}>
                    ${data[data.length - 1].balance.toFixed(2)}
                </span>
            </div>
        </div>
    );
}

// ── Trade Confirmation Modal ──────────────────────────────────────────────────
function TradeModal({ signal, onClose, onConfirm, loading, result }) {
    const isBuy = signal.decision === 'BUY'
    const colorClass = isBuy ? 'text-accent-green' : 'text-accent-red'
    const bgClass = isBuy ? 'bg-accent-green/10 border-accent-green/30' : 'bg-accent-red/10 border-accent-red/30'
    const [numTrades, setNumTrades] = useState(1)

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}>
            <div className="glass-card w-full max-w-sm p-6 animate-fade-in" style={{ border: '1px solid rgba(255,255,255,0.12)' }}>
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Zap size={18} className={colorClass} />
                        <span className="font-bold text-text-primary">Place Demo Trade</span>
                    </div>
                    <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
                        <X size={18} />
                    </button>
                </div>

                {/* Result state */}
                {result ? (
                    <div className={`rounded-xl p-4 mb-4 text-center ${result.ok ? 'bg-accent-green/10 border border-accent-green/30' : 'bg-accent-red/10 border border-accent-red/30'}`}>
                        {result.ok ? (
                            <>
                                <CheckCircle size={32} className="mx-auto mb-2 text-accent-green" />
                                <p className="font-bold text-accent-green">Trade Executed!</p>
                                <p className="text-xs text-text-secondary mt-1">OANDA trade ID: {result.tradeId || 'N/A'}</p>
                                <p className="text-xs text-text-muted mt-1">Practice account — no real money used.</p>
                            </>
                        ) : (
                            <>
                                <AlertTriangle size={32} className="mx-auto mb-2 text-accent-red" />
                                <p className="font-bold text-accent-red">Execution Failed</p>
                                <p className="text-xs text-text-secondary mt-1">{result.error}</p>
                            </>
                        )}
                        <button onClick={onClose} className="mt-3 px-4 py-2 rounded-xl bg-bg-secondary text-text-secondary text-sm hover:text-text-primary transition-colors">
                            Close
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Trade details */}
                        <div className={`rounded-xl p-4 mb-4 border ${bgClass}`}>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <p className="text-xs text-text-muted">Pair</p>
                                    <p className="font-bold font-mono text-text-primary">{signal.pair}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-text-muted">Direction</p>
                                    <p className={`font-bold ${colorClass}`}>{signal.decision}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-text-muted">Lot Size</p>
                                    <p className="font-mono text-text-primary text-sm">0.01 (micro)</p>
                                </div>
                                <div>
                                    <p className="text-xs text-text-muted">Risk:Reward</p>
                                    <p className="font-mono text-accent-blue text-sm">1:{signal.rr?.toFixed(1)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-text-muted">Stop Loss</p>
                                    <p className="font-mono text-accent-red text-sm">{signal.sl?.toFixed(5)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-text-muted">Take Profit</p>
                                    <p className="font-mono text-accent-green text-sm">{signal.tp?.toFixed(5)}</p>
                                </div>
                            </div>
                            
                            <div className="mt-4 pt-4 border-t border-text-muted/20 flex justify-between items-center">
                                <p className="text-xs text-text-muted">Number of Trades (1-50)</p>
                                <div className="flex items-center gap-3">
                                    <button onClick={() => setNumTrades(Math.max(1, numTrades - 1))} className="w-6 h-6 rounded-full bg-bg-secondary flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors">-</button>
                                    <span className="font-mono text-sm w-4 text-center text-text-primary">{numTrades}</span>
                                    <button onClick={() => setNumTrades(Math.min(50, numTrades + 1))} className="w-6 h-6 rounded-full bg-bg-secondary flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors">+</button>
                                </div>
                            </div>
                        </div>

                        {/* Disclaimer */}
                        <div className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 mb-4">
                            <AlertTriangle size={14} className="text-amber-400 mt-0.5 shrink-0" />
                            <p className="text-xs text-amber-300 leading-relaxed">
                                This will execute <strong>{numTrades} distinct simulated trades</strong> dynamically generating unique simulated P&L for your profile balance simulation.
                            </p>
                        </div>

                        {/* Buttons */}
                        <div className="flex gap-3">
                            <button
                                onClick={onClose}
                                className="flex-1 py-2.5 rounded-xl bg-bg-secondary text-text-secondary text-sm font-medium hover:text-text-primary transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => onConfirm(numTrades)}
                                disabled={loading}
                                className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all ${loading ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-90'} ${isBuy ? 'bg-accent-green text-bg-primary' : 'bg-accent-red text-white'}`}
                            >
                                {loading ? 'Placing...' : `Confirm ${signal.decision}`}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

// ── Main SignalCard ────────────────────────────────────────────────────────────
export default function SignalCard({ signal, loading }) {
    const [showModal, setShowModal] = useState(false)
    const [tradeLoading, setTradeLoading] = useState(false)
    const [tradeResult, setTradeResult] = useState(null)
    const addToast = useToast()

    const handleTrade = async (numTrades = 1) => {
        setTradeLoading(true)
        setTradeResult(null)
        try {
            const res = await executeTrade(signal.pair, signal.decision, signal.sl, signal.tp, numTrades)
            const tradeId = res?.trades?.[0]?.oanda_trade_id || res?.trade?.oanda_trade_id || 'simulated'
            setTradeResult({ ok: true, tradeId })

            // Log to journal
            const tradesToLog = res?.trades?.length > 0 ? res.trades : [{
                pair: signal.pair,
                direction: signal.decision,
                entry_price: signal.entry_price || signal.sl,
                sl: signal.sl,
                tp: signal.tp,
                rr_achieved: signal.rr,
                status: 'executed',
                pnl: res?.total_pnl || 0,
            }];

            tradesToLog.forEach(t => {
                addTradeToJournal({
                    pair: t.pair || signal.pair,
                    direction: t.direction || signal.decision,
                    entry: t.entry_price || signal.entry_price || signal.sl,
                    sl: t.sl || signal.sl,
                    tp: t.tp || signal.tp,
                    rr: t.rr_achieved || signal.rr,
                    confidence: signal.ensemble_probability,
                    status: t.status || 'executed',
                    pnl: t.pnl || 0,
                });
            });

            addToast({
                type: 'success',
                title: `${numTrades > 1 ? numTrades : 'Trade'} Executed — ${signal.decision}`,
                message: `${signal.pair} at R:R 1:${signal.rr?.toFixed(1)} | Total P&L: $${res?.total_pnl?.toFixed(2) || '0.00'}`,
            })
        } catch (err) {
            const msg = err?.response?.data?.detail || err.message || 'Unknown error'
            setTradeResult({ ok: false, error: msg })
            addToast({
                type: 'info',
                title: 'Trade Failed',
                message: msg,
            })
        } finally {
            setTradeLoading(false)
        }
    }

    const closeModal = () => {
        setShowModal(false)
        setTradeResult(null)
    }

    if (loading) {
        return (
            <div className="glass-card p-6 animate-pulse">
                <div className="h-20 bg-bg-hover rounded-xl mb-4" />
                <div className="h-4 bg-bg-hover rounded w-3/4 mb-2" />
                <div className="h-4 bg-bg-hover rounded w-1/2" />
            </div>
        )
    }

    if (!signal) {
        return (
            <div className="glass-card p-6 text-center text-text-muted">
                <Brain size={40} className="mx-auto mb-3 opacity-40" />
                <p>Awaiting signal…</p>
            </div>
        )
    }

    const decision = signal.decision || 'HOLD'
    const cfg = DECISION_CONFIG[decision] || DECISION_CONFIG.HOLD
    const Icon = cfg.icon
    const prob = (signal.ensemble_probability || 0) * 100
    const gateLog = signal.gate_log || {}
    const canTrade = decision === 'BUY' || decision === 'SELL'

    return (
        <>
            {showModal && (
                <TradeModal
                    signal={signal}
                    onClose={closeModal}
                    onConfirm={handleTrade}
                    loading={tradeLoading}
                    result={tradeResult}
                />
            )}

            <div className="glass-card p-6 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <p className="text-xs text-text-secondary tracking-widest uppercase">AI Signal</p>
                        <p className="text-sm text-text-muted font-mono mt-0.5">{signal.pair}</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="pulse-dot" />
                        <span className="text-xs text-accent-green">LIVE</span>
                    </div>
                </div>

                {/* Decision badge */}
                <div
                    className={`rounded-2xl p-5 text-center mb-6 ${cfg.className}`}
                    style={{ boxShadow: `0 0 40px ${cfg.glow}` }}
                >
                    <Icon size={36} className="mx-auto mb-2" />
                    <p className="text-3xl font-black tracking-widest">{cfg.label}</p>
                    <p className="text-sm mt-1 opacity-80">
                        Confidence: {prob.toFixed(1)}%
                    </p>
                </div>

                {/* Confidence bar */}
                <div className="mb-5">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-text-secondary">Ensemble Probability</span>
                        <span className="text-text-primary font-mono">{signal.ensemble_probability?.toFixed(4)}</span>
                    </div>
                    <div className="confidence-bar">
                        <div
                            className="confidence-fill"
                            style={{
                                width: `${prob}%`,
                                background: `linear-gradient(90deg, #3B82F6, ${prob > 70 ? '#00D4AA' : '#F59E0B'})`,
                            }}
                        />
                    </div>
                    <div className="flex justify-between text-xs mt-1 text-text-muted">
                        <span>0%</span>
                        <span className="text-accent-gold">Threshold: {((signal.threshold_used || 0.7) * 100).toFixed(0)}%</span>
                        <span>100%</span>
                    </div>
                </div>

                {/* SL / TP / R:R */}
                <div className="grid grid-cols-3 gap-3 mb-5">
                    {[
                        { label: 'Stop Loss', value: signal.sl?.toFixed(5), color: 'text-accent-red' },
                        { label: 'Take Profit', value: signal.tp?.toFixed(5), color: 'text-accent-green' },
                        { label: 'Risk:Reward', value: `1:${signal.rr?.toFixed(1)}`, color: 'text-accent-blue' },
                    ].map(({ label, value, color }) => (
                        <div key={label} className="bg-bg-secondary rounded-xl p-3 text-center">
                            <p className="text-xs text-text-muted mb-1">{label}</p>
                            <p className={`text-sm font-bold font-mono ${color}`}>{value || '—'}</p>
                        </div>
                    ))}
                </div>

                {/* Model contributions */}
                {signal.model_contributions && (
                    <div className="mb-5">
                        <p className="text-xs text-text-secondary mb-2 uppercase tracking-wider">Model Contributions</p>
                        {Object.entries(signal.model_contributions).map(([model, prob]) => (
                            <div key={model} className="flex items-center gap-2 mb-1">
                                <span className="text-xs text-text-muted w-24 capitalize">{model}</span>
                                <div className="flex-1 confidence-bar">
                                    <div
                                        className="confidence-fill"
                                        style={{ width: `${prob * 100}%`, background: '#3B82F6' }}
                                    />
                                </div>
                                <span className="text-xs font-mono text-text-secondary w-12 text-right">
                                    {(prob * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Decision gates */}
                <TradeHistoryChart pair={signal.pair} />
                
                {Object.keys(gateLog).length > 0 && (
                    <div className="mb-5">
                        <p className="text-xs text-text-secondary mb-2 uppercase tracking-wider flex items-center gap-1">
                            <Shield size={12} /> Decision Gates
                        </p>
                        <div className="bg-bg-secondary rounded-xl px-4 py-2">
                            <GateRow label="Regime = Expansion" passed={gateLog.regime_ok} />
                            <GateRow label="Structure Bullish" passed={gateLog.structure_bullish} />
                            <GateRow label="Liquidity Sweep Below" passed={gateLog.liquidity_sweep_ok} />
                            <GateRow label="AI Probability" passed={gateLog.probability_ok} value={`${((signal.ensemble_probability || 0) * 100).toFixed(1)}%`} />
                            <GateRow label="RSI < 70" passed={gateLog.rsi_ok} value={signal.rsi?.toFixed(1)} />
                            <GateRow label="R:R ≥ 1:2" passed={gateLog.rr_ok} value={`1:${signal.rr?.toFixed(1)}`} />
                            <GateRow label="Risk Guardian" passed={gateLog.guardian_ok} value={gateLog.guardian_ok ? 'APPROVED' : 'BLOCKED'} />
                        </div>
                    </div>
                )}

                {/* ── Demo Trade Button ── */}
                {canTrade ? (
                    <button
                        onClick={() => setShowModal(true)}
                        className={`w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-95 ${decision === 'BUY'
                            ? 'bg-accent-green text-bg-primary shadow-lg shadow-accent-green/20'
                            : 'bg-accent-red text-white shadow-lg shadow-accent-red/20'}`}
                    >
                        <Zap size={15} />
                        📤 Place Demo Trade ({decision})
                    </button>
                ) : (
                    <div className="w-full py-3 rounded-xl text-center text-xs text-text-muted bg-bg-secondary border border-dashed border-text-muted/20">
                        Trade button activates on BUY or SELL signal
                    </div>
                )}

                <p className="text-xs text-text-muted mt-4 text-center font-mono">
                    {signal.timestamp ? new Date(signal.timestamp).toLocaleString() : '—'}
                </p>
            </div>
        </>
    )
}

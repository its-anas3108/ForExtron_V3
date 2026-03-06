// MonteCarloPanel.jsx – AI Market Simulator with probability cone visualization
import { useState, useRef, useEffect } from 'react'
import { Activity, Play, Target, ShieldAlert, Minus } from 'lucide-react'
import { runSimulation } from '../services/api.js'

function ProbBar({ label, value, color }) {
    return (
        <div style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 3, color: 'var(--text-secondary)' }}>
                <span>{label}</span>
                <span style={{ fontWeight: 700, color }}>{value}%</span>
            </div>
            <div style={{ width: '100%', height: 8, borderRadius: 4, background: 'var(--bg-secondary)' }}>
                <div style={{
                    width: `${Math.min(value, 100)}%`, height: '100%', borderRadius: 4,
                    background: color, transition: 'width 0.8s ease'
                }} />
            </div>
        </div>
    )
}

function PriceConeChart({ data }) {
    const canvasRef = useRef(null)

    useEffect(() => {
        if (!data || !canvasRef.current) return
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        const W = canvas.width = canvas.offsetWidth * 2
        const H = canvas.height = canvas.offsetHeight * 2
        ctx.scale(2, 2)
        const w = W / 2, h = H / 2

        ctx.clearRect(0, 0, w, h)

        const { cone_upper, cone_lower, cone_p90, cone_p10, median_path, best_path, worst_path, sampled_paths, sl, tp, entry_price } = data

        // Compute price bounds
        const allPrices = [...cone_upper, ...cone_lower, sl, tp, entry_price]
        const minP = Math.min(...allPrices) - (Math.max(...allPrices) - Math.min(...allPrices)) * 0.05
        const maxP = Math.max(...allPrices) + (Math.max(...allPrices) - Math.min(...allPrices)) * 0.05
        const range = maxP - minP || 0.001

        const padL = 55, padR = 10, padT = 15, padB = 25
        const chartW = w - padL - padR
        const chartH = h - padT - padB

        const px = (i, arr) => padL + (i / (arr.length - 1)) * chartW
        const py = (price) => padT + (1 - (price - minP) / range) * chartH

        // Grid lines
        ctx.strokeStyle = 'rgba(148,163,184,0.1)'
        ctx.lineWidth = 0.5
        for (let i = 0; i < 5; i++) {
            const y = padT + (i / 4) * chartH
            ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke()
            const price = maxP - (i / 4) * range
            ctx.fillStyle = 'var(--text-muted)'
            ctx.font = '9px monospace'
            ctx.textAlign = 'right'
            ctx.fillText(price.toFixed(4), padL - 5, y + 3)
        }

        // 5-95% cone (outer)
        if (cone_upper && cone_lower) {
            ctx.fillStyle = 'rgba(59,130,246,0.06)'
            ctx.beginPath()
            for (let i = 0; i < cone_upper.length; i++) ctx.lineTo(px(i, cone_upper), py(cone_upper[i]))
            for (let i = cone_lower.length - 1; i >= 0; i--) ctx.lineTo(px(i, cone_lower), py(cone_lower[i]))
            ctx.closePath(); ctx.fill()
        }

        // 10-90% cone (inner)
        if (cone_p90 && cone_p10) {
            ctx.fillStyle = 'rgba(59,130,246,0.1)'
            ctx.beginPath()
            for (let i = 0; i < cone_p90.length; i++) ctx.lineTo(px(i, cone_p90), py(cone_p90[i]))
            for (let i = cone_p10.length - 1; i >= 0; i--) ctx.lineTo(px(i, cone_p10), py(cone_p10[i]))
            ctx.closePath(); ctx.fill()
        }

        // Sampled paths (faint)
        if (sampled_paths) {
            sampled_paths.forEach(path => {
                ctx.strokeStyle = 'rgba(148,163,184,0.12)'
                ctx.lineWidth = 0.5
                ctx.beginPath()
                for (let i = 0; i < path.length; i++) ctx.lineTo(px(i, path), py(path[i]))
                ctx.stroke()
            })
        }

        // Worst path
        if (worst_path) {
            ctx.strokeStyle = 'rgba(239,68,68,0.5)'
            ctx.lineWidth = 1
            ctx.setLineDash([3, 3])
            ctx.beginPath()
            for (let i = 0; i < worst_path.length; i++) ctx.lineTo(px(i, worst_path), py(worst_path[i]))
            ctx.stroke()
            ctx.setLineDash([])
        }

        // Best path
        if (best_path) {
            ctx.strokeStyle = 'rgba(34,197,94,0.5)'
            ctx.lineWidth = 1
            ctx.setLineDash([3, 3])
            ctx.beginPath()
            for (let i = 0; i < best_path.length; i++) ctx.lineTo(px(i, best_path), py(best_path[i]))
            ctx.stroke()
            ctx.setLineDash([])
        }

        // Median path (bold)
        if (median_path) {
            ctx.strokeStyle = '#3b82f6'
            ctx.lineWidth = 2
            ctx.beginPath()
            for (let i = 0; i < median_path.length; i++) ctx.lineTo(px(i, median_path), py(median_path[i]))
            ctx.stroke()
        }

        // TP line
        ctx.strokeStyle = 'rgba(34,197,94,0.8)'
        ctx.lineWidth = 1
        ctx.setLineDash([6, 3])
        ctx.beginPath(); ctx.moveTo(padL, py(tp)); ctx.lineTo(w - padR, py(tp)); ctx.stroke()
        ctx.fillStyle = '#22c55e'
        ctx.font = 'bold 9px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(`TP ${tp.toFixed(4)}`, padL + 2, py(tp) - 4)

        // SL line
        ctx.strokeStyle = 'rgba(239,68,68,0.8)'
        ctx.beginPath(); ctx.moveTo(padL, py(sl)); ctx.lineTo(w - padR, py(sl)); ctx.stroke()
        ctx.fillStyle = '#ef4444'
        ctx.fillText(`SL ${sl.toFixed(4)}`, padL + 2, py(sl) + 12)

        // Entry line
        ctx.strokeStyle = 'rgba(148,163,184,0.5)'
        ctx.setLineDash([2, 2])
        ctx.beginPath(); ctx.moveTo(padL, py(entry_price)); ctx.lineTo(w - padR, py(entry_price)); ctx.stroke()
        ctx.setLineDash([])
        ctx.fillStyle = 'var(--text-muted)'
        ctx.fillText(`Entry ${entry_price.toFixed(4)}`, padL + 2, py(entry_price) - 4)

    }, [data])

    return (
        <div style={{ position: 'relative', width: '100%', height: 220, marginTop: 8 }}>
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
        </div>
    )
}

export default function MonteCarloPanel({ signal }) {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleSimulate = async () => {
        if (!signal || loading) return
        setLoading(true)
        try {
            const res = await runSimulation({
                pair: signal.pair || 'EUR_USD',
                direction: signal.decision || 'BUY',
                entry: signal.entry || signal.price || 1.0850,
                sl: signal.sl || 1.0820,
                tp: signal.tp || 1.0910,
                volatility: 0.08,
                num_simulations: 500,
                horizon_minutes: 120,
            })
            setResult(res)
        } catch (err) {
            console.error('Simulation error:', err)
        } finally {
            setLoading(false)
        }
    }

    // Auto-run when signal changes
    useEffect(() => {
        if (signal?.decision && signal.decision !== 'HOLD') {
            handleSimulate()
        }
    }, [signal?.decision, signal?.pair])

    return (
        <div className="glass-card p-4 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <Activity size={16} /> AI Market Simulator
                </h3>
                <button
                    onClick={handleSimulate}
                    disabled={loading || !signal}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all active:scale-95 disabled:opacity-50"
                    style={{ background: 'rgba(59,130,246,0.15)', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.3)' }}
                >
                    <Play size={12} />
                    {loading ? 'Simulating...' : 'Run Simulation'}
                </button>
            </div>

            {!result && !loading && (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
                    Generate a BUY or SELL signal to see the Monte Carlo probability cone.
                </p>
            )}

            {loading && (
                <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <Activity size={20} className="animate-spin" style={{ margin: '0 auto 8px', display: 'block' }} />
                    Running 500 simulations...
                </div>
            )}

            {result && !loading && (
                <>
                    {/* Probability outcomes */}
                    <div style={{ marginBottom: 16 }}>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
                            Outcome Probabilities ({result.num_simulations} simulations, {result.horizon_minutes}min)
                        </p>
                        <ProbBar label="Take Profit Hit" value={result.tp_probability} color="#22c55e" />
                        <ProbBar label="Breakeven" value={result.breakeven_probability} color="#f59e0b" />
                        <ProbBar label="Stop Loss Hit" value={result.sl_probability} color="#ef4444" />
                    </div>

                    {/* Price Cone Chart */}
                    <div>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
                            Price Probability Cone
                        </p>
                        <PriceConeChart data={result} />
                        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 6, fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                <span style={{ width: 12, height: 2, background: '#3b82f6', display: 'inline-block' }} /> Median
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                <span style={{ width: 12, height: 2, background: 'rgba(59,130,246,0.2)', display: 'inline-block' }} /> 90% Cone
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                <span style={{ width: 12, height: 2, background: '#22c55e', display: 'inline-block', borderTop: '1px dashed #22c55e' }} /> Best
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                <span style={{ width: 12, height: 2, background: '#ef4444', display: 'inline-block', borderTop: '1px dashed #ef4444' }} /> Worst
                            </span>
                        </div>
                    </div>

                    {/* Summary stats */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 12 }}>
                        <div className="glass-card" style={{ padding: '8px 10px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Direction</p>
                            <p style={{ fontSize: '0.85rem', fontWeight: 700, color: result.direction === 'BUY' ? '#22c55e' : '#ef4444' }}>{result.direction}</p>
                        </div>
                        <div className="glass-card" style={{ padding: '8px 10px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Median Exit</p>
                            <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>{result.median_final_price}</p>
                        </div>
                        <div className="glass-card" style={{ padding: '8px 10px', textAlign: 'center' }}>
                            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Horizon</p>
                            <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>{result.horizon_minutes}m</p>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

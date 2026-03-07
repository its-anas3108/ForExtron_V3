// CurrencyMap.jsx – Global AI Currency Intelligence Map
import { useState, useEffect } from 'react'
import { Globe, RefreshCw, TrendingUp, TrendingDown, Activity, AlertCircle, Maximize2 } from 'lucide-react'
import { getCurrencyStrength } from '../services/api.js'

export default function CurrencyMap() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    const fetchStrength = () => {
        setLoading(true)
        getCurrencyStrength()
            .then(res => {
                setData(res)
            })
            .catch(err => console.error("Error fetching currency strength:", err))
            .finally(() => setLoading(false))
    }

    // Refresh every 10 seconds to show "live" dynamic movement
    useEffect(() => {
        fetchStrength()
        const id = setInterval(fetchStrength, 10000)
        return () => clearInterval(id)
    }, [])

    if (loading && !data) {
        return (
            <div className="glass-card p-4 animate-fade-in flex flex-col items-center justify-center min-h-[400px]">
                <Globe className="animate-spin text-accent-blue mb-4 opacity-70" size={32} />
                <p className="text-sm font-semibold text-text-primary">Scanning Global Forex Basket...</p>
                <p className="text-xs text-text-muted mt-2">Calculating relative strength across 8 fiat currencies</p>
            </div>
        )
    }

    if (!data || !data.currencies) return null

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Header / Intro */}
            <div className="glass-card p-5 relative overflow-hidden">
                {/* Decorative background gradients */}
                <div className="absolute top-0 right-0 w-48 h-48 bg-accent-blue/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent-green/5 rounded-full blur-2xl -ml-16 -mb-16 pointer-events-none"></div>

                <div className="flex items-start gap-4 relative z-10">
                    <div className="w-12 h-12 rounded-xl bg-accent-blue/10 flex items-center justify-center shrink-0 border border-accent-blue/20">
                        <Globe className="text-accent-blue" size={24} />
                    </div>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-text-primary tracking-tight">Global Currency Intelligence Map</h2>
                            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-accent-blue/30 bg-accent-blue/10 text-[10px] uppercase font-bold text-accent-blue tracking-wider">
                                <Activity size={10} className="animate-pulse" /> Live
                            </span>
                        </div>
                        <p className="text-xs text-text-secondary leading-relaxed max-w-2xl">
                            Instead of analyzing a single pair, our AI scans the entire global ecosystem in real-time.
                            It calculates relative strength scores to detect which currencies are dominating the market and which are collapsing.
                        </p>
                    </div>
                    <button onClick={fetchStrength} className="ml-auto flex items-center gap-2 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-bg-secondary">
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                {/* Left Column: The Dashboard Heatmap */}
                <div className="lg:col-span-2 glass-card p-5">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-sm font-bold text-text-primary uppercase tracking-widest flex items-center gap-2">
                            <Maximize2 size={16} className="text-text-muted" /> Relative Strength Index
                        </h3>
                        <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">0 - 100 Scale</p>
                    </div>

                    <div className="space-y-4">
                        {data.currencies.map((curr, idx) => {
                            // Determine color based on strength
                            let barColor = 'bg-slate-500' // neutral
                            let textColor = 'text-slate-400'

                            if (curr.score >= 70) {
                                barColor = 'bg-accent-green'
                                textColor = 'text-accent-green'
                            } else if (curr.score >= 50) {
                                barColor = 'bg-accent-blue'
                                textColor = 'text-accent-blue'
                            } else if (curr.score <= 30) {
                                barColor = 'bg-accent-red'
                                textColor = 'text-accent-red'
                            } else {
                                barColor = 'bg-accent-gold'
                                textColor = 'text-accent-gold'
                            }

                            return (
                                <div key={curr.currency} className="flex items-center gap-4 group">
                                    {/* Rank & Currency Label */}
                                    <div className="w-16 flex items-center justify-between shrink-0">
                                        <span className="text-[10px] font-mono text-text-muted w-4">#{idx + 1}</span>
                                        <span className={`text-sm font-bold font-mono tracking-wider ${textColor}`}>
                                            {curr.currency}
                                        </span>
                                    </div>

                                    {/* Progress Bar Track */}
                                    <div className="flex-1 h-3 bg-bg-secondary rounded-full overflow-hidden relative border border-white/5">
                                        {/* Filled Bar */}
                                        <div
                                            className={`h-full ${barColor} transition-all duration-1000 ease-out`}
                                            style={{
                                                width: `${curr.score}%`,
                                                boxShadow: `0 0 10px ${barColor.replace('bg-', 'var(--')})`
                                            }}
                                        />
                                        {/* Center line indicator */}
                                        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-white/10 z-10" />
                                    </div>

                                    {/* Score Value */}
                                    <div className="w-12 text-right shrink-0">
                                        <span className="text-xs font-mono font-bold text-text-primary">{curr.score}%</span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Right Column: AI Insight & Trade Suggestions */}
                <div className="space-y-4">
                    {/* Top Pair Suggestion Summary */}
                    <div className="glass-card p-5 border-t-2 border-accent-blue">
                        <h4 className="text-[10px] uppercase font-bold tracking-widest text-text-muted mb-4">Market Leadership</h4>

                        <div className="flex justify-between items-center mb-6">
                            <div className="text-center">
                                <p className="text-[10px] text-text-secondary uppercase mb-1">Strongest</p>
                                <div className="flex items-center justify-center gap-1 text-accent-green font-bold text-xl font-mono">
                                    <TrendingUp size={18} /> {data.strongest}
                                </div>
                            </div>
                            <div className="text-text-muted font-bold text-sm">VS</div>
                            <div className="text-center">
                                <p className="text-[10px] text-text-secondary uppercase mb-1">Weakest</p>
                                <div className="flex items-center justify-center gap-1 text-accent-red font-bold text-xl font-mono">
                                    <TrendingDown size={18} /> {data.weakest}
                                </div>
                            </div>
                        </div>

                        <div className="bg-bg-secondary rounded-lg p-3 text-center border border-white/5">
                            <p className="text-[10px] uppercase tracking-wider text-text-muted mb-1 font-semibold">Suggested Trade Bias</p>
                            <p className="text-sm font-bold text-text-primary tracking-wide">
                                BUY {data.strongest}/{data.weakest}
                            </p>
                        </div>
                    </div>

                    {/* Deep AI Insight Text */}
                    <div className="glass-card p-5 relative overflow-hidden flex-1">
                        <div className="flex items-center gap-2 mb-3">
                            <AlertCircle size={16} className="text-accent-gold" />
                            <h4 className="text-xs uppercase font-bold tracking-widest text-accent-gold">FXGuru Insight</h4>
                        </div>
                        <p className="text-sm text-text-secondary leading-relaxed relative z-10 italic">
                            "{data.insight}"
                        </p>
                    </div>
                </div>

            </div>
        </div>
    )
}

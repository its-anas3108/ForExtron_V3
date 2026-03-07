// LiquidityMap.jsx – AI Liquidity & Pressure Map (Forex Order Book Alternative)
import { useState, useEffect } from 'react'
import { Layers, RefreshCw, AlertTriangle, ShieldAlert, ArrowDownCircle, ArrowUpCircle, Activity } from 'lucide-react'
import { getLiquidityMap } from '../services/api.js'

export default function LiquidityMap({ instrument }) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    const fetchLiquidity = () => {
        setLoading(true)
        getLiquidityMap(instrument)
            .then(res => {
                setData(res)
            })
            .catch(err => console.error("Error fetching liquidity map:", err))
            .finally(() => setLoading(false))
    }

    // Refresh every 5 seconds to simulate real-time order book movement
    useEffect(() => {
        fetchLiquidity()
        const id = setInterval(fetchLiquidity, 5000)
        return () => clearInterval(id)
    }, [instrument])

    if (loading && !data) {
        return (
            <div className="glass-card p-4 animate-fade-in flex flex-col items-center justify-center min-h-[400px]">
                <Layers className="animate-spin text-accent-blue mb-4 opacity-70" size={32} />
                <p className="text-sm font-semibold text-text-primary">Scanning Institutional Liquidity Pools...</p>
                <p className="text-xs text-text-muted mt-2">Estimating market depth for {instrument}</p>
            </div>
        )
    }

    if (!data || !data.levels) return null

    // Separate support and resistance for visualization
    const resistanceLevels = data.levels.filter(l => l.type === 'resistance').reverse() // Top down
    const supportLevels = data.levels.filter(l => l.type === 'support') // Top down

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Header / Intro */}
            <div className="glass-card p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-accent-red/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent-green/5 rounded-full blur-2xl -ml-10 -mb-10 pointer-events-none"></div>

                <div className="flex items-start gap-4 relative z-10">
                    <div className="w-12 h-12 rounded-xl bg-accent-blue/10 flex items-center justify-center shrink-0 border border-accent-blue/20">
                        <Layers className="text-accent-blue" size={24} />
                    </div>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <h2 className="text-base font-bold text-text-primary tracking-tight">AI Liquidity & Pressure Map</h2>
                            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-accent-blue/30 bg-accent-blue/10 text-[10px] uppercase font-bold text-accent-blue tracking-wider">
                                <Activity size={10} className="animate-pulse" /> Live Order Book
                            </span>
                        </div>
                        <p className="text-xs text-text-secondary leading-relaxed max-w-2xl">
                            Forex trades over-the-counter (OTC). Our AI calculates a synthetic Level-2 order book by tracking price velocity, volatility (ATR), and proximity to psychological numbers to estimate where resting liquidity and stop-loss clusters are sitting.
                        </p>
                    </div>
                    <button onClick={fetchLiquidity} className="ml-auto flex items-center gap-2 text-xs font-semibold text-text-muted hover:text-text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-bg-secondary">
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">

                {/* Left Column: Synthetic Depth Panel */}
                <div className="lg:col-span-3 glass-card p-5">
                    <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                        <h3 className="text-[10px] font-bold text-text-primary uppercase tracking-widest">
                            {instrument} Market Depth
                        </h3>
                        <div className="flex items-center gap-6 text-[10px] font-bold uppercase tracking-widest text-text-muted">
                            <span className="text-accent-green w-16 text-right">Buy Pres.</span>
                            <span className="w-16 text-center text-text-primary">Price</span>
                            <span className="text-accent-red w-16 text-left">Sell Pres.</span>
                        </div>
                    </div>

                    <div className="space-y-1 font-mono text-sm relative">
                        {/* Resistance Block */}
                        {resistanceLevels.map((level, idx) => (
                            <div key={`res-${idx}`} className="flex items-center justify-between group hover:bg-bg-secondary/50 rounded py-1 px-2 transition-colors">
                                {/* Buy Pressure (Left) */}
                                <div className="flex-1 flex justify-end pr-8 relative">
                                    <div className="absolute right-8 top-1/2 -translate-y-1/2 h-4 bg-accent-green/20 rounded-l" style={{ width: `${level.buy_pressure}%` }}></div>
                                    <span className="relative z-10 text-accent-green/80 text-xs">{level.buy_pressure}%</span>
                                </div>

                                {/* Price (Center) */}
                                <div className="w-24 text-center shrink-0 font-bold text-accent-red flex items-center justify-center gap-2">
                                    <ArrowDownCircle size={12} className="opacity-50" />
                                    {level.price}
                                </div>

                                {/* Sell Pressure (Right) */}
                                <div className="flex-1 flex justify-start pl-8 relative">
                                    <div className="absolute left-8 top-1/2 -translate-y-1/2 h-4 bg-accent-red/70 rounded-r shadow-[0_0_10px_rgba(239,68,68,0.3)] transition-all duration-300" style={{ width: `${level.sell_pressure}%` }}></div>
                                    <span className="relative z-10 text-white font-bold text-xs pl-2">{level.sell_pressure}%</span>
                                </div>
                            </div>
                        ))}

                        {/* Current Spread Divider */}
                        <div className="my-3 py-2 border-y border-white/10 flex items-center justify-center gap-4 bg-white/[0.02]">
                            <span className="h-px bg-white/20 w-16"></span>
                            <span className="text-xs uppercase tracking-widest font-bold text-text-secondary flex items-center gap-2">
                                <Activity size={12} className="text-accent-blue" />
                                Live Market Spread
                            </span>
                            <span className="h-px bg-white/20 w-16"></span>
                        </div>

                        {/* Support Block */}
                        {supportLevels.map((level, idx) => (
                            <div key={`sup-${idx}`} className="flex items-center justify-between group hover:bg-bg-secondary/50 rounded py-1 px-2 transition-colors">
                                {/* Buy Pressure (Left) */}
                                <div className="flex-1 flex justify-end pr-8 relative">
                                    <div className="absolute right-8 top-1/2 -translate-y-1/2 h-4 bg-accent-green/70 rounded-l shadow-[0_0_10px_rgba(34,197,94,0.3)] transition-all duration-300" style={{ width: `${level.buy_pressure}%` }}></div>
                                    <span className="relative z-10 text-white font-bold text-xs pr-2">{level.buy_pressure}%</span>
                                </div>

                                {/* Price (Center) */}
                                <div className="w-24 text-center shrink-0 font-bold text-accent-green flex items-center justify-center gap-2">
                                    {level.price}
                                    <ArrowUpCircle size={12} className="opacity-50" />
                                </div>

                                {/* Sell Pressure (Right) */}
                                <div className="flex-1 flex justify-start pl-8 relative">
                                    <div className="absolute left-8 top-1/2 -translate-y-1/2 h-4 bg-accent-red/20 rounded-r" style={{ width: `${level.sell_pressure}%` }}></div>
                                    <span className="relative z-10 text-accent-red/80 text-xs">{level.sell_pressure}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Column: AI Insight & Trade Suggestions */}
                <div className="space-y-4 lg:col-span-1 flex flex-col">

                    <div className="glass-card p-5 border-t-2 border-accent-gold flex-1">
                        <div className="flex items-center gap-2 mb-4">
                            <ShieldAlert size={16} className="text-accent-gold" />
                            <h4 className="text-[10px] uppercase font-bold tracking-widest text-accent-gold">Liquidity Alert</h4>
                        </div>

                        <p className="text-sm text-text-secondary leading-relaxed font-medium">
                            {data.insight}
                        </p>

                        <div className="mt-8 space-y-4">
                            <div>
                                <p className="text-[10px] uppercase tracking-wider text-text-muted mb-1 font-semibold">Strongest Buy Wall</p>
                                <div className="bg-bg-secondary/50 rounded border border-accent-green/20 px-3 py-2 text-sm font-mono text-accent-green font-bold flex items-center gap-2">
                                    <ArrowUpCircle size={14} />
                                    {data.strongest_support}
                                </div>
                            </div>

                            <div>
                                <p className="text-[10px] uppercase tracking-wider text-text-muted mb-1 font-semibold">Strongest Sell Wall</p>
                                <div className="bg-bg-secondary/50 rounded border border-accent-red/20 px-3 py-2 text-sm font-mono text-accent-red font-bold flex items-center gap-2">
                                    <ArrowDownCircle size={14} />
                                    {data.strongest_resistance}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}

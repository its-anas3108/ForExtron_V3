// RegimeBadge.jsx – Regime and structure bias display pills
import { TrendingUp, RefreshCw, Zap, AlertTriangle, HelpCircle, ArrowUp, ArrowDown, ArrowRight } from 'lucide-react'

const REGIME_STYLES = {
    expansion: { bg: 'bg-emerald-500/15 border-emerald-500/50', text: 'text-emerald-400', dot: 'bg-emerald-400', icon: TrendingUp },
    accumulation: { bg: 'bg-amber-500/15 border-amber-500/50', text: 'text-amber-400', dot: 'bg-amber-400', icon: RefreshCw },
    exhaustion: { bg: 'bg-red-500/15 border-red-500/50', text: 'text-red-400', dot: 'bg-red-400', icon: Zap },
    anomaly: { bg: 'bg-purple-500/15 border-purple-500/50', text: 'text-purple-400', dot: 'bg-purple-400', icon: AlertTriangle },
    unknown: { bg: 'bg-slate-500/15 border-slate-500/50', text: 'text-slate-400', dot: 'bg-slate-400', icon: HelpCircle },
}

const BIAS_STYLES = {
    bullish: { bg: 'bg-emerald-500/10 border-emerald-500/30', text: 'text-emerald-400', icon: ArrowUp },
    bearish: { bg: 'bg-red-500/10 border-red-500/30', text: 'text-red-400', icon: ArrowDown },
    neutral: { bg: 'bg-slate-500/10 border-slate-500/30', text: 'text-slate-400', icon: ArrowRight },
}

export default function RegimeBadge({ regime, structureBias, regimeConfidence }) {
    const rs = REGIME_STYLES[regime] || REGIME_STYLES.unknown
    const bs = BIAS_STYLES[structureBias] || BIAS_STYLES.neutral

    return (
        <div className="flex gap-3 flex-wrap">
            {/* Regime pill */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold ${rs.bg} ${rs.text}`}>
                <div className={`w-2 h-2 rounded-full animate-pulse ${rs.dot}`} />
                <span className="flex items-center gap-1.5"><rs.icon size={14} /> {(regime || 'unknown').charAt(0).toUpperCase() + (regime || 'unknown').slice(1)}</span>
                {regimeConfidence && (
                    <span className="opacity-60 text-xs font-normal">
                        {(regimeConfidence * 100).toFixed(0)}%
                    </span>
                )}
            </div>

            {/* Structure bias pill */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold ${bs.bg} ${bs.text}`}>
                <span className="flex items-center gap-1.5"><bs.icon size={14} /> {(structureBias || 'neutral').charAt(0).toUpperCase() + (structureBias || 'neutral').slice(1)} Structure</span>
            </div>
        </div>
    )
}

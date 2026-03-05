// Dashboard.jsx – Master dashboard page
import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Settings, Bell, Wifi, WifiOff } from 'lucide-react'
import SignalCard from '../components/SignalCard.jsx'
import RegimeBadge from '../components/RegimeBadge.jsx'
import LiveChart from '../components/LiveChart.jsx'
import AnalyticsPanel from '../components/AnalyticsPanel.jsx'
import ChatPanel from '../components/ChatPanel.jsx'
import AgentStatusBar from '../components/AgentStatusBar.jsx'
import { useWebSocket } from '../services/websocket.js'
import { getSignal, getPerformance, getAgentStatus, getSignalHistory, getInstruments } from '../services/api.js'

const INR_PAIRS = ['USD_INR', 'EUR_INR', 'GBP_INR']

export default function Dashboard() {
    const [instrument, setInstrument] = useState('EUR_USD')
    const [instruments, setInstruments] = useState([
        'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD',
        'USD_INR', 'EUR_INR', 'GBP_INR',
    ])
    const [signal, setSignal] = useState(null)
    const [performance, setPerformance] = useState(null)
    const [agentStatus, setAgentStatus] = useState(null)
    const [signalHistory, setSignalHistory] = useState([])
    const [candles, setCandles] = useState([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('chart') // 'chart' | 'analytics'
    const [lastUpdated, setLastUpdated] = useState(null)

    const { lastCandle, lastSignal, agentEvent, connected } = useWebSocket(instrument)

    // Fetch all data
    const fetchAll = useCallback(async () => {
        setLoading(true)
        try {
            const [sig, perf, agents, history] = await Promise.allSettled([
                getSignal(instrument),
                getPerformance(instrument),
                getAgentStatus(),
                getSignalHistory(instrument, 50),
            ])
            if (sig.status === 'fulfilled') setSignal(sig.value)
            if (perf.status === 'fulfilled') setPerformance(perf.value)
            if (agents.status === 'fulfilled') setAgentStatus(agents.value)
            if (history.status === 'fulfilled') setSignalHistory(history.value)
            setLastUpdated(new Date())
        } catch (e) {
            console.error('Fetch error:', e)
        } finally {
            setLoading(false)
        }
    }, [instrument])

    // Fetch instruments list
    useEffect(() => {
        getInstruments().then(d => {
            if (d?.instruments) setInstruments(d.instruments)
        }).catch(() => { })
    }, [])

    // Initial fetch + 30s polling
    useEffect(() => {
        fetchAll()
        const id = setInterval(fetchAll, 30000)
        return () => clearInterval(id)
    }, [fetchAll])

    // Live WebSocket updates
    useEffect(() => {
        if (lastCandle) setCandles(prev => [...prev.slice(-99), lastCandle])
    }, [lastCandle])

    useEffect(() => {
        if (lastSignal) { setSignal(lastSignal); setSignalHistory(prev => [lastSignal, ...prev.slice(0, 49)]) }
    }, [lastSignal])

    useEffect(() => {
        if (agentEvent) setAgentStatus(agentEvent)
    }, [agentEvent])

    const isInr = INR_PAIRS.includes(instrument)

    return (
        <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)' }}>
            {/* ── Top Navigation Bar ──────────────────────────────────────────── */}
            <nav className="border-b border-slate-200 px-6 py-3 flex items-center justify-between backdrop-blur-lg sticky top-0 z-50"
                style={{ background: 'rgba(255, 255, 255, 0.95)' }}>
                {/* Logo */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-green to-accent-blue flex items-center justify-center">
                        <span className="text-bg-primary font-black text-sm">FX</span>
                    </div>
                    <div>
                        <span className="gradient-text font-black text-lg tracking-tight">FXGuru Pro</span>
                        <p className="text-xs text-text-muted -mt-0.5">Institutional AI Platform</p>
                    </div>
                </div>

                {/* Instrument selector */}
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <select
                            value={instrument}
                            onChange={e => setInstrument(e.target.value)}
                            className="bg-bg-card border border-slate-200 rounded-xl px-4 py-2 text-sm text-text-primary font-mono focus:border-accent-green/40 focus:outline-none appearance-none pr-8 cursor-pointer"
                        >
                            <optgroup label="Major Pairs">
                                {instruments.filter(i => !INR_PAIRS.includes(i)).map(i => (
                                    <option key={i} value={i}>{i}</option>
                                ))}
                            </optgroup>
                            <optgroup label="INR Pairs 🇮🇳">
                                {instruments.filter(i => INR_PAIRS.includes(i)).map(i => (
                                    <option key={i} value={i}>{i}</option>
                                ))}
                            </optgroup>
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                            <span className="text-text-muted text-xs">▾</span>
                        </div>
                    </div>

                    {isInr && (
                        <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400">
                            🇮🇳 INR
                        </span>
                    )}

                    {/* Connection status */}
                    <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full ${connected
                        ? 'bg-accent-green/10 text-accent-green'
                        : 'bg-accent-red/10 text-accent-red'
                        }`}>
                        {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
                        {connected ? 'Live' : 'Offline'}
                    </div>

                    <button
                        onClick={fetchAll}
                        className="p-2 rounded-xl text-text-secondary hover:text-accent-green hover:bg-accent-green/10 transition-colors"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </nav>

            {/* ── Main Content ─────────────────────────────────────────────────── */}
            <div className="p-4 lg:p-6 space-y-4">

                {/* Agent Status Bar */}
                <AgentStatusBar agentStatus={agentStatus} />

                {/* Regime + structure badges */}
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <RegimeBadge
                        regime={signal?.regime}
                        structureBias={signal?.structure_bias}
                        regimeConfidence={signal?.regime_confidence}
                    />
                    {lastUpdated && (
                        <p className="text-xs text-text-muted">
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </p>
                    )}
                </div>

                {/* Main grid */}
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-4">
                    {/* Left column */}
                    <div className="space-y-4">
                        {/* Tab selector */}
                        <div className="flex gap-1 bg-bg-secondary rounded-xl p-1 w-fit">
                            {['chart', 'analytics'].map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize ${activeTab === tab
                                        ? 'bg-bg-card text-text-primary shadow'
                                        : 'text-text-muted hover:text-text-secondary'
                                        }`}
                                >
                                    {tab === 'chart' ? '📈 Chart' : '📊 Analytics'}
                                </button>
                            ))}
                        </div>

                        {activeTab === 'chart' ? (
                            <LiveChart candles={candles} signal={signal} />
                        ) : (
                            <AnalyticsPanel performance={performance} signalHistory={signalHistory} />
                        )}

                        {/* Chat panel (bottom on small screens) */}
                        <div className="xl:hidden">
                            <ChatPanel instrument={instrument} />
                        </div>
                    </div>

                    {/* Right column */}
                    <div className="space-y-4">
                        <SignalCard signal={signal} loading={loading} />

                        {/* INR context card */}
                        {isInr && (
                            <div className="glass-card p-4 border border-amber-500/20">
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">🇮🇳</span>
                                    <div>
                                        <p className="text-sm font-semibold text-amber-400 mb-1">INR Pair Mode</p>
                                        <p className="text-xs text-text-secondary leading-relaxed">
                                            {instrument} uses poll-based data feed (10s interval). Monitor RBI policy,
                                            USD demand, and oil prices for macro context. INR pairs may have wider spreads
                                            and lower liquidity vs major pairs.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Chat panel (large screens) */}
                        <div className="hidden xl:block">
                            <ChatPanel instrument={instrument} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="border-t border-slate-200 px-6 py-3 text-center text-xs text-text-muted">
                FXGuru Pro v2.0 · Institutional-grade AI · Not financial advice · Data via OANDA API
            </footer>
        </div>
    )
}

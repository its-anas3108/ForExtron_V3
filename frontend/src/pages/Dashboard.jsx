// Dashboard.jsx – Master dashboard page
import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Settings, Bell, Wifi, WifiOff, TrendingUp, TrendingDown, Moon, Sun, LineChart, BarChart2, BookOpen, MapPin, Activity, Newspaper, Repeat, Eye, Clock, Globe, Layers, User, LogOut } from 'lucide-react'
import SignalCard from '../components/SignalCard.jsx'
import RegimeBadge from '../components/RegimeBadge.jsx'
import LiveChart from '../components/LiveChart.jsx'
import AnalyticsPanel from '../components/AnalyticsPanel.jsx'
import ChatPanel from '../components/ChatPanel.jsx'
import PriceTicker from '../components/PriceTicker.jsx'
import SignalTimeline from '../components/SignalTimeline.jsx'
import TradeJournal from '../components/TradeJournal.jsx'
import MonteCarloPanel from '../components/MonteCarloPanel.jsx'
import NewsPanel from '../components/NewsPanel.jsx'
import TradeReplayPanel from '../components/TradeReplayPanel.jsx'
import SignalIntelligence from '../components/SignalIntelligence.jsx'
import OpportunityRecovery from '../components/OpportunityRecovery.jsx'
import CurrencyMap from '../components/CurrencyMap.jsx'
import LiquidityMap from '../components/LiquidityMap.jsx'
import AccountSummary from './AccountSummary.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../components/ToastProvider.jsx'
import { useWebSocket } from '../services/websocket.js'
import { getSignal, getPerformance, getAgentStatus, getSignalHistory, getInstruments, triggerDemoSignal, getCandles } from '../services/api.js'

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
    const [activeTab, setActiveTab] = useState('account') // 'account' | 'chart' | 'analytics' | 'journal'
    const [lastUpdated, setLastUpdated] = useState(null)
    const [demoLoading, setDemoLoading] = useState(null)

    // Theme state
    const [isDark, setIsDark] = useState(() => {
        const saved = localStorage.getItem('fxguru_theme')
        return saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)
    })

    const { lastCandle, lastSignal, agentEvent, connected } = useWebSocket(instrument)
    const addToast = useToast()
    const { logout } = useAuth()

    // Apply dark mode
    useEffect(() => {
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark')
            localStorage.setItem('fxguru_theme', 'dark')
        } else {
            document.documentElement.removeAttribute('data-theme')
            localStorage.setItem('fxguru_theme', 'light')
        }
    }, [isDark])

    // Fetch all data
    const fetchAll = useCallback(async () => {
        setLoading(true)
        try {
            const [sig, perf, agents, history, initialCandles] = await Promise.allSettled([
                getSignal(instrument),
                getPerformance(instrument),
                getAgentStatus(),
                getSignalHistory(instrument, 50),
                getCandles(instrument, 100),
            ])
            if (sig.status === 'fulfilled') setSignal(sig.value)
            if (perf.status === 'fulfilled') setPerformance(perf.value)
            if (agents.status === 'fulfilled') setAgentStatus(agents.value)
            if (history.status === 'fulfilled') setSignalHistory(history.value)
            if (initialCandles.status === 'fulfilled') {
                const candleData = initialCandles.value
                setCandles(Array.isArray(candleData) ? candleData : (candleData?.candles || []))
            }
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
        if (lastSignal) {
            setSignal(lastSignal)
            setSignalHistory(prev => {
                // Check if signal already exists to prevent duplicate toasts
                if (prev[0] && prev[0].timestamp === lastSignal.timestamp) return prev;

                // Fire toast for new BUY/SELL signals
                if (lastSignal.decision === 'BUY' || lastSignal.decision === 'SELL') {
                    addToast({
                        type: lastSignal.decision.toLowerCase(),
                        title: `New ${lastSignal.decision} Signal`,
                        message: `${lastSignal.pair} at R:R 1:${lastSignal.rr?.toFixed(1)} (${(lastSignal.ensemble_probability * 100).toFixed(0)}% conf)`,
                    })
                }

                return [lastSignal, ...prev.slice(0, 49)]
            })
        }
    }, [lastSignal, addToast])

    useEffect(() => {
        if (agentEvent) setAgentStatus(agentEvent)
    }, [agentEvent])

    // Demo signal handler
    const handleDemoSignal = async (direction) => {
        setDemoLoading(direction)
        try {
            const sig = await triggerDemoSignal(instrument, direction)
            setSignal(sig)

            // Wait for WS to broadcast it, but if we want instant UI feedback, we push it
            // We just let the WS effect handle the toast, but push history for safety
            setSignalHistory(prev => {
                if (prev[0] && prev[0].timestamp === sig.timestamp) return prev;
                return [sig, ...prev.slice(0, 49)]
            })
            setLastUpdated(new Date())
        } catch (e) {
            console.error('Demo signal error:', e)
        } finally {
            setDemoLoading(null)
        }
    }

    const isInr = INR_PAIRS.includes(instrument)

    return (
        <div className="min-h-screen relative" style={{ background: 'var(--bg-primary)' }}>
            {/* ── Top Navigation Bar ──────────────────────────────────────────── */}
            <nav className="border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50 transition-colors"
                style={{ background: 'var(--nav-bg)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', borderColor: 'var(--border)' }}>
                {/* Logo */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-green to-accent-blue flex items-center justify-center">
                        <span className="text-white font-black text-sm">FX</span>
                    </div>
                    <div>
                        <span className="gradient-text font-black text-lg tracking-tight">ForeXtron</span>
                        <p className="text-xs text-text-muted -mt-0.5" style={{ color: 'var(--text-muted)' }}>Institutional AI Platform</p>
                    </div>
                </div>

                {/* Instrument selector & Controls */}
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <select
                            value={instrument}
                            onChange={e => setInstrument(e.target.value)}
                            className="rounded-xl px-4 py-2 text-sm font-mono focus:outline-none appearance-none pr-8 cursor-pointer transition-colors"
                            style={{
                                background: 'var(--bg-card)',
                                color: 'var(--text-primary)',
                                border: '1px solid var(--border)'
                            }}
                        >
                            <optgroup label="Major Pairs">
                                {instruments.filter(i => !INR_PAIRS.includes(i)).map(i => (
                                    <option key={i} value={i}>{i}</option>
                                ))}
                            </optgroup>
                            <optgroup label="INR Pairs">
                                {instruments.filter(i => INR_PAIRS.includes(i)).map(i => (
                                    <option key={i} value={i}>{i}</option>
                                ))}
                            </optgroup>
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                            <span style={{ color: 'var(--text-muted)' }} className="text-xs">▾</span>
                        </div>
                    </div>

                    {isInr && (
                        <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400">
                            <MapPin size={12} /> INR
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

                    {/* Dark Mode Toggle */}
                    <button
                        onClick={() => setIsDark(!isDark)}
                        className="p-2 rounded-xl transition-colors hover:bg-hover"
                        style={{ color: 'var(--text-secondary)' }}
                        title="Toggle Dark Mode"
                    >
                        {isDark ? <Sun size={16} /> : <Moon size={16} />}
                    </button>

                    {/* Logout Button */}
                    <button
                        onClick={logout}
                        className="p-2 rounded-xl transition-colors hover:bg-hover ml-1"
                        style={{ color: 'var(--accent-red)' }}
                        title="Sign Out"
                    >
                        <LogOut size={16} />
                    </button>

                    {/* Refresh */}
                    <button
                        onClick={fetchAll}
                        className="p-2 rounded-xl transition-colors hover:text-accent-green"
                        style={{ color: 'var(--text-secondary)' }}
                        title="Refresh Data"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    </button>

                    {/* Demo signal buttons */}
                    <div className="flex items-center gap-1.5 ml-1">
                        <button
                            onClick={() => handleDemoSignal('BUY')}
                            disabled={demoLoading !== null}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all active:scale-95 disabled:opacity-50"
                            style={{ background: 'rgba(5, 150, 105, 0.15)', color: 'var(--accent-green)', border: '1px solid rgba(5, 150, 105, 0.3)' }}
                        >
                            <TrendingUp size={13} />
                            {demoLoading === 'BUY' ? '...' : 'Demo BUY'}
                        </button>
                        <button
                            onClick={() => handleDemoSignal('SELL')}
                            disabled={demoLoading !== null}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all active:scale-95 disabled:opacity-50"
                            style={{ background: 'rgba(220, 38, 38, 0.15)', color: 'var(--accent-red)', border: '1px solid rgba(220, 38, 38, 0.3)' }}
                        >
                            <TrendingDown size={13} />
                            {demoLoading === 'SELL' ? '...' : 'Demo SELL'}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Price Ticker Bar */}
            <PriceTicker instruments={instruments} activeInstrument={instrument} onSelect={setInstrument} />

            {/* ── Main Content ─────────────────────────────────────────────────── */}
            <div className="p-4 lg:p-6 space-y-4">

                {/* Regime + structure badges */}
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <RegimeBadge
                        regime={signal?.regime}
                        structureBias={signal?.structure_bias}
                        regimeConfidence={signal?.regime_confidence}
                    />
                    {lastUpdated && (
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </p>
                    )}
                </div>

                {/* Main grid */}
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-4">
                    {/* Left column */}
                    <div className="space-y-4">
                        {/* Tab selector */}
                        <div className="flex gap-1 rounded-xl p-1 w-fit flex-wrap" style={{ background: 'var(--bg-secondary)' }}>
                            {['account', 'chart', 'analytics', 'journal', 'intelligence', 'simulator', 'news', 'recovery', 'global', 'liquidity', 'replay'].map(tab => {
                                const labels = {
                                    account: { text: 'Account', icon: User },
                                    chart: { text: 'Chart', icon: LineChart },
                                    analytics: { text: 'Analytics', icon: BarChart2 },
                                    journal: { text: 'Journal', icon: BookOpen },
                                    intelligence: { text: 'Intelligence', icon: Eye },
                                    simulator: { text: 'Simulator', icon: Activity },
                                    news: { text: 'News', icon: Newspaper },
                                    recovery: { text: 'Recovery', icon: Clock },
                                    global: { text: 'Global Map', icon: Globe },
                                    liquidity: { text: 'Liquidity', icon: Layers },
                                    replay: { text: 'Replay', icon: Repeat },
                                }
                                const Icon = labels[tab].icon
                                return (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize flex items-center gap-1.5 ${activeTab === tab
                                            ? 'shadow'
                                            : 'hover:opacity-80'
                                            }`}
                                        style={activeTab === tab
                                            ? { background: 'var(--bg-card)', color: 'var(--text-primary)' }
                                            : { color: 'var(--text-muted)' }
                                        }
                                    >
                                        <Icon size={16} /> {labels[tab].text}
                                    </button>
                                )
                            })}
                        </div>

                        {activeTab === 'account' && <AccountSummary />}
                        {activeTab === 'chart' && <LiveChart candles={candles} signal={signal} />}
                        {activeTab === 'analytics' && <AnalyticsPanel performance={performance} signalHistory={signalHistory} />}
                        {activeTab === 'journal' && <TradeJournal />}
                        {activeTab === 'intelligence' && <SignalIntelligence signal={signal} />}
                        {activeTab === 'simulator' && <MonteCarloPanel signal={signal} />}
                        {activeTab === 'news' && <NewsPanel instrument={instrument} />}
                        {activeTab === 'recovery' && <OpportunityRecovery instrument={instrument} />}
                        {activeTab === 'global' && <CurrencyMap />}
                        {activeTab === 'liquidity' && <LiquidityMap instrument={instrument} />}
                        {activeTab === 'replay' && <TradeReplayPanel signal={signal} signalHistory={signalHistory} />}

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
                                    <div className="mt-1 p-2 bg-amber-500/10 rounded-full text-amber-500">
                                        <MapPin size={24} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-amber-400 mb-1">INR Pair Mode</p>
                                        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                                            {instrument} uses poll-based data feed (10s interval). Monitor RBI policy,
                                            USD demand, and oil prices for macro context. INR pairs may have wider spreads
                                            and lower liquidity vs major pairs.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        <SignalTimeline signalHistory={signalHistory} />

                        {/* Chat panel (large screens) */}
                        <div className="hidden xl:block">
                            <ChatPanel instrument={instrument} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="border-t px-6 py-3 text-center text-xs" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
                ForeXtron v2.0 · Institutional-grade AI · Not financial advice · Data via OANDA API
            </footer>
        </div>
    )
}


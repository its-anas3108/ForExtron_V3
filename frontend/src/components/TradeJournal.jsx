// TradeJournal.jsx – Demo trade history with P&L tracking (localStorage)
import { useState, useEffect } from 'react'
import { Trash2, Download, BookOpen } from 'lucide-react'

const STORAGE_KEY = 'fxguru_trade_journal'

function loadTrades() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    } catch { return [] }
}

function saveTrades(trades) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trades))
}

export function addTradeToJournal(trade) {
    const trades = loadTrades()
    trades.unshift({
        id: Date.now(),
        time: new Date().toISOString(),
        pair: trade.pair,
        direction: trade.direction,
        entry: trade.entry,
        sl: trade.sl,
        tp: trade.tp,
        rr: trade.rr,
        confidence: trade.confidence,
        status: trade.status || 'open',
        pnl: trade.pnl || null,
        demo: true,
    })
    // Keep max 100
    if (trades.length > 100) trades.pop()
    saveTrades(trades)
    // Dispatch event so component re-renders
    window.dispatchEvent(new Event('journal-update'))
}

function formatTime(ts) {
    if (!ts) return '—'
    const d = new Date(ts)
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function TradeJournal() {
    const [trades, setTrades] = useState(loadTrades)

    useEffect(() => {
        const handler = () => setTrades(loadTrades())
        window.addEventListener('journal-update', handler)
        window.addEventListener('storage', handler)
        return () => {
            window.removeEventListener('journal-update', handler)
            window.removeEventListener('storage', handler)
        }
    }, [])

    const clearAll = () => {
        saveTrades([])
        setTrades([])
    }

    // Stats
    const total = trades.length
    const wins = trades.filter(t => t.pnl > 0).length
    const losses = trades.filter(t => t.pnl < 0).length
    const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : '—'
    const totalPnl = trades.reduce((sum, t) => sum + (t.pnl || 0), 0)

    return (
        <div className="glass-card p-4 animate-fade-in">
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    <BookOpen size={16} /> Trade Journal
                </h3>
                <div style={{ display: 'flex', gap: 8 }}>
                    {total > 0 && (
                        <button
                            onClick={clearAll}
                            style={{
                                background: 'none', border: 'none', cursor: 'pointer',
                                color: 'var(--text-muted)', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 4,
                            }}
                        >
                            <Trash2 size={12} /> Clear
                        </button>
                    )}
                </div>
            </div>

            {/* Stats row */}
            <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12,
            }}>
                {[
                    { label: 'Total', value: total, color: 'var(--text-primary)' },
                    { label: 'Wins', value: wins, color: 'var(--accent-green)' },
                    { label: 'Losses', value: losses, color: 'var(--accent-red)' },
                    { label: 'Win Rate', value: `${winRate}%`, color: 'var(--accent-blue)' },
                ].map(({ label, value, color }) => (
                    <div key={label} style={{
                        background: 'var(--bg-secondary)', borderRadius: 8, padding: '0.4rem',
                        textAlign: 'center',
                    }}>
                        <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>{label}</p>
                        <p style={{ fontSize: '0.9rem', fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</p>
                    </div>
                ))}
            </div>

            {/* Table */}
            {total === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    <p>No trades recorded yet</p>
                    <p style={{ fontSize: '0.65rem', marginTop: 4 }}>
                        Place a demo trade via the signal card to start tracking
                    </p>
                </div>
            ) : (
                <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                    <table className="journal-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Pair</th>
                                <th>Dir</th>
                                <th>Entry</th>
                                <th>SL</th>
                                <th>TP</th>
                                <th>R:R</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.slice(0, 30).map(t => (
                                <tr key={t.id}>
                                    <td style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                                        {formatTime(t.time)}
                                    </td>
                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                        {t.pair?.replace('_', '/')}
                                    </td>
                                    <td style={{
                                        fontWeight: 700,
                                        color: t.direction === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)',
                                    }}>
                                        {t.direction}
                                    </td>
                                    <td>{t.entry?.toFixed(5) || '—'}</td>
                                    <td style={{ color: 'var(--accent-red)' }}>{t.sl?.toFixed(5) || '—'}</td>
                                    <td style={{ color: 'var(--accent-green)' }}>{t.tp?.toFixed(5) || '—'}</td>
                                    <td style={{ color: 'var(--accent-blue)' }}>1:{t.rr?.toFixed(1) || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

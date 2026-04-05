// NewsPanel.jsx – AI News Impact Engine with live sentiment feed
import { useState, useEffect } from 'react'
import { Newspaper, TrendingUp, TrendingDown, Minus, RefreshCw, AlertTriangle, Landmark, Globe, BarChart3, Sparkles } from 'lucide-react'
import { getNewsFeed, getNewsImpact } from '../services/api.js'

const CATEGORY_ICONS = {
    'Central Bank': Landmark,
    'Economic Data': BarChart3,
    'Geopolitical': Globe,
    'Market Sentiment': TrendingUp,
}

const SENTIMENT_STYLES = {
    bullish: { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.3)', color: '#22c55e', icon: TrendingUp },
    bearish: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', color: '#ef4444', icon: TrendingDown },
    neutral: { bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.3)', color: '#94a3b8', icon: Minus },
}

function ImpactBar({ score }) {
    const color = score > 70 ? '#ef4444' : score > 50 ? '#f59e0b' : '#22c55e'
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 60, height: 5, borderRadius: 3, background: 'var(--bg-secondary)' }}>
                <div style={{ width: `${Math.min(score, 100)}%`, height: '100%', borderRadius: 3, background: color, transition: 'width 0.5s' }} />
            </div>
            <span style={{ fontSize: '0.65rem', fontWeight: 600, color }}>{score}</span>
        </div>
    )
}

function NewsEvent({ event }) {
    const style = SENTIMENT_STYLES[event.sentiment] || SENTIMENT_STYLES.neutral
    const CatIcon = CATEGORY_ICONS[event.category] || Newspaper
    const SentIcon = style.icon

    return (
        <div style={{
            padding: '10px 12px', borderRadius: 10, marginBottom: 8,
            background: style.bg, border: `1px solid ${style.border}`,
            transition: 'transform 0.2s',
        }}
            className="hover:scale-[1.01]"
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        <CatIcon size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>{event.category}</span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                            {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    <p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.35, marginBottom: 4 }}>
                        {event.headline}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{event.source}</span>
                        <ImpactBar score={event.impact_score} />
                    </div>
                </div>
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 3, padding: '3px 8px',
                    borderRadius: 6, fontSize: '0.65rem', fontWeight: 700,
                    background: style.bg, color: style.color, border: `1px solid ${style.border}`,
                    flexShrink: 0,
                }}>
                    <SentIcon size={11} /> {event.sentiment.charAt(0).toUpperCase() + event.sentiment.slice(1)}
                </div>
            </div>

            {/* Affected pairs */}
            {event.affected_pairs && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                    {Object.entries(event.affected_pairs).map(([pair, info]) => {
                        const pairStyle = SENTIMENT_STYLES[info.direction] || SENTIMENT_STYLES.neutral
                        const PairIcon = pairStyle.icon
                        return (
                            <span key={pair} style={{
                                fontSize: '0.6rem', padding: '2px 6px', borderRadius: 4,
                                background: pairStyle.bg, color: pairStyle.color, fontWeight: 600,
                                display: 'flex', alignItems: 'center', gap: 2,
                            }}>
                                <PairIcon size={9} /> {pair.replace('_', '/')}
                            </span>
                        )
                    })}
                </div>
            )}

            {/* AI Contribution Rationale */}
            {event.contribution && (
                <div style={{
                    marginTop: 8, padding: '8px 10px', borderRadius: 8,
                    background: 'rgba(56, 189, 248, 0.05)', border: '1px solid rgba(56, 189, 248, 0.15)',
                    display: 'flex', alignItems: 'flex-start', gap: 8
                }}>
                    <Sparkles size={12} style={{ color: '#38bdf8', marginTop: 2, flexShrink: 0 }} />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                        <strong style={{ color: '#38bdf8', fontWeight: 600 }}>ForeXtron:</strong> {event.contribution}
                    </p>
                </div>
            )}
        </div>
    )
}

export default function NewsPanel({ instrument }) {
    const [feed, setFeed] = useState([])
    const [impact, setImpact] = useState(null)
    const [loading, setLoading] = useState(false)

    const fetchData = async () => {
        setLoading(true)
        try {
            const [feedRes, impactRes] = await Promise.allSettled([
                getNewsFeed(50), // fetch more to ensure we have enough for today
                getNewsImpact(instrument || 'EUR_USD'),
            ])
            if (feedRes.status === 'fulfilled') {
                setFeed(feedRes.value.events || []);
            }
            if (impactRes.status === 'fulfilled') setImpact(impactRes.value)
        } catch (err) {
            console.error('News fetch error:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 30000)
        return () => clearInterval(interval)
    }, [instrument])

    return (
        <div className="glass-card p-4 animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 className="flex items-center gap-1.5" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    <Newspaper size={16} /> AI News Intelligence
                </h3>
                <button onClick={fetchData} disabled={loading}
                    className="p-1.5 rounded-lg transition-colors"
                    style={{ color: 'var(--text-muted)' }}>
                    <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            {/* Pair sentiment summary */}
            {impact && (
                <div style={{
                    display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 12,
                    padding: 10, borderRadius: 10, background: 'var(--bg-secondary)',
                }}>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>Bullish</p>
                        <p style={{ fontSize: '1rem', fontWeight: 800, color: '#22c55e' }}>{impact.bullish_score}%</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>Bearish</p>
                        <p style={{ fontSize: '1rem', fontWeight: 800, color: '#ef4444' }}>{impact.bearish_score}%</p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: 2 }}>Neutral</p>
                        <p style={{ fontSize: '1rem', fontWeight: 800, color: '#94a3b8' }}>{impact.neutral_score}%</p>
                    </div>
                </div>
            )}

            {/* Net sentiment badge */}
            {impact && (
                <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 12,
                    padding: '6px 12px', borderRadius: 8,
                    ...(() => {
                        const s = SENTIMENT_STYLES[impact.net_sentiment] || SENTIMENT_STYLES.neutral
                        return { background: s.bg, border: `1px solid ${s.border}`, color: s.color }
                    })(),
                }}>
                    <AlertTriangle size={13} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                        Net Sentiment for {(instrument || 'EUR_USD').replace('_', '/')}: {impact.net_sentiment.toUpperCase()}
                    </span>
                </div>
            )}

            {/* News feed list */}
            <div style={{ maxHeight: 380, overflowY: 'auto' }}>
                {feed.length === 0 && !loading && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
                        No news events available.
                    </p>
                )}
                {feed.map(event => (
                    <NewsEvent key={event.id} event={event} />
                ))}
            </div>
        </div>
    )
}

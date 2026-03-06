// PriceTicker.jsx – Live scrolling price ticker for all instruments
import { useState, useEffect, useRef } from 'react'
import { getPrices } from '../services/api.js'

export default function PriceTicker({ instruments = [], activeInstrument, onSelect }) {
    const [prices, setPrices] = useState({})
    const [prevPrices, setPrevPrices] = useState({})
    const [flashing, setFlashing] = useState({})

    // Fetch prices every 5 seconds
    useEffect(() => {
        let alive = true

        const fetchPrices = async () => {
            try {
                const data = await getPrices()
                if (!alive) return
                setPrevPrices(prev => ({ ...prev, ...prices }))
                setPrices(data.prices || {})

                // Set flash states
                const flashes = {}
                for (const [pair, info] of Object.entries(data.prices || {})) {
                    const prev = prices[pair]
                    if (prev && info.mid !== prev.mid) {
                        flashes[pair] = info.mid > prev.mid ? 'up' : 'down'
                    }
                }
                setFlashing(flashes)
                setTimeout(() => alive && setFlashing({}), 700)
            } catch (e) {
                // Silently fail; ticker will just show stale data
            }
        }

        fetchPrices()
        const id = setInterval(fetchPrices, 5000)
        return () => { alive = false; clearInterval(id) }
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    const displayPairs = instruments.length > 0
        ? instruments
        : Object.keys(prices)

    if (displayPairs.length === 0) return null

    return (
        <div className="ticker-bar">
            <div className="ticker-scroll">
                {displayPairs.map(pair => {
                    const info = prices[pair]
                    const isActive = pair === activeInstrument
                    const flash = flashing[pair]
                    const mid = info?.mid
                    const spread = info?.spread

                    return (
                        <div
                            key={pair}
                            className={`ticker-item ${isActive ? 'active' : ''}`}
                            onClick={() => onSelect?.(pair)}
                        >
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.7rem' }}>
                                {pair.replace('_', '/')}
                            </span>
                            <span
                                className={flash === 'up' ? 'price-flash-up' : flash === 'down' ? 'price-flash-down' : ''}
                                style={{ fontWeight: 700, color: 'var(--text-primary)' }}
                            >
                                {mid?.toFixed(pair.includes('JPY') ? 3 : 5) || '—'}
                            </span>
                            {spread != null && (
                                <span style={{
                                    fontSize: '0.6rem',
                                    color: spread > 3 ? 'var(--accent-gold)' : 'var(--text-muted)',
                                }}>
                                    {spread.toFixed(1)}p
                                </span>
                            )}
                            {flash === 'up' && <span style={{ color: 'var(--accent-green)', fontSize: '0.65rem' }}>▲</span>}
                            {flash === 'down' && <span style={{ color: 'var(--accent-red)', fontSize: '0.65rem' }}>▼</span>}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

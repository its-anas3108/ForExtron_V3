// LiveChart.jsx – Live candlestick-style chart with EMA overlays using Recharts
import {
    ComposedChart, Bar, Line, XAxis, YAxis, Tooltip,
    CartesianGrid, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import { useState } from 'react'

function formatTime(ts) {
    if (!ts) return ''
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ''
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

/**
 * Custom candlestick shape for Recharts Bar component.
 * We pass dataKey="range" where range is [low, high].
 * x, y, width, height are the bounding box for [low, high].
 */
function CandleShape(props) {
    const { x, y, width, height, payload } = props
    if (!payload || !payload.open || !payload.close) return null

    const { open, close, high, low } = payload
    const isBull = close >= open
    const color = isBull ? '#00D4AA' : '#FF4757'

    const priceRange = high - low
    // Avoid division by zero
    const pixelsPerPrice = priceRange > 0 ? (height / priceRange) : 0

    const openY = y + (high - open) * pixelsPerPrice
    const closeY = y + (high - close) * pixelsPerPrice
    
    const bodyTop = Math.min(openY, closeY)
    const bodyHeight = Math.max(Math.abs(closeY - openY), 2) // min 2px height
    
    const cx = x + width / 2

    return (
        <g>
            {/* Wick */}
            <line
                x1={cx} y1={y}
                x2={cx} y2={y + height}
                stroke={color}
                strokeWidth={1}
                opacity={0.8}
            />
            {/* Body */}
            <rect
                x={x + width * 0.15}
                y={bodyTop}
                width={width * 0.7}
                height={bodyHeight}
                fill={color}
                rx={1}
            />
        </g>
    )
}

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    const d = payload[0]?.payload || {}
    return (
        <div className="glass-card p-3 text-xs font-mono">
            <p className="text-text-secondary mb-2">{label}</p>
            <div className="space-y-1">
                <p>O: <span className="text-text-primary">{d.open?.toFixed(5)}</span></p>
                <p>H: <span className="text-accent-green">{d.high?.toFixed(5)}</span></p>
                <p>L: <span className="text-accent-red">{d.low?.toFixed(5)}</span></p>
                <p>C: <span className="text-text-primary">{d.close?.toFixed(5)}</span></p>
                {d.ema_10 && <p>EMA10: <span className="text-blue-400">{d.ema_10?.toFixed(5)}</span></p>}
                {d.ema_50 && <p>EMA50: <span className="text-purple-400">{d.ema_50?.toFixed(5)}</span></p>}
            </div>
        </div>
    )
}

export default function LiveChart({ candles = [], signal }) {
    const [showEma, setShowEma] = useState(true)

    // Process candles for chart
    const data = candles.slice(-60).map(c => ({
        time: formatTime(c.timestamp),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
        ema_10: c.ema_10 || null,
        ema_50: c.ema_50 || null,
        // Full range of candle for Bar bounding box
        range: [c.low, c.high],
        // Bull/Bear flag
        isBull: (c.close || 0) >= (c.open || 0),
    }))

    const yMin = data.length ? Math.min(...data.map(d => d.low).filter(v => v != null)) * 0.9995 : 0
    const yMax = data.length ? Math.max(...data.map(d => d.high).filter(v => v != null)) * 1.0005 : 1

    return (
        <div className="glass-card p-4 h-full min-h-[360px]">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text-primary">Live Chart</h3>
                <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{
                        background: 'rgba(0, 212, 170, 0.1)',
                        color: '#00D4AA',
                        border: '1px solid rgba(0, 212, 170, 0.3)',
                    }}>
                        {data.length} candles
                    </span>
                    <button
                        onClick={() => setShowEma(!showEma)}
                        className={`text-xs px-3 py-1 rounded-full border transition-colors ${showEma
                            ? 'border-accent-blue/50 text-accent-blue bg-accent-blue/10'
                            : 'border-text-muted/30 text-text-muted'
                            }`}
                    >
                        EMA Overlay
                    </button>
                </div>
            </div>

            {data.length === 0 ? (
                <div className="flex items-center justify-center h-64 text-text-muted text-sm">
                    <div className="text-center">
                        <div className="animate-pulse mb-2">📊</div>
                        Loading chart data…
                    </div>
                </div>
            ) : (
                <ResponsiveContainer width="100%" height={300}>
                    <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #E2E8F0)" opacity={0.4} />
                        <XAxis
                            dataKey="time"
                            tick={{ fill: 'var(--text-muted, #475569)', fontSize: 10 }}
                            axisLine={false}
                            tickLine={false}
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            domain={[yMin, yMax]}
                            tick={{ fill: 'var(--text-muted, #475569)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={v => typeof v === 'number' ? v.toFixed(4) : ''}
                            width={65}
                        />
                        <Tooltip content={<CustomTooltip />} />

                        {/* Candle bodies - custom shape for OHLC */}
                        <Bar dataKey="range" shape={<CandleShape />} isAnimationActive={false} />

                        {/* Close price line for visual continuity */}
                        <Line
                            dataKey="close"
                            stroke="var(--text-muted, #94a3b8)"
                            strokeWidth={1}
                            dot={false}
                            opacity={0.4}
                            name="Close"
                        />

                        {showEma && (
                            <>
                                <Line
                                    dataKey="ema_10"
                                    stroke="#3B82F6"
                                    strokeWidth={1.5}
                                    dot={false}
                                    name="EMA 10"
                                    connectNulls={true}
                                />
                                <Line
                                    dataKey="ema_50"
                                    stroke="#8B5CF6"
                                    strokeWidth={1.5}
                                    dot={false}
                                    name="EMA 50"
                                    connectNulls={true}
                                />
                            </>
                        )}

                        {/* SL/TP lines from signal */}
                        {signal?.sl && (
                            <ReferenceLine y={signal.sl} stroke="#FF4757" strokeDasharray="4 4" label={{ value: 'SL', fill: '#FF4757', fontSize: 10 }} />
                        )}
                        {signal?.tp && (
                            <ReferenceLine y={signal.tp} stroke="#00D4AA" strokeDasharray="4 4" label={{ value: 'TP', fill: '#00D4AA', fontSize: 10 }} />
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            )}
        </div>
    )
}

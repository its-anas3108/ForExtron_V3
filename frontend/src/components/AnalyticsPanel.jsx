// AnalyticsPanel.jsx – Equity curve, win rate, drawdown using Recharts
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'

const COLORS = ['#00D4AA', '#FF4757', '#F59E0B', '#3B82F6']

function MetricCard({ label, value, sub, color = 'text-text-primary' }) {
    return (
        <div className="bg-bg-secondary rounded-xl p-4">
            <p className="text-xs text-text-muted mb-1">{label}</p>
            <p className={`text-2xl font-black font-mono ${color}`}>{value}</p>
            {sub && <p className="text-xs text-text-muted mt-0.5">{sub}</p>}
        </div>
    )
}

export default function AnalyticsPanel({ performance, signalHistory }) {
    const p = performance || {}

    // Equity curve from signal history
    const equityData = signalHistory
        ? signalHistory.slice(-30).map((s, i) => ({
            t: i + 1,
            prob: Math.round((s.ensemble_probability || 0.5) * 100),
            decision: s.decision,
        }))
        : []

    // Win rate donut
    const pieData = [
        { name: 'Wins', value: p.winning_trades || 0 },
        { name: 'Losses', value: p.losing_trades || 0 },
    ]

    const winRate = p.win_rate ? `${(p.win_rate * 100).toFixed(1)}%` : '—'
    const drawdown = p.max_drawdown_pct ? `${(p.max_drawdown_pct).toFixed(2)}%` : '—'
    const expectancy = p.expectancy ? p.expectancy.toFixed(2) : '—'
    const sharpe = p.sharpe_ratio ? p.sharpe_ratio.toFixed(2) : '—'

    return (
        <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Analytics</h3>

            {/* Metric row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                <MetricCard label="Win Rate" value={winRate} color="text-accent-green" sub={`${p.total_trades || 0} trades`} />
                <MetricCard label="Max Drawdown" value={drawdown} color={(p.max_drawdown_pct || 0) > 1.5 ? 'text-accent-red' : 'text-accent-green'} />
                <MetricCard label="Expectancy" value={expectancy} color="text-accent-blue" sub="per trade" />
                <MetricCard label="Sharpe Ratio" value={sharpe} color={(p.sharpe_ratio || 0) > 1 ? 'text-accent-green' : 'text-accent-gold'} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Confidence timeline */}
                <div>
                    <p className="text-xs text-text-secondary mb-2 uppercase tracking-wider">Ensemble Confidence (last 30)</p>
                    <ResponsiveContainer width="100%" height={150}>
                        <LineChart data={equityData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
                            <XAxis dataKey="t" tick={{ fill: '#475569', fontSize: 9 }} axisLine={false} tickLine={false} />
                            <YAxis domain={[0, 100]} tick={{ fill: '#475569', fontSize: 9 }} axisLine={false} tickLine={false} unit="%" />
                            <Tooltip
                                contentStyle={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '11px' }}
                                formatter={(v) => [`${v}%`, 'Confidence']}
                            />
                            <Line type="monotone" dataKey="prob" stroke="#3B82F6" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Win/Loss donut */}
                <div>
                    <p className="text-xs text-text-secondary mb-2 uppercase tracking-wider">Win / Loss Distribution</p>
                    {(p.total_trades || 0) > 0 ? (
                        <ResponsiveContainer width="100%" height={150}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={60}
                                    paddingAngle={3} dataKey="value">
                                    {pieData.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '8px', fontSize: '11px' }} />
                                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-36 text-text-muted text-xs">
                            No trade history yet
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

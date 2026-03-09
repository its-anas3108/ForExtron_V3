import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DollarSign, Activity, Target, Layers } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export default function AccountSummary() {
    const { user } = useAuth();
    const [summary, setSummary] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAccountData = async () => {
            try {
                const token = localStorage.getItem('token');
                const [summaryRes, tradesRes] = await Promise.all([
                    axios.get(`${API_BASE_URL}/account/summary`, { headers: { Authorization: `Bearer ${token}` } }),
                    axios.get(`${API_BASE_URL}/account/trades`, { headers: { Authorization: `Bearer ${token}` } })
                ]);
                setSummary(summaryRes.data);
                setTrades(tradesRes.data);
            } catch (err) {
                console.error('Failed to fetch account info', err);
            } finally {
                setLoading(false);
            }
        };

        if (user) {
            fetchAccountData();
            // Start polling every 10 seconds for dynamic updates
            const pollId = setInterval(fetchAccountData, 10000);
            return () => clearInterval(pollId);
        }
    }, [user]);

    if (loading) {
        return <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Loading account details...</div>;
    }

    if (!summary) return null;

    return (
        <div className="animate-fade-in" style={{ padding: '0 8px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 24 }}>
                Account Overview
            </h2>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
                <div className="glass-card" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{ padding: 10, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 10, color: '#10b981' }}>
                            <DollarSign size={20} />
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Account Balance</p>
                    </div>
                    <p style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        ${summary.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </p>
                </div>

                <div className="glass-card" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{ padding: 10, background: 'rgba(59, 130, 246, 0.1)', borderRadius: 10, color: '#3b82f6' }}>
                            <Layers size={20} />
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Total P&L</p>
                    </div>
                    <p style={{ fontSize: '1.8rem', fontWeight: 800, color: summary.total_pnl >= 0 ? '#10b981' : '#ef4444' }}>
                        {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toFixed(2)}
                    </p>
                </div>

                <div className="glass-card" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{ padding: 10, background: 'rgba(245, 158, 11, 0.1)', borderRadius: 10, color: '#f59e0b' }}>
                            <Target size={20} />
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Win Rate</p>
                    </div>
                    <p style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        {summary.win_rate.toFixed(1)}%
                    </p>
                </div>

                <div className="glass-card" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{ padding: 10, background: 'rgba(168, 85, 247, 0.1)', borderRadius: 10, color: '#a855f7' }}>
                            <Activity size={20} />
                        </div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Total Trades</p>
                    </div>
                    <p style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        {summary.total_trades}
                    </p>
                </div>
            </div>

            {/* Trade History Table */}
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>Recent Trade History</h3>
            <div className="glass-card" style={{ overflow: 'hidden' }}>
                {trades.length === 0 ? (
                    <p style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>No trades executed yet.</p>
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                                <th style={{ padding: '16px', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Date</th>
                                <th style={{ padding: '16px', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Pair</th>
                                <th style={{ padding: '16px', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Action</th>
                                <th style={{ padding: '16px', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Entry</th>
                                <th style={{ padding: '16px', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>PnL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                    <td style={{ padding: '16px', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                                        {new Date(trade.entry_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                                    </td>
                                    <td style={{ padding: '16px', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                        {trade.pair.replace('_', '/')}
                                    </td>
                                    <td style={{ padding: '16px', fontSize: '0.85rem', fontWeight: 700, color: trade.direction === 'BUY' ? '#10b981' : '#ef4444' }}>
                                        {trade.direction}
                                    </td>
                                    <td style={{ padding: '16px', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                                        {trade.entry_price}
                                    </td>
                                    <td style={{ padding: '16px', fontSize: '0.85rem', fontWeight: 700, color: trade.pnl >= 0 ? '#10b981' : '#ef4444' }}>
                                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl?.toFixed(2) || 'Open'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}

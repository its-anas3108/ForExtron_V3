// api.js – Axios service layer
import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 15000,
})

// ── Signals ──────────────────────────────────────────────────────────────────
export const getSignal = (pair) => api.get(`/signal/${pair}`).then(r => r.data)
export const getSignalHistory = (pair, limit = 50) => api.get(`/signals/history/${pair}?limit=${limit}`).then(r => r.data)
export const getInstruments = () => api.get('/instruments').then(r => r.data)

// ── Regime ───────────────────────────────────────────────────────────────────
export const getRegime = (pair) => api.get(`/regime/${pair}`).then(r => r.data)

// ── Performance ───────────────────────────────────────────────────────────────
export const getPerformance = (pair) => api.get(`/performance/${pair}`).then(r => r.data)
export const getTrades = (pair, limit = 20) => api.get(`/trades/${pair}?limit=${limit}`).then(r => r.data)

// ── Agents ────────────────────────────────────────────────────────────────────
export const getAgentStatus = () => api.get('/agents/status').then(r => r.data)
export const getAgentLogs = () => api.get('/agents/logs').then(r => r.data)

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendChat = (message, instrument = 'EUR_USD', sessionId = 'default') =>
    api.post('/chat', { message, instrument, session_id: sessionId }).then(r => r.data)
export const getChatHistory = (sessionId = 'default') =>
    api.get(`/chat/history/${sessionId}`).then(r => r.data)

// ── Execution (demo practice account only) ────────────────────────────────────
export const executeOrder = (payload) => api.post('/execute', payload).then(r => r.data)

/** Execute a demo trade — always uses 0.01 micro lot (OANDA practice account) */
export const executeTrade = (pair, direction, sl, tp) =>
    api.post('/execute', {
        pair,
        direction,
        lot_size: 0.01,
        sl,
        tp,
        confirmed: true,
    }).then(r => r.data)

/** Check if execution gateway is enabled */
export const getExecutionStatus = () => api.get('/execute/status').then(r => r.data)

// ── Education ─────────────────────────────────────────────────────────────────
/** Get a plain-English explanation of a Forex term */
export const explainTerm = (term) => api.get(`/explain/${term}`).then(r => r.data)

// ── Demo Signals ──────────────────────────────────────────────────────────────
/** Trigger a demo BUY or SELL signal for testing */
export const triggerDemoSignal = (pair, direction) =>
    api.post('/demo/signal', { pair, direction }).then(r => r.data)

// ── Live Prices ───────────────────────────────────────────────────────────────
/** Get live prices for all instruments (for the ticker) */
export const getPrices = () => api.get('/prices').then(r => r.data)

// ── Monte Carlo Simulator ─────────────────────────────────────────────────────
/** Run Monte Carlo simulation for a trade setup */
export const runSimulation = (payload) => api.post('/simulate', payload).then(r => r.data)

// ── News Impact Engine ────────────────────────────────────────────────────────
/** Get latest news feed */
export const getNewsFeed = (count = 10) => api.get(`/news/feed?count=${count}`).then(r => r.data)
/** Get news impact for a specific pair */
export const getNewsImpact = (pair) => api.get(`/news/impact/${pair}`).then(r => r.data)

// ── Trade Replay Engine ───────────────────────────────────────────────────────
/** Analyze a completed trade */
export const analyzeTradeReplay = (trade) => api.post('/replay/analyze', trade).then(r => r.data)

// ── XAI Signal Intelligence ───────────────────────────────────────────────────
/** Get XAI analysis for a signal */
export const getSignalIntelligence = (signal) => api.post('/xai/analyze', signal).then(r => r.data)

export default api

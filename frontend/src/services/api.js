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

export default api

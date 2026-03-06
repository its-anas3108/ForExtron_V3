// ToastProvider.jsx – Context-based toast notification system
import { createContext, useContext, useState, useCallback, useRef } from 'react'
import { X, TrendingUp, TrendingDown, CheckCircle, Info } from 'lucide-react'

const ToastContext = createContext(null)

let toastId = 0

const ICONS = {
    buy: TrendingUp,
    sell: TrendingDown,
    success: CheckCircle,
    info: Info,
}

const COLORS = {
    buy: 'text-accent-green',
    sell: 'text-accent-red',
    success: 'text-accent-green',
    info: 'text-accent-blue',
}

function Toast({ toast, onDismiss }) {
    const Icon = ICONS[toast.type] || Info
    const color = COLORS[toast.type] || 'text-accent-blue'
    const borderClass = `toast-${toast.type === 'buy' ? 'buy' : toast.type === 'sell' ? 'sell' : toast.type === 'success' ? 'success' : 'info'}`

    return (
        <div className={`toast ${borderClass} ${toast.exiting ? 'toast-exit' : ''}`}>
            <Icon size={18} className={`${color} flex-shrink-0`} />
            <div className="flex-1 min-w-0">
                <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {toast.title}
                </p>
                {toast.message && (
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                        {toast.message}
                    </p>
                )}
            </div>
            <button
                onClick={() => onDismiss(toast.id)}
                style={{ color: 'var(--text-muted)', cursor: 'pointer', background: 'none', border: 'none', padding: 4 }}
            >
                <X size={14} />
            </button>
        </div>
    )
}

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([])
    const timers = useRef({})

    const dismiss = useCallback((id) => {
        // Start exit animation
        setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t))
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 300)
        if (timers.current[id]) {
            clearTimeout(timers.current[id])
            delete timers.current[id]
        }
    }, [])

    const addToast = useCallback((toast) => {
        const id = ++toastId
        const newToast = { id, ...toast, exiting: false }

        setToasts(prev => {
            // Keep max 3 toasts
            const updated = [...prev, newToast]
            if (updated.length > 3) updated.shift()
            return updated
        })

        // Auto-dismiss after 5s
        timers.current[id] = setTimeout(() => dismiss(id), 5000)

        return id
    }, [dismiss])

    return (
        <ToastContext.Provider value={addToast}>
            {children}
            <div className="toast-container">
                {toasts.map(t => (
                    <Toast key={t.id} toast={t} onDismiss={dismiss} />
                ))}
            </div>
        </ToastContext.Provider>
    )
}

export function useToast() {
    const addToast = useContext(ToastContext)
    if (!addToast) throw new Error('useToast must be used within ToastProvider')
    return addToast
}

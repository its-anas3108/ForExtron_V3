// websocket.js – Custom React hook for WebSocket live feed
import { useEffect, useRef, useCallback, useState } from 'react'

export function useWebSocket(instrument) {
    const ws = useRef(null)
    const [lastCandle, setLastCandle] = useState(null)
    const [lastSignal, setLastSignal] = useState(null)
    const [agentEvent, setAgentEvent] = useState(null)
    const [connected, setConnected] = useState(false)

    const connect = useCallback(() => {
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
        const host = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? `${window.location.hostname}:8000`
            : window.location.host
        const url = `${proto}://${host}/ws/live/${instrument}`
        ws.current = new WebSocket(url)

        ws.current.onopen = () => setConnected(true)
        ws.current.onclose = () => {
            setConnected(false)
            // Auto-reconnect after 5s
            setTimeout(connect, 5000)
        }
        ws.current.onerror = () => ws.current.close()
        ws.current.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data)
                if (msg.type === 'candle') setLastCandle(msg.data)
                else if (msg.type === 'signal') setLastSignal(msg.data)
                else if (msg.type === 'agent_event') setAgentEvent(msg.data)
            } catch { }
        }
    }, [instrument])

    useEffect(() => {
        connect()
        return () => ws.current?.close()
    }, [connect])

    return { lastCandle, lastSignal, agentEvent, connected }
}

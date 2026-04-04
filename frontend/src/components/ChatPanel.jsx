// ChatPanel.jsx – Conversational AI panel
import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Zap } from 'lucide-react'
import { sendChat, getChatHistory } from '../services/api.js'


function ChatBubble({ role, message, timestamp }) {
    const isUser = role === 'user'
    return (
        <div className={`flex gap-2 mb-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {!isUser && (
                <div className="w-7 h-7 rounded-full bg-accent-green/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot size={14} className="text-accent-green" />
                </div>
            )}
            <div className={`max-w-xs sm:max-w-sm rounded-2xl px-4 py-3 text-sm ${isUser ? 'chat-user' : 'chat-ai'}`}>
                <p className="text-text-primary leading-relaxed whitespace-pre-wrap">{message}</p>
                {timestamp && (
                    <p className="text-xs text-text-muted mt-1 text-right">
                        {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                )}
            </div>
            {isUser && (
                <div className="w-7 h-7 rounded-full bg-bg-hover flex items-center justify-center flex-shrink-0 mt-1">
                    <User size={14} className="text-text-secondary" />
                </div>
            )}
        </div>
    )
}

export default function ChatPanel({ instrument }) {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            message: `Hello! I'm ForeXtron, your personal financial guide. I can explain our platform's key features like the Live Dashboard, Signal Timeline, and Trade Journal. I can also help you understand complex Forex terms or analyze any currency pair. How can I assist you today?`,
            timestamp: new Date().toISOString(),
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async (text = input) => {
        if (!text.trim() || loading) return
        const userMsg = { role: 'user', message: text.trim(), timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await sendChat(text.trim(), instrument || 'EUR_USD')
            setMessages(prev => [...prev, {
                role: 'assistant',
                message: res.response,
                timestamp: res.timestamp,
            }])
        } catch (err) {
            const detail = err?.response?.data?.detail || err?.response?.data?.response || err?.message || 'Unknown error'
            setMessages(prev => [...prev, {
                role: 'assistant',
                message: `Error: ${detail}`,
                timestamp: new Date().toISOString(),
            }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="glass-card flex flex-col h-[520px]">
            {/* Header */}
            <div className="flex items-center gap-3 p-4 border-b border-slate-200">
                <div className="w-8 h-8 rounded-full bg-accent-green/20 flex items-center justify-center">
                    <Bot size={16} className="text-accent-green" />
                </div>
                <div>
                    <p className="text-sm font-semibold text-text-primary">ForeXtron</p>
                    <p className="text-xs text-accent-green flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-accent-green rounded-full animate-pulse inline-block" />
                        Online
                    </p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
                {messages.map((m, i) => (
                    <ChatBubble key={i} {...m} />
                ))}
                {loading && (
                    <div className="flex gap-2 mb-3">
                        <div className="w-7 h-7 rounded-full bg-accent-green/20 flex items-center justify-center">
                            <Bot size={14} className="text-accent-green" />
                        </div>
                        <div className="chat-ai rounded-2xl px-4 py-3 flex items-center gap-1">
                            {[0, 1, 2].map(i => (
                                <div key={i} className="w-2 h-2 bg-accent-green/60 rounded-full animate-bounce"
                                    style={{ animationDelay: `${i * 0.15}s` }} />
                            ))}
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>


            {/* Input */}
            <div className="p-4 pt-2 border-t border-slate-200">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSend()}
                        placeholder="Ask about signals, regime, BoS, INR…"
                        className="flex-1 bg-bg-secondary rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder-text-muted border border-slate-200 focus:border-accent-green/40 focus:outline-none transition-colors"
                    />
                    <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || loading}
                        className="btn-glow w-10 h-10 flex items-center justify-center rounded-xl disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        <Send size={15} />
                    </button>
                </div>
            </div>
        </div>
    )
}

"""
llm_engine.py – Chatbot LLM interface.
Supports Gemini 1.5 Flash (default) and OpenAI GPT-4o-mini.
Upgraded to act as a friendly Forex educator with plain-English explanations.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FXGuru Edu — a friendly, expert Forex trading educator built into the FXGuru Pro platform.

Your TWO core jobs:
1. EXPLAIN FOREX CONCEPTS in plain, beginner-friendly language using real-world analogies.
2. EXPLAIN PLATFORM SIGNALS using the live system state data provided to you.

== HOW TO TEACH ==
- ALWAYS start with a simple, plain-English sentence. Then add a real-world analogy.
- THEN give the technical detail.
- Use emojis sparingly to make responses friendly (e.g. 📌, 💡, ⚠️).
- Keep responses concise — 3 to 6 sentences max unless a longer explanation is truly needed.
- Never use jargon without immediately explaining it in brackets.

== EXAMPLES ==
Q: What is a pip?
A: 📌 A pip is the smallest price movement in a currency pair — think of it like a "cent" for exchange rates. For most pairs like EUR/USD, 1 pip = 0.0001 (the 4th decimal place). So if EUR/USD moves from 1.0800 to 1.0801, it moved 1 pip. Your profit/loss per pip depends on your lot size.

Q: What is a Stop Loss?
A: 💡 A stop loss is your safety net — it automatically closes your trade if the price moves against you by a certain amount, so you don't lose more than you're comfortable with. Think of it like a speed governor on a car that prevents you from going too fast (losing too much). On this platform, SL is always calculated to keep your risk at 1-2% per trade.

Q: Why HOLD?
A: ⚠️ The system is on HOLD because not all 7 safety gates have passed. [Then cite the specific failed gate from gate_log data.]

== SIGNAL EXPLANATIONS ==
When explaining platform signals, always cite the specific gate(s) from the gate_log.
When explaining a HOLD signal, ALWAYS name which gate failed and why it matters.
For INR pairs, mention relevant macro factors: RBI policy, USD/INR correlation, oil prices.

Remember: You are talking to someone who may be completely new to Forex. Be their friendly guide."""

INTENT_EXAMPLES = {
    "explain_signal": "Why HOLD? Why BUY? Explain the signal. What is the current recommendation?",
    "show_performance": "Win rate? How are we doing? Show performance. What's the return?",
    "regime_inquiry": "What regime? Market conditions? Expansion or accumulation?",
    "explain_concept": "What is BoS? Explain liquidity sweep. What is ChoCH? What is FVG?",
    "risk_inquiry": "Risk status? Drawdown? How many trades today? Guardian status?",
    "trade_history": "Recent trades? Last trade result? Trade log?",
    "inr_inquiry": "USD INR? What about INR pairs? Indian Rupee signal?",
}


def _build_prompt(intent: str, context: dict, user_message: str) -> str:
    signal = context.get("latest_signal", {})
    regime = context.get("regime", "unknown")
    performance = context.get("performance", {})
    risk = context.get("risk_status", {})
    agent_health = context.get("agent_health", {})

    context_block = f"""
=== CURRENT SYSTEM STATE ===
Instrument: {signal.get('pair', 'N/A')}
Regime: {regime} (confidence: {signal.get('regime_confidence', 'N/A')})
Structure Bias: {signal.get('structure_bias', 'N/A')}
Ensemble Probability: {signal.get('ensemble_probability', 'N/A')}
Decision: {signal.get('decision', 'N/A')}
Threshold Used: {signal.get('threshold_used', 'N/A')}

Model Contributions: {signal.get('model_contributions', {})}
Gate Log: {signal.get('gate_log', {})}
SL: {signal.get('sl', 'N/A')} | TP: {signal.get('tp', 'N/A')} | R:R: {signal.get('rr', 'N/A')}

=== PERFORMANCE ===
Win Rate: {performance.get('win_rate', 'N/A')}%
Drawdown: {performance.get('max_drawdown_pct', 'N/A')}%
Expectancy: {performance.get('expectancy', 'N/A')}
Sharpe: {performance.get('sharpe_ratio', 'N/A')}

=== RISK GUARDIAN ===
Hold Mode: {risk.get('hold_mode', False)}
Trades Today: {risk.get('trades_today', 0)}/{risk.get('max_trades', 2)}
Daily Drawdown: {risk.get('drawdown_pct', 0)}%
"""

    return (
        f"{SYSTEM_PROMPT}\n\n{context_block}\n\n"
        f"=== USER QUESTION ===\n{user_message}\n\n"
        f"Provide a precise, structured answer using the context above."
    )


async def generate_response(intent: str, context: dict, user_message: str) -> str:
    prompt = _build_prompt(intent, context, user_message)

    result = None
    if settings.LLM_PROVIDER == "gemini":
        result = await _call_gemini(prompt)
    elif settings.LLM_PROVIDER == "openai":
        result = await _call_openai(prompt)

    # Fall back to rule-based response if LLM is unavailable/rate-limited
    if result is None:
        logger.info("LLM unavailable — using rule-based fallback response")
        return _fallback_response(intent, context, user_message)

    return result


async def _call_gemini(prompt: str) -> str:
    try:
        import asyncio
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL_GEMINI)
        # generate_content is synchronous — run in thread to avoid blocking the event loop
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()
    except Exception as e:
        err_str = str(e)
        logger.error(f"Gemini error: {err_str}")
        # On rate limit (429), return None to signal fallback should be used
        if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
            return None  # Caller will use fallback
        return f"⚠️ AI Assistant temporarily unavailable. Error: {err_str[:120]}"


async def _call_openai(prompt: str) -> str:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model=settings.LLM_MODEL_OPENAI,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"⚠️ AI Assistant temporarily unavailable."


# ── Forex Glossary (50+ terms, used as fallback) ──────────────────────────
FOREX_GLOSSARY = {
    "pip": "📌 A **pip** is the smallest standard price move in Forex — like a 'cent' for exchange rates. For most pairs (EUR/USD, GBP/USD), 1 pip = **0.0001** (4th decimal). For JPY pairs, 1 pip = 0.01. Example: EUR/USD moving from 1.0800 → 1.0801 = 1 pip move.",
    "spread": "📌 The **spread** is the difference between the BUY price (ask) and SELL price (bid) — it's the broker's fee. Think of it like a currency exchange booth at the airport that buys at ₹82 and sells at ₹83. The 1-rupee difference is the spread.",
    "leverage": "⚠️ **Leverage** lets you control a large trade with a small amount of money. A 100:1 leverage means ₹1,000 controls ₹100,000 worth of currency. It amplifies both profits AND losses, so use it carefully.",
    "lot": "📌 A **lot** is a standard unit of trade size. 1 Standard Lot = 100,000 units. 1 Mini Lot = 10,000 units. 1 Micro Lot = 1,000 units. FXGuru uses 0.01 lots (micro) for demo trades to keep risk minimal.",
    "lot size": "📌 **Lot size** controls how much currency you're buying/selling. Bigger lot size = bigger profit per pip AND bigger loss per pip. FXGuru defaults to 0.01 micro lots for safe demo trading.",
    "stop loss": "💡 A **stop loss (SL)** is your safety net — it automatically closes your trade if price moves against you beyond a set level, limiting your loss. Think of it like a circuit breaker. FXGuru calculates SL based on recent price structure and keeps risk at 1-2% per trade.",
    "sl": "💡 **SL (Stop Loss)** — see 'stop loss'.",
    "take profit": "💡 **Take Profit (TP)** is your target exit — when price reaches this level, your trade closes automatically with a profit. FXGuru sets TP to achieve at least a 1:2 risk-reward ratio.",
    "tp": "💡 **TP (Take Profit)** — see 'take profit'.",
    "risk reward": "📌 **Risk:Reward (R:R)** compares how much you risk vs. how much you could gain. A 1:2 R:R means you risk 10 pips to potentially earn 20 pips. FXGuru only signals when R:R is at least 1:2 (Gate 6).",
    "rr": "📌 **R:R (Risk:Reward ratio)** — see 'risk reward'.",
    "margin": "⚠️ **Margin** is the deposit your broker holds as collateral while your trade is open — like a security deposit. If your account balance drops too low relative to margin, you get a 'margin call' and trades close automatically.",
    "drawdown": "📌 **Drawdown** measures how much the account has fallen from its highest point. A 10% drawdown means after reaching a peak balance of ₹10,000, it dropped to ₹9,000. FXGuru's Risk Guardian halts trading if daily drawdown exceeds its limit.",
    "bos": "📌 **BoS (Break of Structure)** means price has closed beyond the last significant swing high (bullish BoS) or swing low (bearish BoS). It confirms the current trend is continuing. Think of it like a stock breaking above a resistance level.",
    "break of structure": "📌 **Break of Structure (BoS)** — price closes beyond a key swing point, confirming trend direction. Bullish BoS = higher high confirmed. Bearish BoS = lower low confirmed.",
    "choch": "📌 **ChoCH (Change of Character)** is the FIRST opposite Break of Structure after a trend. It's the earliest warning sign that the trend may be reversing. Example: In an uptrend, the first lower low is a ChoCH.",
    "change of character": "📌 **Change of Character (ChoCH)** — the first sign a trend is losing momentum and may reverse. FXGuru uses this to avoid trading in the wrong direction.",
    "fvg": "📌 **FVG (Fair Value Gap)** is a price imbalance zone created when price moves so fast that it skips over an area. Institutions tend to send price back to 'fill' the gap before continuing. FXGuru looks for FVGs as potential entry zones.",
    "fair value gap": "📌 **Fair Value Gap** — an area on the chart where price moved too quickly and left an imbalance. Price often returns to this zone. Also called an 'imbalance' or 'inefficiency'.",
    "order block": "📌 An **Order Block** is the last bearish candle before a bullish move (or last bullish candle before a bearish move) — it marks where institutions placed large orders. Price often revisits these zones.",
    "liquidity": "📌 **Liquidity** in Forex refers to clusters of stop-loss orders sitting above recent highs or below recent lows. Big institutions often push price into these areas to 'sweep' the stops and collect liquidity before reversing.",
    "liquidity sweep": "📌 A **Liquidity Sweep** happens when price briefly breaks above a recent high (or below a recent low) to trigger stop-losses, then quickly reverses. It's an institutional trap. FXGuru requires this as Gate 3 before a BUY signal.",
    "regime": "📌 **Market Regime** is the overall market condition: **Expansion** (trending, volatile — models active), **Accumulation** (range, building up), or **Exhaustion** (trend running out of steam). FXGuru only trades in Expansion regime.",
    "expansion": "📌 **Expansion regime** means the market is trending strongly with higher volatility. This is when FXGuru's DL models activate and BUY/SELL signals can be generated.",
    "accumulation": "📌 **Accumulation regime** — the market is range-bound, institutions are quietly building positions. FXGuru stays on HOLD during this phase.",
    "exhaustion": "📌 **Exhaustion regime** — the trend is running out of energy. FXGuru signals HOLD to avoid catching a reversal.",
    "ensemble": "📌 **Ensemble** means combining multiple AI models to make one final prediction. FXGuru combines 5 models: Logistic Regression (10%), DNN (20%), GRU (30%), CNN (25%), Transformer (15%) — their weighted average gives the ensemble probability.",
    "dnn": "📌 **DNN (Deep Neural Network)** — the AI model that looks at many technical features at once to predict price direction. It contributes 20% to FXGuru's ensemble.",
    "gru": "📌 **GRU (Gated Recurrent Unit)** — an AI model that understands sequences and patterns over time (like reading a story). It contributes 30% to the ensemble and is the highest-weighted model.",
    "cnn": "📌 **CNN (Convolutional Neural Network)** — originally designed for images, it detects patterns in price chart data. Contributes 25% to the ensemble.",
    "transformer": "📌 **Transformer** — the same AI architecture behind ChatGPT, used here to find long-range patterns in price history. Contributes 15% to FXGuru's ensemble.",
    "rsi": "📌 **RSI (Relative Strength Index)** measures whether a currency pair is overbought (>70) or oversold (<30). FXGuru checks RSI < 70 as Gate 5 to avoid buying into an overheated market.",
    "sharpe": "📌 **Sharpe Ratio** measures return relative to risk. A Sharpe above 1.0 is good, above 2.0 is excellent. It's calculated as: average return ÷ standard deviation of returns. Higher = better risk-adjusted performance.",
    "sharpe ratio": "📌 **Sharpe Ratio** — see 'sharpe'.",
    "expectancy": "📌 **Expectancy** is the average profit or loss you can expect per trade, accounting for win rate and average win/loss size. Positive expectancy = the system is profitable over many trades.",
    "win rate": "📌 **Win Rate** is the percentage of trades that close at profit. A 60% win rate means 6 out of 10 trades win. However, win rate alone isn't enough — you also need positive expectancy (wins bigger than losses).",
    "buy": "📌 A **BUY signal** means FXGuru's AI expects the price to go UP. All 7 decision gates must pass for a BUY. You'd profit if price rises above your entry and hits Take Profit.",
    "sell": "📌 A **SELL (short) signal** means FXGuru's AI expects price to go DOWN. You profit if price falls to your Take Profit level. Selling currencies you don't own is normal in Forex.",
    "hold": "📌 **HOLD** means one or more of FXGuru's 7 safety gates have failed — the trade conditions aren't right yet. Ask 'why HOLD?' to see exactly which gate(s) failed.",
    "drift": "📌 **Model Drift** means the AI's predictions have become less accurate over time, likely because market conditions changed. FXGuru's Drift Agent monitors this and triggers retraining when needed.",
    "threshold": "📌 **Dynamic Threshold** is the minimum probability required for FXGuru to issue a BUY signal. It adjusts between 0.65-0.75 based on market conditions. Higher threshold = the system is being more conservative.",
    "risk guardian": "📌 **Risk Guardian** is FXGuru's automated risk manager — it tracks daily drawdown and trade count. If daily losses exceed the limit or too many trades have been placed, it goes into Hold Mode to protect your account.",
    "supervisor": "📌 **Supervisor Agent** oversees all AI agents (Risk Guardian, Drift Agent, Threshold Agent) and coordinates the overall system health.",
    "pips": "📌 **Pips** is the plural of pip. See 'pip' for a full explanation.",
    "candle": "📌 A **candlestick (candle)** is a chart element showing the open, high, low, and close price for a time period. Green candles = price closed higher. Red candles = price closed lower.",
    "oanda": "📌 **OANDA** is the Forex broker connected to this platform. Your OANDA Practice account uses demo money — no real funds are at risk.",
    "inr": "📌 **INR pairs** (USD/INR, EUR/INR, GBP/INR) are Indian Rupee currency pairs. They use poll-based data (updated every 10 seconds) instead of live streaming, and are influenced by RBI policy, oil prices, and global USD demand.",
    "rbi": "📌 **RBI (Reserve Bank of India)** sets India's interest rates and monetary policy. Rate changes significantly affect INR pairs — rate hikes usually strengthen the Rupee.",
}


def _fallback_response(intent: str, context: dict, user_message: str = "") -> str:
    """Rich rule-based fallback when no LLM is configured."""
    signal = context.get("latest_signal", {})
    decision = signal.get("decision", "HOLD")
    gate_log = signal.get("gate_log", {})
    regime = signal.get("regime", "unknown")
    msg_lower = user_message.lower()

    # Check glossary first for educational questions
    if intent in ("explain_concept", "learn_forex"):
        for term, explanation in FOREX_GLOSSARY.items():
            if term in msg_lower:
                return explanation
        return (
            "**Forex Concepts I can explain:**\n"
            "pip · spread · leverage · lot · stop loss · take profit · R:R · margin · drawdown · "
            "BoS · ChoCH · FVG · order block · liquidity sweep · regime · expansion · RSI · Sharpe · "
            "ensemble · DNN · GRU · CNN · Transformer · Risk Guardian · drift · BUY · SELL · HOLD\n\n"
            "Just ask: *'What is [term]?'* and I'll explain it simply!"
        )

    if intent == "explain_signal":
        failed = [k for k, v in gate_log.items() if v is False]
        gate_names = {
            "regime_ok": "Regime must be Expansion",
            "structure_bullish": "Structure must be Bullish (BoS confirmed)",
            "liquidity_sweep_ok": "Liquidity Sweep must be confirmed",
            "probability_ok": "AI Ensemble probability must exceed threshold",
            "rsi_ok": "RSI must be below 70 (not overbought)",
            "rr_ok": "Risk:Reward must be at least 1:2",
            "guardian_ok": "Risk Guardian must approve (drawdown/trade limit check)",
        }
        failed_readable = [gate_names.get(g, g) for g in failed]
        result = f"**Decision: {decision}** | Regime: {regime}\nEnsemble Probability: {signal.get('ensemble_probability', 'N/A')}\n\n"
        if failed_readable:
            result += "⚠️ **Failed Gates (why HOLD):**\n" + "\n".join(f"  ✗ {g}" for g in failed_readable)
        else:
            result += "✅ All 7 gates passed."
        return result

    elif intent == "regime_inquiry":
        return (
            f"📌 Current market regime: **{regime}**\n"
            "- **Expansion** → Trending market, all AI models active, BUY/SELL signals possible\n"
            "- **Accumulation** → Range-bound market, system holds\n"
            "- **Exhaustion** → Trend ending, system avoids new trades"
        )
    elif intent == "show_performance":
        perf = context.get("performance", {})
        return (
            f"📊 **Performance Summary**\n"
            f"Win Rate: {perf.get('win_rate', 'N/A')}%\n"
            f"Max Drawdown: {perf.get('max_drawdown_pct', 'N/A')}%\n"
            f"Expectancy: {perf.get('expectancy', 'N/A')}\n"
            f"Sharpe Ratio: {perf.get('sharpe_ratio', 'N/A')}"
        )
    return (
        "💡 I can help you understand:\n"
        "- **Trading signals**: Ask 'Why HOLD?' or 'What is the current signal?'\n"
        "- **Forex terms**: Ask 'What is a pip?' or 'Explain leverage'\n"
        "- **Performance**: Ask 'Show win rate' or 'What is the Sharpe ratio?'\n"
        "- **Market regime**: Ask 'What regime are we in?'\n\n"
        "Configure GEMINI_API_KEY for full AI-powered responses!"
    )

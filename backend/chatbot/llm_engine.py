"""
llm_engine.py – Chatbot LLM interface.
Supports Gemini 1.5 Flash (default) and OpenAI GPT-4o-mini.
Upgraded to act as a friendly Forex educator with plain-English explanations.
"""

import os
import logging
from app.config import settings

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name=settings.LLM_MODEL_GEMINI,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 500,
    }
)

SYSTEM_PROMPT = """You are ForeXtron — a friendly, expert financial assistant and Forex trading educator built into the platform.

Your core jobs are:
1. EXPLAIN FOREX AND FINANCIAL CONCEPTS in plain, beginner-friendly language using real-world analogies. You are permitted to answer ANY general finance, economy, or trading questions.
2. EXPLAIN PLATFORM SIGNALS using the live system state data provided to you.

== STRICT DOMAIN FILTER ==
If the user asks a question that is COMPLETELY UNRELATED to finance, trading, economics, or the platform (e.g. baking recipes, coding, casual chat, etc.), you MUST reply with this exact phrase, word-for-word, and nothing else:
"hey , glad u had this doubt but i am just an financial aid . SO, ask me questions related that "

== HOW TO TEACH ==
- ALWAYS start with a simple, plain-English sentence. Then add a real-world analogy.
- THEN give the technical detail.
- Use emojis sparingly to make responses friendly (e.g. 📌, 💡, ⚠️).
- Keep responses concise unless a longer explanation is truly needed.
- Never use jargon without immediately explaining it in brackets.

== SIGNAL EXPLANATIONS ==
When explaining platform signals, always cite the specific gate(s) from the gate_log.
When explaining a HOLD signal, ALWAYS name which gate failed and why it matters.
For INR pairs, mention relevant macro factors: RBI policy, USD/INR correlation, oil prices.

Remember: You are talking to someone who may be completely new to Forex and Finance. Be their friendly guide."""

INTENT_EXAMPLES = {
    "explain_signal": "Why HOLD? Why BUY? Explain the signal. What is the current recommendation?",
    "show_performance": "Win rate? How are we doing? Show performance. What's the return?",
    "regime_inquiry": "What regime? Market conditions? Expansion or accumulation?",
    "explain_concept": "What is BoS? Explain liquidity sweep. What is ChoCH? What is FVG?",
    "risk_inquiry": "Risk status? Drawdown? How many trades today? Guardian status?",
    "trade_history": "Recent trades? Last trade result? Trade log?",
    "inr_inquiry": "USD INR? What about INR pairs? Indian Rupee signal?",
}


async def generate_response(intent: str, context: dict, user_message: str) -> str:
    """Uses the native Gemini Google Generative AI SDK to generate responses."""
    logger.info("Using Native Gemini response engine.")
    
    # Check glossary first for instant definitions (faster than LLM for static terms)
    msg_lower = user_message.lower()
    if intent in ("explain_concept", "learn_forex"):
        for term, explanation in FOREX_GLOSSARY.items():
            if term in msg_lower:
                return f"💡 **{term.upper()}**: {explanation}"
                
    # Build context for the LLM
    signal = context.get("latest_signal", {})
    decision = signal.get("decision", "HOLD")
    regime = signal.get("regime", "unknown")
    gate_log = signal.get("gate_log", {})
    
    # Format current state for the LLM
    state_str = (
        f"CURRENT MARKET STATE:\n"
        f"- Regime: {regime}\n"
        f"- System Decision: {decision}\n"
        f"- Failed Gates: {[k for k, v in gate_log.items() if v is False] or 'None'}\n"
    )
    
    full_prompt = f"{SYSTEM_PROMPT}\n\n{state_str}\n\nUser Question: {user_message}"
    
    try:
        # Note: using async generation if available, else standard
        response = await model.generate_content_async(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return _fallback_response(intent, context, user_message)



# ── Forex Glossary (50+ terms, used as fallback) ──────────────────────────
FOREX_GLOSSARY = {
    "pip": "A pip is the smallest standard price move in Forex. It is like a cent for exchange rates. For most pairs like EUR/USD or GBP/USD, 1 pip is 0.0001 or the 4th decimal place. For JPY pairs, 1 pip is 0.01. For example, if EUR/USD moves from 1.0800 to 1.0801, that is a 1 pip move.",
    "spread": "The spread is the difference between the BUY ask price and SELL bid price. It is the broker's fee. Think of it like a currency exchange booth at the airport that buys at 82 and sells at 83. The 1 difference is the spread.",
    "leverage": "Leverage lets you control a large trade with a small amount of money. A 100:1 leverage means 1,000 controls 100,000 worth of currency. It amplifies both profits and losses, so use it carefully.",
    "lot": "A lot is a standard unit of trade size. 1 Standard Lot is 100,000 units. 1 Mini Lot is 10,000 units. 1 Micro Lot is 1,000 units. FXGuru uses 0.01 lots for demo trades to keep risk minimal.",
    "lot size": "Lot size controls how much currency you are buying or selling. A bigger lot size means a bigger profit per pip AND bigger loss per pip. FXGuru defaults to 0.01 micro lots for safe demo trading.",
    "stop loss": "A stop loss is your safety net. It automatically closes your trade if price moves against you beyond a set level, limiting your loss. FXGuru calculates the SL based on recent price structure and keeps risk at 1-2% per trade.",
    "sl": "SL stands for Stop Loss. It automatically closes your trade if the price moves against you to limit your loss.",
    "take profit": "Take Profit is your target exit. When price reaches this level, your trade closes automatically with a profit. FXGuru sets TP to achieve at least a 1:2 risk to reward ratio.",
    "tp": "TP stands for Take Profit. It is where your trade automatically closes in profit.",
    "risk reward": "Risk to Reward compares how much you risk versus how much you could gain. A 1:2 ratio means you risk 10 pips to potentially earn 20 pips. FXGuru only signals when the ratio is at least 1:2 (Gate 6).",
    "rr": "R:R stands for Risk Reward ratio. It shows the potential profit compared to the potential loss on a trade.",
    "margin": "Margin is the deposit your broker holds as collateral while your trade is open. If your account balance drops too low relative to margin, you get a margin call and trades close automatically.",
    "drawdown": "Drawdown measures how much the account has fallen from its highest point. A 10% drawdown means after reaching a peak balance of 10,000, it dropped to 9,000. FXGuru's Risk Guardian halts trading if daily drawdown exceeds its limit.",
    "bos": "BoS stands for Break of Structure. It means price has closed beyond the last significant swing high or swing low. It confirms the current trend is continuing.",
    "break of structure": "Break of Structure means price has closed beyond a key swing point, confirming trend direction. A bullish BoS means a higher high is confirmed. A bearish BoS means a lower low is confirmed.",
    "choch": "ChoCH stands for Change of Character. It is the FIRST opposite Break of Structure after a trend. It's the earliest warning sign that the trend may be reversing.",
    "change of character": "Change of Character is the first sign a trend is losing momentum and may reverse. FXGuru uses this to avoid trading in the wrong direction.",
    "fvg": "FVG stands for Fair Value Gap. It is an imbalance zone created when price moves so fast that it skips over an area. Institutions tend to send price back to fill the gap before continuing. FXGuru looks for FVGs as potential entry zones.",
    "fair value gap": "A Fair Value Gap is an area on the chart where price moved too quickly and left an imbalance. Price often returns to this zone.",
    "order block": "An Order Block is the last bearish candle before a bullish move, or the last bullish candle before a bearish move. It marks where institutions placed large orders. Price often revisits these zones.",
    "liquidity": "Liquidity in Forex refers to clusters of stop-loss orders sitting above recent highs or below recent lows. Big institutions often push price into these areas to sweep the stops and collect liquidity before reversing.",
    "liquidity sweep": "A Liquidity Sweep happens when price briefly breaks above a recent high or below a recent low to trigger stop-losses, then quickly reverses. FXGuru requires this as Gate 3 before a BUY signal.",
    "regime": "Market Regime is the overall market condition: Expansion, Accumulation, or Exhaustion. FXGuru only trades in the Expansion regime.",
    "expansion": "The Expansion regime means the market is trending strongly with higher volatility. This is when FXGuru's models activate and BUY/SELL signals can be generated.",
    "accumulation": "The Accumulation regime means the market is range-bound and institutions are quietly building positions. FXGuru stays on HOLD during this phase.",
    "exhaustion": "The Exhaustion regime means the trend is running out of energy. FXGuru signals HOLD to avoid catching a reversal.",
    "ensemble": "Ensemble means combining multiple AI models to make one final prediction. FXGuru combines Logistic Regression, DNN, GRU, CNN, and Transformer models. Their weighted average gives the ensemble probability.",
    "dnn": "DNN stands for Deep Neural Network. It is an AI model that looks at many technical features at once to predict price direction. It contributes 20% to FXGuru's ensemble.",
    "gru": "GRU stands for Gated Recurrent Unit. It is an AI model that understands sequences and patterns over time. It contributes 30% to the ensemble and is the highest-weighted model.",
    "cnn": "CNN stands for Convolutional Neural Network. Originally designed for images, it detects patterns in price chart data. It contributes 25% to the ensemble.",
    "transformer": "Transformer is the same AI architecture behind ChatGPT, used here to find long-range patterns in price history. It contributes 15% to FXGuru's ensemble.",
    "rsi": "RSI stands for Relative Strength Index. It measures whether a currency pair is overbought or oversold. FXGuru checks if RSI is below 70 as Gate 5 to avoid buying into an overheated market.",
    "sharpe": "The Sharpe Ratio measures return relative to risk. A Sharpe above 1.0 is good, and above 2.0 is excellent. Higher means better risk-adjusted performance.",
    "sharpe ratio": "The Sharpe Ratio measures the average return earned in excess of the risk-free rate per unit of volatility or total risk.",
    "expectancy": "Expectancy is the average profit or loss you can expect per trade, accounting for win rate and average win/loss size. A positive expectancy means the system is profitable over many trades.",
    "win rate": "Win Rate is the percentage of trades that close at profit. A 60% win rate means 6 out of 10 trades win.",
    "buy": "A BUY signal means FXGuru's AI expects the price to go UP. All 7 decision gates must pass for a BUY. You profit if price rises above your entry and hits Take Profit.",
    "sell": "A SELL signal means FXGuru's AI expects price to go DOWN. You profit if price falls to your Take Profit level.",
    "hold": "HOLD means one or more of FXGuru's 7 safety gates have failed. The trade conditions aren't right yet. You can ask me 'why HOLD' to see exactly which gates failed.",
    "drift": "Model Drift means the AI's predictions have become less accurate over time. FXGuru's Drift Agent monitors this and triggers retraining when needed.",
    "threshold": "Dynamic Threshold is the minimum probability required for FXGuru to issue a BUY signal. It adjusts based on market conditions.",
    "risk guardian": "Risk Guardian is FXGuru's automated risk manager. It tracks daily drawdown and trade count. If daily losses exceed the limit, it goes into Hold Mode to protect your account.",
    "supervisor": "The Supervisor Agent oversees all AI agents like the Risk Guardian and Drift Agent to coordinate overall system health.",
    "pips": "Pips are the smallest regular price changes in an exchange rate. You can ask me 'what is a pip' for more detail.",
    "candle": "A candlestick or candle is a chart element showing the open, high, low, and close price for a time period. Green candles mean the price closed higher. Red candles mean the price closed lower.",
    "oanda": "OANDA is the Forex broker connected to this platform. Your OANDA Practice account uses demo money, so no real funds are at risk.",
    "inr": "INR pairs use poll-based data updated every 10 seconds instead of live streaming. They are influenced by RBI policy, oil prices, and global USD demand.",
    "rbi": "The Reserve Bank of India sets India's interest rates and monetary policy. Rate changes significantly affect INR pairs.",
}


def _fallback_response(intent: str, context: dict, user_message: str = "") -> str:
    """Rich rule-based engine covering website navigation, forex education, and signals."""
    signal = context.get("latest_signal", {})
    decision = signal.get("decision", "HOLD")
    gate_log = signal.get("gate_log", {})
    regime = signal.get("regime", "unknown")
    msg_lower = user_message.lower()

    if intent == "hello_help":
        return (
            "Hello! I am ForeXtron. Let's make trading simpler together.\n\n"
            "Here is how I can assist you:\n\n"
            "I can explain incoming signals. Just ask me 'Why HOLD?' or 'What is the current signal?'\n\n"
            "I can show you our performance metrics. Simply type 'What is our win rate?'\n\n"
            "I can guide you through the dashboard features. Try asking 'How do I use the Trade Journal?' or 'What is dark mode?'\n\n"
            "I can also teach you Forex concepts if you are learning. Just ask 'What is a pip?' or 'Explain leverage.'\n\n"
            "How can I help you today?"
        )

    # Check glossary first for educational questions
    if intent in ("explain_concept", "learn_forex"):
        for term, explanation in FOREX_GLOSSARY.items():
            if term in msg_lower:
                return explanation
        return (
            "I can explain many Forex concepts to help you learn! For example, you can ask me about pips, spreads, leverage, lots, margin, or stop losses.\n\n"
            "I can also explain technical analysis like BoS, ChoCH, FVG, or order blocks.\n\n"
            "Just ask me: 'What is a pip?' and I will explain it simply."
        )

    if intent == "explain_signal":
        failed = [k for k, v in gate_log.items() if v is False]
        gate_names = {
            "regime_ok": "Regime must be Expansion",
            "structure_bullish": "Structure must be Bullish (BoS confirmed)",
            "liquidity_sweep_ok": "Liquidity Sweep must be confirmed",
            "probability_ok": "AI Ensemble probability must exceed threshold",
            "rsi_ok": "RSI must be below 70 to avoid overbought conditions",
            "rr_ok": "Risk to Reward ratio must be at least 1:2",
            "guardian_ok": "Risk Guardian must approve based on drawdown and trade limits",
        }
        failed_readable = [gate_names.get(g, g) for g in failed]
        result = f"The current decision is {decision}. We are seeing an {regime} regime right now. The ensemble probability calculates to {signal.get('ensemble_probability', 'N/A')}.\n\n"
        if failed_readable:
            result += "The system chose to HOLD because the following gates failed:\n" + "\n".join(f" Failed: {g}" for g in failed_readable)
        else:
            result += "All 7 safety gates have successfully passed."
        return result

    elif intent == "regime_inquiry":
        return (
            f"The current market regime is {regime}.\n\n"
            "Expansion means a trending market where all AI models are active and trades can be generated.\n\n"
            "Accumulation means a range-bound market where the system holds.\n\n"
            "Exhaustion means the trend is ending, so the system avoids new trades."
        )
    elif intent == "show_performance":
        perf = context.get("performance", {})
        return (
            f"Here is our recent Performance Summary:\n\n"
            f"Win Rate: {perf.get('win_rate', 'N/A')}%\n"
            f"Max Drawdown: {perf.get('max_drawdown_pct', 'N/A')}%\n"
            f"Expectancy: {perf.get('expectancy', 'N/A')}\n"
            f"Sharpe Ratio: {perf.get('sharpe_ratio', 'N/A')}"
        )
    elif intent == "navigate_website":
        if "journal" in msg_lower:
            return "The Trade Journal tab tracks all your simulated trades. It records entry, SL, TP, and automatically calculates your running Win Rate and profit. It saves directly to your browser's local storage automatically."
        elif "timeline" in msg_lower or "history" in msg_lower:
            return "The vertical Signal Timeline on the right logs every signal the AI generates. You can click any entry to expand it and see exactly which decision gates passed or failed."
        elif "dark mode" in msg_lower or "theme" in msg_lower:
            return "You can enable Dark Mode using the Sun or Moon icon located in the top navigation bar. We will remember your preference for your next visit."
        elif "ticker" in msg_lower or "price" in msg_lower:
            return "The scrolling Price Ticker below the navigation shows live Bid to Ask spreads and flashes green and red as prices move. If you click on a pair, it will instantly switch the dashboard to that instrument."
        elif "demo" in msg_lower or "trade" in msg_lower:
            return "You can use the 'Demo BUY' or 'Demo SELL' buttons at the top of the screen to place simulated trades for practice. These will immediately appear in the Signal Timeline and Trade Journal so you can track your success."
        return (
            "I can help you understand the dashboard features! You can ask me about the Trade Journal, the Signal Timeline, the Price Ticker, or how to use Dark Mode."
        )

    return (
        "I'm here to assist you! You can ask me about trading signals, such as 'Why HOLD?' or 'What is the current signal?'\n\n"
        "You can ask me to explain Forex terms like 'What is a pip?' or 'Explain leverage.'\n\n"
        "If you want to view our metrics, try 'Show win rate' or 'What is the Sharpe ratio?'\n\n"
        "I can also guide you around the platform. Just ask 'Where are my trades?' or 'How do I use dark mode?'"
    )

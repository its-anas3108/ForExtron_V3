"""
llm_engine.py – Chatbot LLM interface.
Uses Gemini 1.5 Flash (free) as primary, with Groq and HuggingFace as fallbacks.
The chatbot is trained as the Lead Architect of the ForeXtron V3 platform.
"""

import os
import logging
from app.config import settings

import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=settings.GEMINI_API_KEY)

# OpenRouter (Optional fallback)
openrouter_client = None
if settings.OPENAI_API_KEY:
    openrouter_client = openai.AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENAI_API_KEY,
    )

SYSTEM_PROMPT = """You are ForeXtron — a friendly, expert financial assistant and the Lead Architect of the ForeXtron v3 deep learning trading platform.

Your core jobs are:
1. EXPLAIN FOREX & SMC: Using real-world analogies, explain concepts like Liquidity Sweeps, BoS, Fair Value Gaps, pips, lots, spreads etc.
2. PROJECT ARCHITECT: You have deep knowledge of the Forextron v3 architecture. Explain how PatchTST (35%), TCN (25%), TFT (30%), and GRN (10%) layers work together.
3. PLATFORM FEATURES: Explain the Live Dashboard, Signal Timeline, Trade Journal, Monte Carlo Simulator, Liquidity Map, and News Intelligence.
4. ANALYZE SIGNALS: Use the provided MARKET STATE to explain WHY the system decided to BUY, SELL, or HOLD. Reference the specific gates that passed or failed.

== ARCHITECT-LEVEL KNOWLEDGE ==
- Architecture: Unified PatchTST-TCN-TFT pipeline replacing legacy RNN/GRU models.
- PatchTST (35%): Local attention core — breaks 100-candle sequences into 10 patches of 10 candles each. Captures local momentum patterns.
- TCN (25%): Temporal Convolutional Network with causal dilations (D=1,2,4) for multi-horizon feature extraction without look-ahead bias.
- TFT (30%): Temporal Fusion Transformer that fuses local patch features with global regime context (Expansion/Accumulation) for optimal entry detection.
- GRN (10%): Gated Residual Networks as final noise suppressors. Only the strongest signals pass to the 7-gate decision layer.
- 7 Safety Gates: 1) Regime=Expansion, 2) Structure=Bullish/Bearish, 3) Liquidity=Swept, 4) Confidence>Threshold, 5) RSI<70, 6) R:R>=1:2, 7) Risk Guardian=PASS
- Indicators: RSI(14), MACD(12,26,9), ATR(14), Bollinger Bands(20, 2 sigma), EMA(10,50)
- Liquidity Engine: 10 synthetic depth levels at 10-tick intervals. Round numbers (00/50) get +15% weight boost.
- Structure Engine: BoS (Break of Structure) and ChoCH (Change of Character) detected using 5-period swing windows.
- Regime Detection: Expansion (trending), Accumulation (range-bound), Exhaustion (dead trend). Trading is locked to Expansion only.
- Monte Carlo: 10,000+ iterations based on win-rate and expectancy to forecast equity curves.
- Risk: 1% per trade, 2% daily drawdown cap, max 2 trades per session, minimum 1:2 R:R ratio.

== PLATFORM FEATURES ==
- Dashboard: Shows live chart with candlesticks and EMA overlays, current signal decision, regime badge, and AI confidence meter.
- Signal Timeline: Vertical log on the right side showing every AI decision with expandable gate details.
- Trade Journal: Logs all simulated trades with entry/exit, SL/TP, P&L, and running win-rate statistics.
- News Intelligence: AI-analyzed forex news with sentiment scoring and market impact assessment.
- Liquidity Map: Shows synthetic buy/sell pressure at 10 depth levels around current price.
- Price Ticker: Scrolling live bid/ask spreads for all supported pairs. Click any pair to switch instruments.
- Dark Mode: Toggle via the sun/moon icon in the navigation bar.
- Chatbot (You): Available on the Intelligence tab to answer any forex or platform question.

== RESPONSE STYLE ==
- Give direct, helpful answers. Sound like a knowledgeable friend, not a textbook.
- For forex concepts: start simple, add an analogy, then give technical depth.
- For signal questions: reference specific gate names and market state data.
- For platform questions: tell the user exactly where to find things and how to use them.
- Keep answers concise but complete. Use bullet points for lists.
- Use emojis sparingly: pin, bulb, construction, brain, chart
- DO NOT USE ASTERISKS (*) FOR BOLDING OR ITALICS. USE PLAIN TEXT.

== DOMAIN FILTER ==
If the user asks something completely unrelated to forex, trading, or this platform, politely redirect:
"Hey! I'm ForeXtron, your forex and trading assistant. I'm best at answering questions about trading, our platform, and market analysis. What would you like to know about those?"
"""

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
    """Routes response generation through AI providers with knowledge augmentation."""
    
    # Build context for the LLM
    signal = context.get("latest_signal", {})
    decision = signal.get("decision", "HOLD")
    regime = signal.get("regime", "unknown")
    gate_log = signal.get("gate_log", {})
    
    state_str = (
        f"CURRENT MARKET STATE:\n"
        f"- Regime: {regime}\n"
        f"- System Decision: {decision}\n"
        f"- Ensemble Probability: {signal.get('ensemble_probability', 'N/A')}\n"
        f"- Failed Gates: {[k for k, v in gate_log.items() if v is False] or 'None'}\n"
    )

    try:
        # Augment prompt with relevant project knowledge
        relevant_knowledge = _get_relevant_knowledge(user_message)
        knowledge_context = f"\n\nRELEVANT TECHNICAL CONTEXT:\n{relevant_knowledge}" if relevant_knowledge else ""
        
        full_message = f"{state_str}{knowledge_context}\n\nUser Question: {user_message}"

        # Multi-Provider Fallback Chain
        providers = ["gemini", "groq", "huggingface", "openai"]
        if settings.LLM_PROVIDER in providers:
            providers.remove(settings.LLM_PROVIDER)
            providers.insert(0, settings.LLM_PROVIDER)

        for provider in providers:
            try:
                raw_response = ""
                if provider == "gemini" and settings.GEMINI_API_KEY:
                    raw_response = await _generate_gemini_response(full_message)
                elif provider == "groq" and settings.GROQ_API_KEY:
                    raw_response = await _generate_groq_response(full_message)
                elif provider == "huggingface" and settings.HUGGINGFACE_API_KEY:
                    raw_response = await _generate_huggingface_response(full_message)
                elif provider == "openai" and openrouter_client:
                    raw_response = await _generate_openrouter_response(full_message)
                
                if raw_response:
                    return raw_response.replace("*", "")
            except Exception as provider_err:
                logger.warning(f"Provider {provider} failed: {provider_err}. Trying next...")
                continue

        # All providers failed — use deterministic fallback
        logger.warning("All AI providers failed. Using deterministic fallback.")
        return _fallback_response(intent, context, user_message).replace("*", "")

    except Exception as e:
        logger.error(f"Critical Chatbot Error: {e}")
        return _fallback_response(intent, context, user_message).replace("*", "")


async def _generate_gemini_response(full_message: str) -> str:
    """Generates response using Google Gemini (free tier)."""
    logger.info(f"Using Gemini ({settings.LLM_MODEL_GEMINI})")
    model = genai.GenerativeModel(
        model_name=settings.LLM_MODEL_GEMINI,
        system_instruction=SYSTEM_PROMPT
    )
    response = await model.generate_content_async(
        full_message, 
        request_options={"timeout": 15}
    )
    return response.text


async def _generate_groq_response(full_message: str) -> str:
    """Uses Groq for extremely fast open-source AI inference."""
    logger.info(f"Using Groq ({settings.LLM_MODEL_GROQ})")
    client = openai.AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=settings.GROQ_API_KEY,
    )
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL_GROQ,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_message}
        ],
        temperature=0.7,
        max_tokens=600,
        timeout=10.0,
    )
    return response.choices[0].message.content


async def _generate_huggingface_response(full_message: str) -> str:
    """Uses Hugging Face Inference API."""
    import aiohttp
    logger.info(f"Using HuggingFace ({settings.HUGGINGFACE_MODEL})")
    
    API_URL = f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    payload = {
        "inputs": f"SYSTEM: {SYSTEM_PROMPT}\n\nUSER: {full_message}\n\nASSISTANT:",
        "parameters": {"max_new_tokens": 500, "temperature": 0.7}
    }

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                    return result[0]["generated_text"].split("ASSISTANT:")[-1].strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].split("ASSISTANT:")[-1].strip()
            
            raise Exception(f"HuggingFace failed with status {response.status}")


async def _generate_openrouter_response(full_message: str) -> str:
    """Generates response using OpenRouter via OpenAI client."""
    logger.info(f"Using OpenRouter ({settings.LLM_MODEL_OPENAI})")
    response = await openrouter_client.chat.completions.create(
        model=settings.LLM_MODEL_OPENAI,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_message}
        ],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content


async def generate_llm_text(prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Generic utility for generating LLM text for background tasks (like news analysis)."""
    try:
        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            model = genai.GenerativeModel(
                model_name=settings.LLM_MODEL_GEMINI,
                system_instruction=system_prompt
            )
            response = await model.generate_content_async(prompt)
            return response.text.strip()
        elif settings.LLM_PROVIDER == "openai" and openrouter_client:
            response = await openrouter_client.chat.completions.create(
                model=settings.LLM_MODEL_OPENAI,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Generic LLM Error: {e}")
    return ""


# ── Forex Glossary (used by explain_router.py) ────────────────────────────
FOREX_GLOSSARY = {
    "pip": "A pip is the smallest standard price move in Forex (0.0001 for most pairs, 0.01 for JPY).",
    "spread": "The spread is the difference between the BUY (ask) and SELL (bid) price — the broker's fee.",
    "leverage": "Leverage lets you control a large position with small capital. 100:1 means $1,000 controls $100,000.",
    "lot": "A lot is a standard trade size unit. Standard=100,000, Mini=10,000, Micro=1,000 units.",
    "stop loss": "A stop loss automatically closes your trade at a set loss level to protect your account.",
    "take profit": "Take Profit automatically closes your trade when price hits your target profit level.",
    "risk reward": "Risk-to-Reward compares potential loss vs gain. ForeXtron requires minimum 1:2 R:R.",
    "margin": "Margin is the collateral your broker holds while your trade is open.",
    "drawdown": "Drawdown measures the drop from peak account balance. ForeXtron caps daily drawdown at 2%.",
    "bos": "Break of Structure (BoS) confirms trend continuation when price closes beyond a swing point.",
    "choch": "Change of Character (ChoCH) is the first counter-trend BoS, signaling potential reversal.",
    "fvg": "Fair Value Gap — an imbalance zone where price moved too fast, often revisited by institutions.",
    "order block": "An Order Block marks where institutions placed large orders — price often revisits these zones.",
    "liquidity": "Liquidity = clusters of stop-loss orders near highs/lows that institutions target before reversing.",
    "liquidity sweep": "A Liquidity Sweep occurs when price wicks beyond a swing level to grab stops, then reverses.",
    "regime": "Market Regime: Expansion (trending), Accumulation (range), or Exhaustion (ending trend).",
    "expansion": "Expansion = strong trending market. ForeXtron's AI models are active and signals can fire.",
    "accumulation": "Accumulation = range-bound market. Institutions building positions quietly. System holds.",
    "exhaustion": "Exhaustion = trend losing energy. System holds to avoid catching reversals.",
    "patchtst": "PatchTST: Local attention core (35% weight). Breaks price into 10-candle patches for pattern detection.",
    "tcn": "TCN: Temporal Convolutional Network (25% weight). Uses causal dilations for multi-horizon features.",
    "tft": "TFT: Temporal Fusion Transformer (30% weight). Fuses local features with global regime context.",
    "grn": "GRN: Gated Residual Network (10% weight). Final noise filter before the 7-gate decision layer.",
    "rsi": "RSI measures overbought/oversold conditions. ForeXtron checks RSI<70 as Safety Gate 5.",
    "sharpe ratio": "Sharpe Ratio = risk-adjusted return. Above 1.0 is good, above 2.0 is excellent.",
    "expectancy": "Expectancy = average profit/loss per trade accounting for win rate and avg win/loss size.",
    "win rate": "Win Rate = percentage of trades that close in profit.",
    "monte carlo": "Monte Carlo runs 10,000+ simulations to forecast future equity curves from your win rate.",
    "risk guardian": "Risk Guardian monitors daily drawdown and trade count, halting trading if limits are hit.",
    "safety gates": "7 criteria for trade signals: Regime, Structure, Liquidity, Confidence, RSI, R:R, Guardian.",
    "journal": "Trade Journal logs all simulated trades with P&L and running statistics.",
    "timeline": "Signal Timeline logs every AI decision for the selected instrument.",
    "candle": "A candlestick shows open, high, low, close for a time period. Green=up, Red=down.",
    "oanda": "OANDA is the connected broker. Practice accounts use demo money — no real risk.",
}


# ── Project V3 Knowledge Base ──────────────────────────────────────────────
PROJECT_V3_KNOWLEDGE = {
    "architecture": "Forextron v3 is an institutional-grade PatchTST-TCN-TFT deep learning pipeline. It eliminates lag-heavy RNNs in favor of shared-weight attention kernels and gated residuals.",
    "patchtst": "PatchTST (Patch Time Series Transformer) handles 35% of architectural importance. It divides 100-candle sequences into 10 patches to learn local momentum while maintaining long-term memory.",
    "tcn": "Temporal Convolutional Network (TCN) handles 25% of the intelligence. Uses causal dilated architecture (dilation factors 1, 2, 4) to extract features without look-ahead bias.",
    "tft": "Temporal Fusion Transformer (TFT) contributes 30% of the decision weight. Fuses local patch features with global regime context for final prediction.",
    "grn": "Gated Residual Networks (GRN) provide the final 10% filtering. Noise suppressors that ensure only the strongest signals pass to the trade output.",
    "indicators": "Institutional parameters: RSI(14), MACD(12,26,9), ATR(14), Bollinger Bands(20, 2 sigma), EMA(10,50).",
    "liquidity": "The Liquidity Engine generates 10 synthetic depth levels (5 support, 5 resistance) at 10-tick intervals. Psychological levels ending in 00 or 50 get a 15% weight boost.",
    "liquidity sweep": "A Liquidity Sweep is detected when a candle wick extends beyond a 5-period swing high/low but the close stays inside, confirming institutional stop-hunting.",
    "bos": "Break of Structure (BoS) is confirmed when a candle closes above the last significant 5-period swing point, validating trend continuation.",
    "choch": "Change of Character (ChoCH) is the first counter-trend BoS after a sustained 5+ period trend, signaling an institutional shift in bias.",
    "gates": "The 7 Safety Gates: 1. Regime (Expansion), 2. Structure (Bullish), 3. Liquidity (Swept), 4. Confidence (>Threshold), 5. RSI (<70), 6. R:R (min 1:2), 7. Guardian (Daily Limit).",
    "regime": "Regime Detection classifies: Expansion (trending), Accumulation (range-bound), Exhaustion (dead trend). Trading is locked to Expansion only.",
    "monte carlo": "Monte Carlo simulator runs 10,000+ iterations based on win-rate and expectancy to forecast the equity curve over the next 100 trades.",
    "risk": "Risk management: 1% per trade, 2% daily drawdown cap, max 2 trades per session, minimum 1:2 R:R ratio enforced by the Risk Guardian.",
}

def _get_relevant_knowledge(user_message: str) -> str:
    """Retrieves relevant technical knowledge based on the user's question."""
    msg = user_message.lower()
    matches = []
    
    # Architecture questions
    if any(q in msg for q in ["patch", "tst", "tcn", "tft", "grn", "architecture", "model weight", "v3 model"]):
        for k in ["architecture", "patchtst", "tcn", "tft", "grn"]:
            if k in msg:
                matches.append(f"{k.upper()}: {PROJECT_V3_KNOWLEDGE[k]}")
        if not matches:
            matches.append(PROJECT_V3_KNOWLEDGE["architecture"])

    # Specific topic matching
    for key, content in PROJECT_V3_KNOWLEDGE.items():
        if key in msg and key not in ["architecture", "patchtst", "tcn", "tft", "grn"]:
            matches.append(f"{key.upper()}: {content}")
    
    # Generic platform questions — provide architecture + gates overview
    if not matches and any(w in msg for w in ["system", "how does", "what does", "tell me about", "explain the platform"]):
        return f"{PROJECT_V3_KNOWLEDGE['architecture']}\n{PROJECT_V3_KNOWLEDGE['gates']}"
        
    return "\n".join(matches)


def _fallback_response(intent: str, context: dict, user_message: str = "") -> str:
    """Deterministic fallback when all AI providers are unavailable."""
    signal = context.get("latest_signal", {})
    decision = signal.get("decision", "HOLD")
    gate_log = signal.get("gate_log", {})
    regime = signal.get("regime", "unknown")
    msg_lower = user_message.lower()

    if intent == "hello_help":
        return (
            "Hello! I'm ForeXtron, your AI trading assistant! 🧠\n\n"
            "Here's what I can help with:\n"
            "• Signal Analysis: Ask 'Why HOLD?' or 'What's the current signal?'\n"
            "• Performance: Ask 'What's our win rate?'\n"
            "• Forex Education: Ask 'What is a pip?' or 'Explain BoS'\n"
            "• Platform Guide: Ask 'Where is the Trade Journal?'\n"
            "• Architecture: Ask 'How does PatchTST work?'\n\n"
            "What would you like to know?"
        )

    if intent == "explain_signal":
        failed = [k for k, v in gate_log.items() if v is False]
        gate_names = {
            "regime_ok": "Regime must be Expansion",
            "structure_bullish": "Structure must be Bullish (BoS confirmed)",
            "liquidity_sweep_ok": "Liquidity Sweep must be confirmed",
            "probability_ok": "AI confidence must exceed threshold",
            "rsi_ok": "RSI must be below 70 (not overbought)",
            "rr_ok": "Risk-to-Reward must be at least 1:2",
            "guardian_ok": "Risk Guardian must approve (drawdown + trade limits)",
        }
        failed_readable = [gate_names.get(g, g) for g in failed]
        result = f"📊 Current decision: {decision} | Regime: {regime} | Probability: {signal.get('ensemble_probability', 'N/A')}\n\n"
        if failed_readable:
            result += "🔴 Gates that failed:\n" + "\n".join(f"• {g}" for g in failed_readable)
        else:
            result += "🟢 All 7 safety gates passed!"
        return result

    elif intent == "regime_inquiry":
        return (
            f"📊 Current regime: {regime}\n\n"
            "• Expansion = trending market, AI models are active, signals can fire\n"
            "• Accumulation = range-bound, institutions building positions, system holds\n"
            "• Exhaustion = trend losing energy, system holds to avoid catching reversals"
        )
    
    elif intent == "show_performance":
        perf = context.get("performance", {})
        return (
            f"📈 Performance Summary\n\n"
            f"• Win Rate: {perf.get('win_rate', 'N/A')}%\n"
            f"• Max Drawdown: {perf.get('max_drawdown_pct', 'N/A')}%\n"
            f"• Expectancy: {perf.get('expectancy', 'N/A')}\n"
            f"• Sharpe Ratio: {perf.get('sharpe_ratio', 'N/A')}"
        )

    # Try knowledge base for technical questions
    knowledge = _get_relevant_knowledge(user_message)
    if knowledge:
        return f"💡 {knowledge}"

    # Try glossary for educational questions
    for term, explanation in FOREX_GLOSSARY.items():
        if term in msg_lower:
            return f"💡 {term.upper()}: {explanation}"

    # Smart fallback: answer trade-related questions using market state
    if any(w in msg_lower for w in ["trade", "signal", "buy", "sell", "hold", "entry", "position", "should i"]):
        failed = [k for k, v in gate_log.items() if v is False]
        if decision == "HOLD":
            return (
                f"📊 Current Signal: {decision} (Regime: {regime})\n\n"
                f"Right now the system is on HOLD because {len(failed)} safety gate(s) haven't passed yet.\n"
                f"Failed gates: {', '.join(failed) if failed else 'checking...'}\n\n"
                "The AI won't generate a BUY or SELL until all 7 gates pass simultaneously. "
                "This protects you from taking trades in unfavorable conditions.\n\n"
                "💡 Ask me 'why HOLD?' for a detailed gate-by-gate breakdown!"
            )
        else:
            return (
                f"📊 Current Signal: {decision} (Regime: {regime})\n\n"
                f"Confidence: {signal.get('ensemble_probability', 'N/A')}\n"
                f"All 7 safety gates have passed! The system has generated a {decision} signal.\n\n"
                "Check the Signal Timeline on the right for full details."
            )

    return (
        "Hey! I'm ForeXtron, your AI trading assistant 🧠\n\n"
        f"Current Market: {decision} signal | {regime} regime\n\n"
        "I can help with:\n"
        "• Signals: 'Why HOLD?' or 'What's the current signal?'\n"
        "• Forex concepts: 'What is a pip?' or 'Explain BoS'\n"
        "• Platform: 'Where is the Trade Journal?'\n"
        "• Architecture: 'How does PatchTST work?'\n\n"
        "What would you like to know?"
    )

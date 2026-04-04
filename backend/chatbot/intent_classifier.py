"""
intent_classifier.py – Keyword-based intent routing for the chatbot.
"""

import re
from typing import Tuple

INTENTS = {
    "hello_help": [
        r"hello", r"hi", r"help", r"what can you do", r"how do i use this",
    ],
    "explain_signal": [
        r"why (hold|buy|sell)", r"explain (signal|decision|recommendation)",
        r"what (is|does) the (signal|recommendation|decision)",
        r"current (signal|call|recommendation)", r"should i (buy|sell)",
    ],
    "show_performance": [
        r"win rate", r"performance", r"how (are we|is it) doing",
        r"return", r"profit", r"loss", r"expectancy", r"sharpe",
    ],
    "regime_inquiry": [
        r"regime", r"market condition", r"expansion|accumulation|exhaustion",
        r"what phase", r"volatility state",
    ],
    "explain_concept": [
        r"what is (bos|choch|fvg|order block|liquidity sweep|impulse|hurst|monte carlo|xai|safety gates)",
        r"explain (bos|choch|fvg|structure|sweep|imbalance|impulse|monte carlo|xai|safety gates)",
        r"define", r"how does.*work",
    ],
    "learn_forex": [
        r"what is (a )?(pip|spread|leverage|lot|margin|drawdown|candlestick|candle|bar)",
        r"what is (a )?(stop loss|take profit|risk reward|lot size|position size)",
        r"what is (a )?(win rate|expectancy|sharpe|regime|ensemble|order block|monte carlo|xai|safety gates)",
        r"explain (pip|spread|leverage|lot|margin|stop loss|take profit|candlestick|monte carlo|xai|safety gates)",
        r"explain (win rate|expectancy|sharpe|drawdown|regime|ensemble|order block|journal|timeline)",
        r"how (do|does|is) (pip|spread|leverage|lot|margin|stop loss).*(work|calculated|set)",
        r"(teach|learn|understand|help me with) (forex|trading|currency)",
        r"(beginner|new to|starting|just started)",
        r"what does (pip|spread|sl|tp|rr|bos|choch|fvg|rrr) mean",
        r"(pip|spread|leverage|margin|lot size|drawdown|sharpe|expectancy|rsi|candle|monte carlo|xai) meaning",
    ],
    "risk_inquiry": [
        r"risk", r"drawdown", r"trades today", r"guardian", r"hold mode",
        r"position size", r"stop loss", r"take profit",
    ],
    "trade_history": [
        r"recent trade", r"last trade", r"trade log", r"trade history",
    ],
    "inr_inquiry": [
        r"(usd|eur|gbp)[\s_]?inr", r"indian rupee", r"rupee", r"inr",
    ],
    "navigate_website": [
        r"dark mode", r"theme", r"trade journal", r"journal", r"history",
        r"timeline", r"price ticker", r"ticker", r"demo trade", r"place trade",
        r"dashboard", r"features", r"new features",
    ],
}


def classify_intent(message: str) -> Tuple[str, float]:
    """
    Returns (intent_name, confidence_score).
    Falls back to "explain_signal" if nothing matches.
    """
    text = message.lower().strip()
    scores = {}

    for intent, patterns in INTENTS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text):
                score += 1
        if score > 0:
            scores[intent] = score

    if scores:
        best = max(scores, key=scores.get)
        confidence = min(1.0, scores[best] / 3)
        return best, confidence

    return "open_query", 0.4

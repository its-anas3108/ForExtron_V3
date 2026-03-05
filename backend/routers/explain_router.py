"""
explain_router.py – GET /api/explain/{term}
Returns a plain-English explanation of any Forex term.
Tries Gemini first, falls back to built-in FOREX_GLOSSARY.
"""

from fastapi import APIRouter
from chatbot.llm_engine import FOREX_GLOSSARY
from app.config import settings

router = APIRouter(tags=["education"])


@router.get("/explain/{term}")
async def explain_term(term: str):
    """Return a plain-English explanation of a Forex term."""
    term_lower = term.lower().replace("-", " ").replace("_", " ")

    # Try exact or partial glossary match first (fast, free, offline)
    if term_lower in FOREX_GLOSSARY:
        return {"term": term, "explanation": FOREX_GLOSSARY[term_lower], "source": "glossary"}

    # Try partial match (e.g. "stops" → "stop loss")
    for key, val in FOREX_GLOSSARY.items():
        if term_lower in key or key in term_lower:
            return {"term": term, "explanation": val, "source": "glossary"}

    # Fallback: ask Gemini for a beginner-friendly explanation
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.LLM_MODEL_GEMINI)
            prompt = (
                f"You are a friendly Forex educator. Explain the Forex trading term '{term}' "
                "in 3–4 simple sentences. Start with a plain-English definition, add a real-world "
                "analogy, then give the technical detail. Use an emoji at the start."
            )
            response = model.generate_content(prompt)
            return {"term": term, "explanation": response.text.strip(), "source": "gemini"}
        except Exception as e:
            pass

    return {
        "term": term,
        "explanation": (
            f"📌 **{term.upper()}** — I don't have a specific definition for this term yet. "
            "Try asking the chatbot: type 'What is " + term + "?' in the chat panel below!"
        ),
        "source": "fallback",
    }


@router.get("/explain")
async def list_terms():
    """Return all Forex terms available in the built-in glossary."""
    return {
        "available_terms": sorted(FOREX_GLOSSARY.keys()),
        "count": len(FOREX_GLOSSARY),
        "tip": "GET /api/explain/{term} for a plain-English definition of any term.",
    }

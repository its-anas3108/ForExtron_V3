"""
chat_router.py – POST /api/chat
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from database.models import ChatRequest
from database.crud import save_chat_message, get_chat_history
from chatbot.intent_classifier import classify_intent
from chatbot.context_builder import build_context
from chatbot.llm_engine import generate_response

router = APIRouter(tags=["chatbot"])


@router.post("/chat")
async def chat(request: ChatRequest):
    intent, confidence = classify_intent(request.message)
    context = await build_context(request.instrument)
    response_text = await generate_response(intent, context, request.message)

    ts = datetime.now(timezone.utc).isoformat()

    # Save user message
    await save_chat_message({
        "session_id": request.session_id,
        "role": "user",
        "message": request.message,
        "intent": intent,
        "context_data": {},
        "timestamp": ts,
    })

    # Save assistant response
    await save_chat_message({
        "session_id": request.session_id,
        "role": "assistant",
        "message": response_text,
        "intent": intent,
        "context_data": {},
        "timestamp": ts,
    })

    return {
        "response": response_text,
        "intent": intent,
        "intent_confidence": round(confidence, 3),
        "timestamp": ts,
    }


@router.get("/chat/history/{session_id}")
async def chat_history(session_id: str, limit: int = 20):
    return await get_chat_history(session_id, limit=limit)

"""
news_router.py – News Impact Engine API
GET /api/news/feed       – latest macro news events
GET /api/news/impact/{pair} – pair-specific news impact
"""

from fastapi import APIRouter
from features.news_engine import get_news_feed, get_pair_news_impact

router = APIRouter(tags=["news"])


@router.get("/news/feed")
async def news_feed(count: int = 10):
    events = await get_news_feed(min(count, 20))
    return {"events": events, "count": len(events)}


@router.get("/news/impact/{pair}")
async def news_impact(pair: str):
    return await get_pair_news_impact(pair.upper())

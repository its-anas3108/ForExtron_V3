"""
crud.py – Async MongoDB CRUD operations using Motor.
"""

import os
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db = None

# ── In-memory fallback when MongoDB is unavailable ────────────────────────────
_mem_candles: List[dict] = []
_mem_signals: List[dict] = []
_MEM_CANDLE_LIMIT = 500
_MEM_SIGNAL_LIMIT = 200


async def init_db():
    global _client, _db
    try:
        # Strict 2-second timeout for MongoDB selection to prevent application startup hang
        _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        _db = _client[settings.MONGO_DB_NAME]
        
        # Immediate connection test to bypass potential Motor hang later
        await _client.admin.command('ping')
        
        # Create indexes
        await _db.candles.create_index([("pair", 1), ("timestamp", -1)])
        await _db.signals.create_index([("pair", 1), ("timestamp", -1)])
        await _db.trades.create_index([("pair", 1), ("entry_time", -1)])
        await _db.agent_logs.create_index([("timestamp", -1)])
        logger.info(f"✅ MongoDB connected: {settings.MONGO_DB_NAME}")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB connection failed ({e}). Falling back to Local Persistence (data/users.json).")
        _client = None
        _db = None


def _get_db():
    return _db

_USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")

def _load_mem_users():
    if os.path.exists(_USERS_FILE):
        try:
            with open(_USERS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load users from json fallback: {e}")
            return []
    return []

def _save_mem_users():
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(_USERS_FILE), exist_ok=True)
        with open(_USERS_FILE, "w") as f:
            json.dump(_mem_users, f, indent=4)
        logger.info(f"✅ User data persisted locally to {_USERS_FILE}")
    except Exception as e:
        logger.error(f"❌ Failed to save users to json fallback: {e}")

_mem_users = _load_mem_users()

# ── Users ──────────────────────────────────────────────────────────────────────
async def create_user(user: dict):
    db = _get_db()
    if db is not None:
        result = await db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user
    
    import uuid
    user["_id"] = str(uuid.uuid4())
    _mem_users.append(user)
    _save_mem_users()
    return user

async def get_user_by_email(email: str) -> Optional[dict]:
    db = _get_db()
    if db is not None:
        user = await db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    matches = [u for u in _mem_users if u.get("email") == email]
    return matches[0] if matches else None

async def update_user_balance(email: str, new_balance: float):
    db = _get_db()
    if db is not None:
        await db.users.update_one({"email": email}, {"$set": {"balance": new_balance}})
    else:
        for u in _mem_users:
            if u.get("email") == email:
                u["balance"] = new_balance
                _save_mem_users()
                break
# ── Candles ────────────────────────────────────────────────────────────────────
async def insert_candle(candle: dict):
    db = _get_db()
    if db is not None:
        await db.candles.update_one(
            {"pair": candle["pair"], "timestamp": candle["timestamp"]},
            {"$set": candle},
            upsert=True,
        )
    else:
        _mem_candles.append(candle)
        if len(_mem_candles) > _MEM_CANDLE_LIMIT:
            _mem_candles.pop(0)


async def get_recent_candles(pair: str, limit: int = 200, timeframe: str = "M5") -> List[dict]:
    db = _get_db()
    if db is not None:
        cursor = db.candles.find(
            {"pair": pair, "timeframe": timeframe},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return list(reversed(docs))
    else:
        filtered = [c for c in _mem_candles if c.get("pair") == pair and c.get("timeframe", "M5") == timeframe]
        return filtered[-limit:]


# ── Signals ────────────────────────────────────────────────────────────────────
async def insert_signal(signal: dict):
    db = _get_db()
    if db is not None:
        await db.signals.insert_one(signal)
    else:
        _mem_signals.append(signal)
        if len(_mem_signals) > _MEM_SIGNAL_LIMIT:
            _mem_signals.pop(0)


async def get_latest_signal(pair: str) -> Optional[dict]:
    db = _get_db()
    if db is not None:
        doc = await db.signals.find_one(
            {"pair": pair}, {"_id": 0}, sort=[("timestamp", -1)]
        )
        return doc
    else:
        matches = [s for s in _mem_signals if s.get("pair") == pair]
        return matches[-1] if matches else None


async def get_signals_history(pair: str, limit: int = 50) -> List[dict]:
    db = _get_db()
    if db is not None:
        cursor = db.signals.find(
            {"pair": pair}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    else:
        matches = [s for s in _mem_signals if s.get("pair") == pair]
        return list(reversed(matches[-limit:]))


_mem_trades = []

# ── Trades ─────────────────────────────────────────────────────────────────────
async def insert_trade(trade: dict):
    db = _get_db()
    if db is not None:
        await db.trades.insert_one(trade)
    else:
        _mem_trades.append(trade)


async def get_recent_trades(pair: str = None, limit: int = 20) -> List[dict]:
    db = _get_db()
    if db is None: return []
    query = {"pair": pair} if pair else {}
    cursor = db.trades.find(query, {"_id": 0}).sort("entry_time", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def get_recent_trades_by_user(email: str, limit: int = 20) -> List[dict]:
    db = _get_db()
    if db is not None:
        query = {"user_email": email}
        cursor = db.trades.find(query, {"_id": 0}).sort("entry_time", -1).limit(limit)
        return await cursor.to_list(length=limit)
    else:
        filtered = [t for t in _mem_trades if t.get("user_email") == email]
        return list(reversed(filtered[-limit:]))


async def update_trade_result(trade_id: str, result: dict):
    db = _get_db()
    if db is None: return
    await db.trades.update_one({"_id": trade_id}, {"$set": result})


# ── Agent Logs ─────────────────────────────────────────────────────────────────
async def log_agent_event(event: dict):
    db = _get_db()
    if db is None: return
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    await db.agent_logs.insert_one(event)


async def get_agent_logs(limit: int = 50) -> List[dict]:
    db = _get_db()
    if db is None: return []
    cursor = db.agent_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ── Performance Metrics ────────────────────────────────────────────────────────
async def upsert_metrics(metrics: dict):
    db = _get_db()
    if db is None: return
    await db.performance_metrics.update_one(
        {"pair": metrics["pair"], "period": metrics.get("period", "daily")},
        {"$set": metrics},
        upsert=True,
    )


async def get_metrics(pair: str) -> Optional[dict]:
    db = _get_db()
    if db is None: return None
    return await db.performance_metrics.find_one({"pair": pair}, {"_id": 0})


# ── Chat History ───────────────────────────────────────────────────────────────
async def save_chat_message(message: dict):
    db = _get_db()
    if db is None: return
    await db.chat_history.insert_one(message)


async def get_chat_history(session_id: str, limit: int = 20) -> List[dict]:
    db = _get_db()
    if db is None: return []
    cursor = db.chat_history.find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return list(reversed(docs))

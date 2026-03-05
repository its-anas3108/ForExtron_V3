# ForEX Pro – Institutional Agentic AI Forex Intelligence Platform

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Copy and fill your .env
copy .env.example .env
# Edit .env: add OANDA_API_KEY, OANDA_ACCOUNT_ID, MONGO_URI, GEMINI_API_KEY

pip install -r requirements.txt

# Create model directory
mkdir models\saved

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## 📁 Folder Structure
```
ForEX/
├── backend/
│   ├── app/          # FastAPI: main, config, websocket
│   ├── data/         # OANDA client, stream handler, validator
│   ├── features/     # Indicators, structure engine, regime features
│   ├── models/       # Regime (XGBoost), DNN, GRU, CNN, Transformer, Ensemble
│   ├── agents/       # Risk Guardian, Drift, Threshold, Supervisor
│   ├── decision/     # Decision engine (7-gate), risk engine
│   ├── execution/    # Manual-confirm order gateway
│   ├── chatbot/      # Intent classifier, context builder, Gemini/OpenAI LLM
│   ├── database/     # Motor (MongoDB) CRUD + Pydantic models
│   ├── monitoring/   # Performance metrics, drift detection
│   ├── retraining/   # Automated retrain pipeline
│   └── routers/      # FastAPI route handlers
└── frontend/
    └── src/
        ├── pages/      # Dashboard.jsx
        ├── components/ # SignalCard, LiveChart, AnalyticsPanel, ChatPanel, RegimeBadge, AgentStatusBar
        └── services/   # api.js, websocket.js
```

---

## 🌐 Supported Instruments
| Pair | Type | Notes |
|------|------|-------|
| EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CHF, USD_CAD, NZD_USD | Major | Full tick streaming |
| USD_INR, EUR_INR, GBP_INR | INR 🇮🇳 | Poll-based (10s interval) |

---

## 🔑 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signal/{pair}` | Latest AI signal |
| GET | `/api/regime/{pair}` | Volatility regime |
| GET | `/api/performance/{pair}` | Win rate, drawdown, Sharpe |
| GET | `/api/agents/status` | All agent health |
| POST | `/api/chat` | Conversational AI |
| POST | `/api/execute` | Trade execution (disabled by default) |
| WS | `/ws/live/{instrument}` | Live candle + signal stream |

---

## 🤖 ML/DL Ensemble
| Model | Weight | Purpose |
|-------|--------|---------|
| Logistic Regression | 10% | Baseline stability |
| DNN (BatchNorm+Dropout) | 20% | Feature-based prediction |
| GRU (Stacked) | 30% | Temporal sequences |
| CNN (Conv1D) | 25% | Pattern recognition |
| Transformer | 15% | Long-range attention |

---

## 🏛️ Decision Gates (ALL must pass for BUY)
1. Regime = Expansion
2. Structure bias = Bullish (BoS + HH/LL + slope)
3. Liquidity sweep below confirmed
4. Ensemble probability > dynamic threshold (0.65–0.75)
5. RSI < 70 (not overbought)
6. R:R ≥ 1:2
7. Risk Guardian approval (drawdown + trade count)

---

## ⚠️ Important Notes
- **Execution is DISABLED by default** — set `EXECUTION_ENABLED = True` in `execution_router.py` manually
- The practice OANDA URL is set by default (`api-fxpractice.oanda.com`)
- INR pairs use poll-based data, not tick streaming
- Models start untrained — use the retrain pipeline or seed with historical data
- Set your `GEMINI_API_KEY` for full chatbot capability (free via Google AI Studio)

---

*ForEX Pro v2.0 – Research-level fintech platform. Not financial advice.*

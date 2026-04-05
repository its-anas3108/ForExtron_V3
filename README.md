<div align="center">
  <br />
  <h1>📈 ForeXtron</h1>
  <p><strong>Institutional Agentic AI Forex Intelligence Platform</strong></p>
  <p>
    Built with <strong>FastAPI, React, Deep Learning (PatchTST/TCN/TFT), and Autonomous Agents</strong>
  </p>
  <br />
</div>

<hr />

## 🌟 Overview

**Forextron** is a sophisticated, research-grade financial technology platform engineered for real-time Forex market analysis. Transitioning from legacy architectures to a unified, state-of-the-art Deep Learning framework (Forextron v3), it leverages multi-horizon temporal forecasting and an intricate multi-agent decision engine to generate highly robust trading intelligence.

Unlike conventional platforms, Forextron integrates native drift detection, persistent user authentication, structural market analysis, and a specialized multi-layered news intelligence system with LLM-powered rationale.

---

## 🚀 Quick Start

### 1. Environment & Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate Python virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Environment Variables Configuration
copy .env.example .env
# Important: Edit .env to add your OANDA_API_KEY, OANDA_ACCOUNT_ID, MONGO_URI, and GEMINI_API_KEY

# Ensure proper directories exist
mkdir -p models/saved

# Launch the FastAPI Server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
# The dashboard is now accessible at http://localhost:5173
```

---

## 🏛️ System Architecture Tracker

```text
ForeXtron/
├── backend/
│   ├── app/          # Core FastAPI instances, DI config, WebSockets
│   ├── data/         # OANDA connectivity (Tick streaming & Polling variants)
│   ├── features/     # Real-time Indicators, Market Structure Engine, Regime Analysis
│   ├── models/       # Deep Learning Core: Forextron v3 (PatchTST, TCN, TFT, GRN)
│   ├── agents/       # Multi-Agent Engine: Risk Guardian, Drift, Threshold, Supervisor
│   ├── decision/     # Multi-gated algorithmic execution evaluator
│   ├── execution/    # Gateway to broker (Manual confirmation by default)
│   ├── chatbot/      # Gemini/OpenAI-powered conversational context loop
│   ├── database/     # Motor (MongoDB) asynchronous CRUD routines
│   ├── monitoring/   # Telemetry, win/loss stats, analytics tracking
│   ├── retraining/   # Automated local continuous learning pipeline
│   └── routers/      # API entrypoints
└── frontend/
    └── src/
        ├── pages/      # Master Views (e.g., Dashboard.jsx)
        ├── components/ # Widgets (SignalCard, LiveChart, AnalyticsPanel, ChatPanel, AgentStatusBar)
        ├── context/    # React Context providers (Auth, Theme)
        └── services/   # REST wrappers and WebSocket integrators
```

---

## 🧠 Deep Learning Paradigm: Forextron v3
Forextron's evolution introduces a unified research-grade neural pipeline optimized explicitly for non-stationary financial time series.

| Architectural Component | Functionality |
|-------------------|-----------------------------------------------------------------------------------------|
| **Feature Embedding** | Projects raw continuous/categorical structural data into dense vector space. |
| **PatchTST** | Splits temporal data into localized non-overlapping segments (patches) to identify short-term phenomena without recurrent memory bottlenecks. |
| **TCN (Temporal CNN)** | Employs causal dilated 1D convolutions ensuring rigid temporal boundaries avoiding data-leakage while establishing a wide mathematical receptive field. |
| **Temporal Fusion Transformer (TFT)**| Utilizes multi-head attention to dynamically learn variable importance across disparate time blocks. |
| **GRN & Regime Context**| Feature gating that actively routes signals based on detected market volatility (Expansion vs Contraction). |

---

## 🛡️ The 7-Gate Algorithmic Decision Engine
To protect capital, Forextron will **NEVER** issue a BUY or SELL signal unless **ALL** 7 conditions below are met:

1. **Regime Validation**: Market currently in an Expansion state.
2. **Structural Confirmation**: Aligned market geometry (e.g., Break of Structure, Higher Highs/Lower Lows, proper Moving Average slope).
3. **Liquidity Sweep**: Confirmed trigger of buy-side/sell-side liquidity zones below structural points.
4. **Ensemble Integrity**: ML Probability Score > Dynamic Agent-set Threshold (0.65+).
5. **Momentum Caps**: RSI < 70 (Safeguarding against executing at absolute exhaustion points).
6. **Mathematical Risk Profile**: Evaluated minimum R:R of 1:2.
7. **Risk Guardian Sanction**: Final check validating maximum acceptable account drawdown and daily trade limits.

---

## 🌐 Supported Instrumentation
| Instrument | Category | Connectivity Flow |
|-------------|----------|-------------------|
| EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CHF, USD_CAD, NZD_USD | Majors | WebSockets: Immediate Tick Streaming (via dedicated Executor) |
| USD_INR, EUR_INR, GBP_INR | Regional | REST Polling: 10-second batched fetch |

---

## 🛠️ Performance & Robustness Features
Recent upgrades have hardened the platform for production-like reliability:
- **Multi-Layered News Intelligence**: A redundant fetch cycle (Finnhub → Forex Factory → Synthetic AI Fallback) ensures the news feed is never empty.
- **Dedicated Concurrency**: A specialized `ThreadPoolExecutor` handles blocking OANDA I/O, preventing event-loop starvation and ensuring 100% API responsiveness.
- **Seamless Charting**: The `LiveChart` features custom candlestick rendering with auto-seeding and synthetic "no-blank" data fallbacks.
- **Data Sanitization**: Automatic handling of NaN/Inf values across the indicator pipeline ensures stable UI rendering.

---

## 🔌 API Endpoints
*Forextron runs on REST logic backed by WebSockets for instantaneous metric delivery.*

| Method | Endpoint | Description |
|---|---|---|
| **GET** | `/api/signal/{pair}` | Retrieve the immediate deterministic signal output. |
| **GET** | `/api/regime/{pair}` | Access current market volatility state. |
| **GET** | `/api/performance/{pair}` | Fetches Win rates, Drawdown, and Sharpe metrics. |
| **GET** | `/api/agents/status` | Heartbeat check for the swarm of logical agents. |
| **POST**| `/api/chat` | Interface point for Natural Language interrogations. |
| **POST**| `/api/execute` | Immediate Order relay (Requires `EXECUTION_ENABLED = True`). |
| **WS**  | `/ws/live/{instrument}` | Subscribes to real-time candles & live intelligence stream. |

---

## ⚠️ Important Operating Directives
- **Failsafe Executions**: Broker-side execution is heavily barricaded in `execution_router.py`. Flip `EXECUTION_ENABLED = True` **only** under supervision or in isolated cloud instances.
- **Broker Connectivity**: Default OANDA configuration attaches to `api-fxpractice.oanda.com`.
- **Database Modularity**: Recent fixes enforce completely persistent user sessions over MongoDB mappings. Do not flush the DB loosely if user-roles are actively stored.
- **LLM Frequencies**: `GEMINI_API_KEY` is highly recommended to enable seamless local conversational chatbot analysis (accessible for free via Google AI Studio).

<div align="center">
  <sub>ForeXtron v3.0 // Institutional Analytics Framework. <em>This code remains strictly for academic, research, and non-financial demonstration purposes.</em></sub>
</div>

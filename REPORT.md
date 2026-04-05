# Forextron Project Report

## Executive Summary
Forextron is an advanced, institutional-grade AI-powered Forex intelligence and algorithmic trading platform. It leverages state-of-the-art Deep Learning models (Forextron v3) alongside an intricate agentic decision engine to provide highly reliable, regime-aware Forex signals. It encompasses a multi-faceted architecture comprising a real-time data ingestion pipeline connected to the OANDA API, a complex deep-learning prediction model, a rule-based agentic decision framework, and a modern React-based frontend dashboard.

## System Architecture Overview

Forextron utilizes a decoupled client-server architecture:
- **Backend**: Built with Python and FastAPI, handling complex data streaming, ML inference, and agentic workflows.
- **Frontend**: A React and Vite-based web application providing a dynamic, real-time dashboard for traders to monitor signals, regime shifts, and agent statuses.
- **Database**: MongoDB (via Motor asynchronous driver) for persistent data storage, including user authentication and historical performance metrics.

### Backend Components
The backend is structured into distinct, highly modular modules:
1. **Data Ingestion (`backend/data/`)**: Stream handlers, validators, and a robust client for OANDA API integration (streaming and polling depending on instrument type).
2. **Feature Engineering (`backend/features/`)**: Calculates critical market dynamics, including technical indicators, market structure, and liquidity sweeps. Continually assesses the current market regime.
3. **Deep Learning Models (`backend/models/`)**: Houses the **Forextron v3** architecture:
    - **PatchTST**: Non-recurrent temporal segmentation for local patterns.
    - **TCN (Temporal Convolutional Networks)**: Ensures rigid temporal stability through causal dilated convolutions.
    - **TFT (Temporal Fusion Transformer)**: Bridging sequence representations.
    - **GRN (Gated Residual Networks)**: Structural noise filtering.
4. **Agentic System (`backend/agents/`)**: 
    - **Risk Guardian**: Evaluates account drawdowns and position sizing.
    - **Drift Agent**: Detects concept drift in model predictions natively.
    - **Threshold Agent**: Dynamically adjusts confidence thresholds based on volatility.
    - **Supervisor**: Aggregates health and performance metrics across the system.
5. **Decision Engine (`backend/decision/`)**: Implements a strict 7-Gate decision protocol ensuring that trades are only executed or signaled when rigorous qualitative, quantitative, and risk-management conditions are met.
6. **Execution (`backend/execution/`)**: A dedicated module for order placement on OANDA (disabled by default for safety).
7. **Conversational AI (`backend/chatbot/`)**: Integrates LLMs (Google Gemini/OpenAI) to assist users with natural language queries regarding the platform's analysis and metrics.

### Frontend Components
Built entirely with React (`frontend/src/`) and styled elegantly:
- **Dashboard (`pages/Dashboard.jsx`)**: The primary analytical canvas.
- **Micro-Components (`components/`)**: Comprises discrete UI widgets including `LiveChart`, `SignalCard`, `AnalyticsPanel`, `RegimeBadge`, `AgentStatusBar`, and `ChatPanel`.
- **Services (`services/`)**: Interfaces with the backend via REST APIs (`api.js`) and WebSockets (`websocket.js`) for split-second updates.

## Forextron v3 Details
Forextron's evolution from a discrete model ensemble to the unified v3 deep learning framework marks a paradigm shift in its accuracy:
- **Unified Pipeline**: Removes legacy RNN/GRU constraints, optimizing multi-horizon forecasting speeds.
- **Multi-Head Output**: Outputs not just deterministic directions, but probabilistic bounds via Sigmoid (direction) and MSE (Regression/Volatility prediction).
- **Regime-Aware Context gating**: Models behave differently under Expansion versus Contraction regimes. 

## The 7-Gate Decision Protocol
A unique feature of Forextron is its rigorous gate system that operates entirely autonomously:
1. Regime evaluation (Must be Expanding)
2. Structural alignment (Breaks of Structure / Higher Highs / Lower Lows)
3. Liquidity sweep confirmation
4. High Dynamic Ensemble Probability Threshold
5. Non-extreme RSI limits
6. Generous Risk-to-Reward ratio projection
7. Explicit Risk Guardian Approval

## Recent Improvements and Upgrades
Based on recent development logs, Forextron has been rapidly advancing:
- **News Engine Robustness**: Implemented a triple-redundant news engine (Finnhub → Forex Factory → Synthetic AI). This ensures that even if local connectivity to news servers is degraded, the AI can still generate contextually relevant macro-sentiments. Fixed internal data structure bugs and duplicated LLM task logic.
- **Frontend Charting Resilience**: Fixed the `LiveChart` to ensure candlesticks are always visible regardless of initial DB state. Developed a custom Recharts component for proper OHLC representation and integrated an auto-seeding mechanism for historical data retrieval.
- **Backend Concurrency Optimization**: Migrated blocking OANDA I/O operations (streaming and polling) to a dedicated `ThreadPoolExecutor`. This architecture ensures the FastAPI event loop remains responsive to UI requests even during intensive data streaming.
- **Auth & State Persistence**: Fully resolved session context issues, ensuring that user metrics, account states, and UI preferences are persistently stored in MongoDB.
- **Data Integrity Layer**: Added a robust sanitization sweep throughout the backend indicator engine to gracefully handle and convert NaN/Inf values, preventing frontend rendering errors.

## Conclusion and Future Roadmap
Forextron stands as a completely self-sufficient forecasting system designed for rigorous academic and practical financial execution. With core features like charting, news intelligence, and backend stability now fully optimized and functional, future improvements will focus on expanding the LLM-driven autonomous trading agents and enhancing the backtesting and trade-replay functionalities.

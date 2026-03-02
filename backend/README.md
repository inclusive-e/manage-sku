# SKU Forecasting API

FastAPI backend for SKU sales forecasting using rule-based heuristics.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                               │
│  Data Upload → Dashboard → Sales Charts → Forecasts → Metrics              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTP
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                               │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Upload  │  │  Sales   │  │Forecasts │  │ Metrics  │  │   Pred.  │       │
│  │   API    │  │   API    │  │   API    │  │   API    │  │   API    │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICES LAYER                                    │
│                                                                             │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────┐        │
│  │  DataProcessor   │   │ FeatureEngineer  │   │AnalysisPipeline   │        │
│  │  • CSV cleaning │──▶│  • Lag features  │──▶│  • Pattern detect  │        │
│  │  • Fill gaps    │   │  • Rolling stats │   │  • Method select   │        │
│  │  • Daily series │   │  • Calendar      │   │  • Backtest        │        │
│  └──────────────────┘   └──────────────────┘   └─────────┬──────────┘        │
│                                                          │                  │
│  ┌──────────────────────────────────────────────────────┐  │                │
│  │              HeuristicForecaster                      │◀─┘                │
│  │  • naive          • seasonal_naive                    │                   │
│  │  • rolling_mean   • weighted_average                  │                   │
│  │  • with_trend    • croston (intermittent)            │                   │
│  └──────────────────────────────────────────────────────┘                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            POSTGRES DATABASE                                │
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │ raw_uploads │   │ sales_data  │   │  features   │   │ predictions │    │
│  │ (metadata)  │──▶│ (daily series)──▶│ (engineered)│──▶│ (results)   │    │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘    │
│                                                                             │
│  source_type: 'user' (real) | 'system' (filled gaps)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
CSV Upload
    │
    ▼
┌─────────────────┐
│  1. Upload      │ POST /api/v1/upload/
│     (file save) │
└────────┬────────┘
         │ raw_uploads.id
         ▼
┌─────────────────────────────┐
│  2. Process                 │ POST /api/v1/sales/{id}/process
│     • Clean columns         │
│     • Fill date gaps        │────▶ sales_data (complete daily series)
│     • source_type           │      source_type: user/system
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  3. Feature Engineering    │ POST /api/v1/forecasts/{id}/features
│     • lag_7d, lag_28d       │
│     • rolling_mean_7d/28d  │────▶ features table
│     • day_of_week           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  4. Forecast                │ POST /api/v1/forecasts/generate
│     • Analyze patterns      │
│     • Select best method    │────▶ predictions (with reasoning)
│     • Backtest & generate  │
└─────────────────────────────┘
```

---

## API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/api/v1/upload/` | POST | Upload CSV/Excel |
| `/api/v1/upload/` | GET | List uploads |
| `/api/v1/sales/{upload_id}/process` | POST | Process → daily series |
| `/api/v1/sales/{upload_id}` | GET | Get processed data |
| `/api/v1/forecasts/generate` | POST | Generate forecasts |
| `/api/v1/forecasts/{id}/features` | POST | Generate features |
| `/api/v1/forecasts/{id}/accuracy` | GET | Backtest results |
| `/api/v1/metrics/{upload_id}/sales` | GET | Sales performance |
| `/api/v1/metrics/{upload_id}/product` | GET | Product performance |

---

## Forecasting Methods

| Method | Use Case |
|--------|----------|
| `naive` | Last observed value |
| `rolling_mean_7d` | Short-term average |
| `rolling_mean_28d` | Long-term average |
| `seasonal_naive` | Same time last season |
| `weighted_average` | Blended recent + long-term |
| `with_trend` | Continues growth/decline |
| `croston` | Intermittent demand |

**Auto-selection**: AnalysisPipeline analyzes data patterns → backtests candidates → selects best

---

## Quick Start

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
cp .env.example .env
psql -U postgres -d sku_db -f migrations/001_create_core_tables.sql

# Run
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

---

## Tech Stack

- FastAPI (async)
- PostgreSQL + asyncpg
- Pandas, NumPy
- statsmodels (analysis)

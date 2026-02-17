# SKU Prediction API

FastAPI backend for SKU (Stock Keeping Unit) sales forecasting using rule-based heuristics. No ML models required for MVP - forecasts work immediately.

## Quick Start

```bash
# 1. Setup environment
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Setup database (PostgreSQL must be running)
cp .env.example .env
# Edit .env with your database credentials

# 3. Run migrations
psql -U postgres -d sku_db -f migrations/001_create_core_tables.sql

# 4. Start server
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│   PostgreSQL    │
│  (React/TS)     │◀────│   Backend       │◀────│   (sku_db)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Upload     │    │   Data Pipeline  │    │   Forecasting    │
│   Service    │───▶│                  │───▶│   Service        │
└──────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Data Flow

### 1. File Upload (`POST /api/v1/upload/`)
- User uploads CSV/Excel with sales data
- File saved to `uploads/` directory
- Record created in `raw_uploads` table (status: "uploaded")

### 2. Data Processing (`POST /api/v1/sales/{upload_id}/process`)
- Reads uploaded file
- Cleans column names, infers types
- **Transforms to complete daily time series** (no date gaps)
- Marks rows as `source_type='user'` (from CSV) or `source_type='system'` (filled gaps)
- Saves to `sales_data` table
- Updates `raw_uploads.status` to "processed"

### 3. Feature Engineering (`POST /api/v1/forecasts/{upload_id}/features/generate`)
- Reads from `sales_data`
- Generates 10 features per SKU per day:
  - **Lags**: `lag_7d`, `lag_28d` (previous sales)
  - **Rolling**: `rolling_mean_7d`, `rolling_mean_28d` (trends)
  - **Calendar**: `day_of_week`, `week_of_year` (seasonality)
- Saves to `features` table

### 4. Forecast Generation (`POST /api/v1/forecasts/generate`)
- Reads features for SKU
- Runs 6 heuristic methods, auto-selects best
- Returns weekly forecasts with confidence intervals

---

## Database Schema

### `raw_uploads` - File Upload Metadata
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Upload identifier |
| filename | VARCHAR(255) | Original filename |
| file_path | VARCHAR(500) | Path on disk |
| status | VARCHAR(50) | uploaded/processing/processed/error |
| detected_schema | JSONB | Auto-detected column types |
| uploaded_at | TIMESTAMP | When uploaded |

### `sales_data` - Clean Daily Sales Data
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| upload_id | UUID | Links to raw_uploads |
| date | TIMESTAMP | Date (no timezone) |
| sku_id | VARCHAR(100) | Product identifier |
| sales_quantity | FLOAT | Units sold |
| unit_price | FLOAT | Price per unit |
| **source_type** | VARCHAR(20) | **'user' = from CSV, 'system' = filled gaps** |
| created_at | TIMESTAMP | Auto-generated |

### `features` - Engineered Features
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| upload_id | UUID | Links to raw_uploads |
| sku_id | VARCHAR(100) | Product identifier |
| date | TIMESTAMP | Date |
| sales_quantity | FLOAT | Target variable |
| lag_7d | FLOAT | Sales 7 days ago |
| lag_28d | FLOAT | Sales 28 days ago |
| rolling_mean_7d | FLOAT | 7-day average |
| rolling_mean_28d | FLOAT | 28-day average |
| day_of_week | INTEGER | 0=Monday, 6=Sunday |
| week_of_year | INTEGER | 1-53 |

### `predictions` - Forecast Results
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| input_data | JSONB | Request parameters |
| prediction_result | JSONB | Forecast output |
| created_at | TIMESTAMP | When generated |

---

## Key Concepts

### Complete Daily Time Series
Raw CSV data often has gaps (days with no sales). We transform this:

**Before (sparse CSV data):**
```
2024-01-01, SKU001, 10
2024-01-05, SKU001, 15  <- 3-day gap!
2024-01-10, SKU001, 20  <- 4-day gap!
```

**After (dense daily series):**
```
2024-01-01, SKU001, 10,  user
2024-01-02, SKU001, 0,   system  <- filled
2024-01-03, SKU001, 0,   system  <- filled
2024-01-04, SKU001, 0,   system  <- filled
2024-01-05, SKU001, 15,  user
2024-01-06, SKU001, 0,   system  <- filled
...
```

The `source_type` column tracks which rows are real data vs. filled gaps.

### Heuristic Forecasting (No ML)
We use 6 rule-based methods:

1. **naive** - Last observed value
2. **rolling_mean_7d** - Average of last 7 days
3. **rolling_mean_28d** - Average of last 28 days
4. **seasonal_naive** - Value from same time last season
5. **weighted_average** - 50% last 7d + 30% last 28d + 20% overall
6. **with_trend** - Last value + projected trend

Auto-selection picks the best method via backtesting on recent data.

---

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API routes (upload, sales, forecasts)
│   ├── core/                # Database, config, utils
│   ├── models/              # SQLAlchemy models (prediction.py)
│   └── services/            # Business logic
│       ├── data_processor.py        # CSV cleaning, daily series
│       ├── processing_pipeline.py   # Orchestrates upload → sales_data
│       ├── simple_feature_engineer.py  # Generates 10 features
│       └── heuristic_forecaster.py     # 6 forecasting methods
├── migrations/
│   └── 001_create_core_tables.sql   # Database schema
├── uploads/                 # Uploaded CSV files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## API Endpoints

### Upload
- `POST /api/v1/upload/` - Upload CSV/Excel file
- `GET /api/v1/upload/` - List uploads

### Sales Data
- `POST /api/v1/sales/{upload_id}/process` - Process upload → sales_data
- `GET /api/v1/sales/{upload_id}` - Get processed data
- `GET /api/v1/sales/{upload_id}/stats` - Data statistics

### Forecasts
- `POST /api/v1/forecasts/{upload_id}/features/generate` - Create features
- `POST /api/v1/forecasts/generate` - Generate forecasts
  ```json
  {
    "upload_id": "uuid-here",
    "horizon_weeks": 4,
    "sku_ids": ["SKU001"],
    "method": "auto"
  }
  ```
- `GET /api/v1/forecasts/{upload_id}/accuracy` - Backtest results

---

## Database Migrations

### Create Tables (Fresh Setup)
```bash
psql -U postgres -d sku_db -f migrations/001_create_core_tables.sql
```

### Reset Database (Drop All Data)
```bash
psql -U postgres -d sku_db -c "
  DROP TABLE IF EXISTS features, sales_data, raw_uploads, predictions CASCADE;
"
# Then re-run migration
psql -U postgres -d sku_db -f migrations/001_create_core_tables.sql
```

---

## Environment Variables

Create `.env` file:

```env
# Application
DEBUG=true
TESTING=false

# Database
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/sku_db"

# CORS (JSON array format)
CORS_ORIGINS='["http://localhost:5173", "http://localhost:3000"]'

# Model (future ML use)
MODEL_PATH="models/model.pth"
```

---

## Development Tips

### Check Database
```bash
# List tables
psql -U postgres -d sku_db -c "\dt"

# Count records
psql -U postgres -d sku_db -c "SELECT COUNT(*) FROM sales_data;"

# View sample data
psql -U postgres -d sku_db -c "SELECT * FROM sales_data LIMIT 5;"

# Check source_type distribution
psql -U postgres -d sku_db -c "SELECT source_type, COUNT(*) FROM sales_data GROUP BY source_type;"
```

### Run Tests
```bash
source venv/bin/activate
pytest tests/
```

### Debug Mode
Set `DEBUG=true` in `.env` to see SQL queries in logs.

---

## Common Issues

### "Upload not found"
- Upload must exist in `raw_uploads` table
- Check upload_id is correct

### "No data found for SKU"
- Must run feature generation first: `POST /forecasts/{upload_id}/features/generate`
- Or call `POST /forecasts/generate` with `"method": "auto"` (auto-generates features)

### Database connection errors
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Verify database `sku_db` exists

---

## Future Enhancements

- [ ] ML models (Prophet, LSTM)
- [ ] Model training pipeline
- [ ] Authentication (JWT)
- [ ] Background job processing (Celery)
- [ ] Model performance monitoring

---

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + asyncpg
- **ORM**: SQLAlchemy (async)
- **Data**: Pandas, NumPy
- **ML**: PyTorch (future)

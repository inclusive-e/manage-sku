# Manage SKU

AI-powered SKU (Stock Keeping Unit) management system with sales forecasting capabilities.

## Overview

This system allows users to upload sales data (CSV, Excel), process it, and generate forecasts for future sales trends, revenue, and inventory management.

## Project Structure

```
manage-sku/
├── backend/              # FastAPI + PyTorch backend
│   ├── app/
│   │   ├── api/v1/endpoints/    # API routes
│   │   ├── core/                # Database & config
│   │   ├── models/              # SQLAlchemy & Pydantic models
│   │   └── services/            # Business logic
│   ├── requirements.txt
│   └── README.md
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── components/          # Sidebar, FileUpload, etc.
│   │   └── pages/               # Dashboard, Upload, etc.
│   └── package.json
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.14+
- Node.js 20+
- PostgreSQL

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## API Documentation

Once backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Implementation Roadmap

### Phase 1: Data Upload & Storage ✅ **COMPLETED**
**Goal**: Enable users to upload sales data files

**Features**:
- [x] File upload endpoint (CSV, XLSX, XLS, TXT)
- [x] File validation (type, size, magic numbers)
- [x] Schema auto-detection (dates, numeric, categorical)
- [x] Data validation (missing values, outliers, date ranges)
- [x] Upload metadata storage in PostgreSQL
- [x] Frontend drag-and-drop upload component
- [x] Preview and validation report display

**Key Components**:
- `backend/app/services/data_upload.py` - File handling
- `backend/app/services/schema_detector.py` - Auto schema detection
- `backend/app/services/data_validator.py` - Data quality checks
- `backend/app/api/v1/endpoints/upload.py` - Upload API
- `frontend/src/components/FileUpload.tsx` - Upload UI

---

### Phase 2: Data Processing Pipeline 🔄 **IN PROGRESS**
**Goal**: Clean and prepare data for analysis

**Features**:
- [x] Column name cleaning and standardization
- [x] Type inference (numeric, datetime, categorical)
- [x] Missing value handling with appropriate defaults
- [ ] Data cleaning (remove/fix anomalies)
- [ ] Duplicate detection and handling
- [ ] Outlier detection and flagging
- [ ] Data transformation (currencies, units)
- [ ] Save cleaned data to `sales_data` table

**Key Components**:
- `backend/app/services/data_processor.py` - Data transformations
- `backend/app/services/data_validator.py` - Anomaly detection
- Database models: `RawUpload`, `SalesData`

---

### Phase 3: Feature Engineering 📊 **PENDING**
**Goal**: Create features for ML models

**Features**:
- [ ] Time-based features (day of week, month, quarter, holidays)
- [ ] Lag features (sales 7d ago, 30d ago, etc.)
- [ ] Rolling statistics (7d avg, 30d avg, trends)
- [ ] SKU-level features (category encoding, price stats)
- [ ] External features (seasonality, promotions)
- [ ] Feature storage and versioning

**Key Components**:
- `backend/app/services/feature_engineering.py`
- Feature store (database or file-based)

---

### Phase 4: Model Training & Management 🤖 **PENDING**
**Goal**: Build and manage forecasting models

**Features**:
- [ ] Prophet model integration (baseline)
- [ ] LSTM model with PyTorch
- [ ] Model training pipeline
- [ ] Cross-validation and hyperparameter tuning
- [ ] Model versioning and artifact storage
- [ ] Training job scheduling

**Key Components**:
- `backend/app/services/predictor.py` - Model wrapper
- `backend/app/models/` - Model implementations
- Model registry (MLflow or custom)

---

### Phase 5: Prediction API 🔮 **PENDING**
**Goal**: Serve predictions via API

**Features**:
- [ ] Forecast endpoint (single SKU, bulk)
- [ ] Confidence intervals
- [ ] Multiple model support (Prophet, LSTM)
- [ ] Model selection logic
- [ ] Prediction caching
- [ ] Historical prediction storage

**API Endpoints**:
- `POST /api/v1/predictions/forecast` - Generate forecasts
- `GET /api/v1/predictions/history` - Past predictions
- `GET /api/v1/metrics/{sku_id}` - Performance metrics

---

### Phase 6: Dashboard & Visualization 📈 **PENDING**
**Goal**: Display insights and forecasts

**Features**:
- [ ] Sales trend charts
- [ ] Forecast visualization with confidence bands
- [ ] SKU performance metrics
- [ ] Inventory alerts and recommendations
- [ ] Data quality dashboard
- [ ] Export forecasts (CSV, PDF)

**Key Components**:
- Charts: Recharts or Chart.js
- Dashboard components in `frontend/src/pages/`

---

### Phase 7: Advanced Features 🚀 **PENDING**
**Goal**: Production-ready features

**Features**:
- [ ] Authentication & authorization (JWT)
- [ ] User management and roles
- [ ] API rate limiting
- [ ] Background job processing (Celery)
- [ ] Email notifications for alerts
- [ ] Data export/import (more formats)
- [ ] A/B testing for models
- [ ] Model performance monitoring

---

## Sample Data

A sample sales data file with anomalies is provided at:
`backend/sample_sales_data.csv` (505 rows)

**Anomalies included for testing**:
- 20 future dates
- 20 negative quantities (returns)
- 15 extreme outliers (500-1000 qty)
- 15 zero quantities
- 10 missing stock levels
- 5 duplicate rows

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sku_db
DEBUG=true
CORS_ORIGINS=http://localhost:5173
MODEL_PATH=models/model.pth
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## Tech Stack

**Backend**:
- FastAPI (async web framework)
- SQLAlchemy + asyncpg (async ORM)
- PyTorch (ML models)
- Pandas (data processing)
- PostgreSQL (database)

**Frontend**:
- React + TypeScript
- React Router (navigation)
- Tailwind CSS (styling)
- Lucide React (icons)
- Recharts (visualization)

**DevOps**:
- Git (version control)
- Virtual environments (Python)
- npm (Node.js packages)

## License

MIT

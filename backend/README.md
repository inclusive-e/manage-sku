# SKU Prediction API

FastAPI backend for SKU prediction using PyTorch models.

## Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Set up PostgreSQL (using Docker):
```bash
docker run -d \
  --name sku-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=sku_db \
  -p 5432:5432 \
  postgres:15-alpine
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API route handlers
│   ├── core/                # Config, database
│   ├── models/              # Database models & schemas
│   └── services/            # Business logic
├── models/                  # Saved PyTorch models
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://postgres:postgres@localhost:5432/sku_db |
| `DEBUG` | Enable debug mode | true |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:5173 |
| `MODEL_PATH` | Path to PyTorch model | models/model.pth |

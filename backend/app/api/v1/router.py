from fastapi import APIRouter

from app.api.v1.endpoints import predictions, upload, sales

api_router = APIRouter()

api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])

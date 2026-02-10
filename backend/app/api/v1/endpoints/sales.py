"""
Sales Data API Endpoints
CRUD operations for processed sales data
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.prediction import SalesData

router = APIRouter()


@router.get("/sales")
async def list_sales(
    upload_id: Optional[str] = Query(None, description="Filter by upload ID"),
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List sales data with optional filtering

    Query params:
    - upload_id: Filter by specific upload
    - sku_id: Filter by specific SKU
    - skip: Pagination offset
    - limit: Number of results (max 1000)
    """
    async with AsyncSessionLocal() as session:
        # Build query
        query = select(SalesData)

        if upload_id:
            query = query.where(SalesData.upload_id == upload_id)
        if sku_id:
            query = query.where(SalesData.sku_id == sku_id)

        # Get total count
        count_query = select(func.count()).select_from(SalesData)
        if upload_id:
            count_query = count_query.where(SalesData.upload_id == upload_id)
        if sku_id:
            count_query = count_query.where(SalesData.sku_id == sku_id)

        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(SalesData.date.desc()).offset(skip).limit(limit)
        result = await session.execute(query)
        sales = result.scalars().all()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "sales": [
                {
                    "id": s.id,
                    "upload_id": s.upload_id,
                    "date": s.date.isoformat() if s.date else None,
                    "sku_id": s.sku_id,
                    "sales_quantity": s.sales_quantity,
                    "sales_revenue": s.sales_revenue,
                    "stock_level": s.stock_level,
                    "category": s.category,
                    "unit_price": s.unit_price,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in sales
            ],
        }


@router.get("/sales/{sale_id}")
async def get_sale(sale_id: int):
    """Get a single sales record by ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SalesData).where(SalesData.id == sale_id))
        sale = result.scalar_one_or_none()

        if not sale:
            raise HTTPException(status_code=404, detail="Sale record not found")

        return {
            "id": sale.id,
            "upload_id": sale.upload_id,
            "date": sale.date.isoformat() if sale.date else None,
            "sku_id": sale.sku_id,
            "sales_quantity": sale.sales_quantity,
            "sales_revenue": sale.sales_revenue,
            "stock_level": sale.stock_level,
            "category": sale.category,
            "unit_price": sale.unit_price,
            "created_at": sale.created_at.isoformat() if sale.created_at else None,
        }


@router.get("/uploads/{upload_id}/sales")
async def get_sales_by_upload(
    upload_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get all sales data for a specific upload

    This is useful for viewing processed data from a specific file upload.
    """
    async with AsyncSessionLocal() as session:
        # Get total count for this upload
        count_result = await session.execute(
            select(func.count())
            .select_from(SalesData)
            .where(SalesData.upload_id == upload_id)
        )
        total = count_result.scalar()

        # Get sales data
        result = await session.execute(
            select(SalesData)
            .where(SalesData.upload_id == upload_id)
            .order_by(SalesData.date.desc())
            .offset(skip)
            .limit(limit)
        )
        sales = result.scalars().all()

        return {
            "upload_id": upload_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "sales": [
                {
                    "id": s.id,
                    "date": s.date.isoformat() if s.date else None,
                    "sku_id": s.sku_id,
                    "sales_quantity": s.sales_quantity,
                    "sales_revenue": s.sales_revenue,
                    "stock_level": s.stock_level,
                    "category": s.category,
                    "unit_price": s.unit_price,
                }
                for s in sales
            ],
        }


@router.get("/uploads/{upload_id}/sales/summary")
async def get_sales_summary(upload_id: str):
    """
    Get summary statistics for sales data of a specific upload

    Returns aggregated metrics like total revenue, total quantity, etc.
    """
    async with AsyncSessionLocal() as session:
        # Check if upload has sales data
        result = await session.execute(
            select(func.count())
            .select_from(SalesData)
            .where(SalesData.upload_id == upload_id)
        )
        total_records = result.scalar()

        if total_records == 0:
            return {
                "upload_id": upload_id,
                "total_records": 0,
                "message": "No sales data found for this upload",
            }

        # Get summary stats
        result = await session.execute(
            select(
                func.count().label("total_records"),
                func.sum(SalesData.sales_quantity).label("total_quantity"),
                func.sum(SalesData.sales_revenue).label("total_revenue"),
                func.avg(SalesData.sales_quantity).label("avg_quantity"),
                func.avg(SalesData.sales_revenue).label("avg_revenue"),
                func.count(func.distinct(SalesData.sku_id)).label("unique_skus"),
            ).where(SalesData.upload_id == upload_id)
        )
        stats = result.one()

        # Get date range
        date_result = await session.execute(
            select(
                func.min(SalesData.date).label("min_date"),
                func.max(SalesData.date).label("max_date"),
            ).where(SalesData.upload_id == upload_id)
        )
        date_range = date_result.one()

        return {
            "upload_id": upload_id,
            "total_records": total_records,
            "summary": {
                "total_quantity": float(stats.total_quantity or 0),
                "total_revenue": float(stats.total_revenue or 0),
                "average_quantity": float(stats.avg_quantity or 0),
                "average_revenue": float(stats.avg_revenue or 0),
                "unique_skus": stats.unique_skus,
            },
            "date_range": {
                "start": date_range.min_date.isoformat()
                if date_range.min_date
                else None,
                "end": date_range.max_date.isoformat() if date_range.max_date else None,
            },
        }

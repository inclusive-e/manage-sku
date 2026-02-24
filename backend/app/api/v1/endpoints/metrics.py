"""
Metrics API Endpoints

Business metrics and analytics
"""

from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.sql import and_

from app.core.database import AsyncSessionLocal
from app.models.prediction import SalesData

router = APIRouter()


@router.get("/{upload_id}/sales")
async def get_sales_performance(
    upload_id: str,
    days: Annotated[
        int,
        Query(
            description="Number of days to analyze (7, 14, 30, or 60)",
            ge=7,
            le=60,
        ),
    ] = 7,
):
    """
    Get sales performance metrics for a specific upload

    Returns:
    - Total sales (units and revenue) for the selected period
    - Daily sales breakdown per SKU
    - Trend indicator comparing current vs previous period
    """
    async with AsyncSessionLocal() as session:
        # Get max date for this upload
        max_date_result = await session.execute(
            select(func.max(SalesData.date)).where(SalesData.upload_id == upload_id)
        )
        max_date = max_date_result.scalar()

        if not max_date:
            return {
                "upload_id": upload_id,
                "period_days": days,
                "date_range": {"start": None, "end": None},
                "total_sales": {"units": 0, "revenue": 0.0},
                "daily_sales": [],
                "trend": {
                    "percentage": 0.0,
                    "direction": "neutral",
                    "current_period_revenue": 0.0,
                    "previous_period_revenue": 0.0,
                },
            }

        # Ensure max_date is a datetime object (not date)
        if isinstance(max_date, str):
            max_date = datetime.fromisoformat(max_date)
        elif not isinstance(max_date, datetime):
            max_date = datetime.combine(max_date, datetime.min.time())

        # Calculate date ranges
        # Current period: [max_date - days + 1, max_date]
        # Previous period: [max_date - 2*days + 1, max_date - days]
        current_end = max_date
        current_start = max_date - timedelta(days=days - 1)
        previous_end = max_date - timedelta(days=days)
        previous_start = max_date - timedelta(days=2 * days - 1)

        # Query total sales for current period
        current_sales_result = await session.execute(
            select(
                func.coalesce(func.sum(SalesData.sales_quantity), 0).label(
                    "total_units"
                ),
                func.coalesce(func.sum(SalesData.sales_revenue), 0.0).label(
                    "total_revenue"
                ),
            ).where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date >= current_start,
                    SalesData.date <= current_end,
                )
            )
        )
        current_sales = current_sales_result.one()

        # Query total sales for previous period (for trend calculation)
        previous_sales_result = await session.execute(
            select(
                func.coalesce(func.sum(SalesData.sales_revenue), 0.0).label(
                    "total_revenue"
                ),
            ).where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date >= previous_start,
                    SalesData.date <= previous_end,
                )
            )
        )
        previous_revenue = previous_sales_result.scalar() or 0.0

        # Query daily sales per SKU for current period
        daily_sales_result = await session.execute(
            select(
                func.date(SalesData.date).label("sale_date"),
                SalesData.sku_id,
                func.sum(SalesData.sales_quantity).label("total_units"),
                func.sum(SalesData.sales_revenue).label("total_revenue"),
            )
            .where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date >= current_start,
                    SalesData.date <= current_end,
                )
            )
            .group_by(
                func.date(SalesData.date),
                SalesData.sku_id,
            )
            .order_by(
                func.date(SalesData.date),
                SalesData.sku_id,
            )
        )
        daily_sales_records = daily_sales_result.all()

        # Format daily sales response
        daily_sales = [
            {
                "date": str(record.sale_date),
                "sku_id": record.sku_id,
                "total_units": float(record.total_units) if record.total_units else 0.0,
                "total_revenue": float(record.total_revenue)
                if record.total_revenue
                else 0.0,
            }
            for record in daily_sales_records
        ]

        # Calculate trend percentage
        current_revenue = (
            float(current_sales.total_revenue) if current_sales.total_revenue else 0.0
        )

        if previous_revenue > 0:
            trend_percentage = (
                (current_revenue - previous_revenue) / previous_revenue
            ) * 100
        elif current_revenue > 0:
            trend_percentage = (
                100.0  # If no previous revenue but current exists, it's a 100% increase
            )
        else:
            trend_percentage = 0.0  # No data in either period

        # Determine trend direction
        if trend_percentage > 0:
            trend_direction = "up"
        elif trend_percentage < 0:
            trend_direction = "down"
        else:
            trend_direction = "neutral"

        return {
            "period_days": days,
            "date_range": {
                "start": current_start.strftime("%Y-%m-%d"),
                "end": current_end.strftime("%Y-%m-%d"),
            },
            "total_sales": {
                "units": float(current_sales.total_units)
                if current_sales.total_units
                else 0.0,
                "revenue": current_revenue,
            },
            "daily_sales": daily_sales,
            "trend": {
                "percentage": round(trend_percentage, 2),
                "direction": trend_direction,
                "current_period_revenue": current_revenue,
                "previous_period_revenue": float(previous_revenue),
            },
        }


@router.get("/{upload_id}/product")
async def get_product_performance(
    upload_id: str,
    days: Annotated[
        int,
        Query(
            description="Number of days to analyze (7, 14, 30, or 60)",
            ge=7,
            le=60,
        ),
    ] = 30,
):
    """
    Get product-level performance metrics for a specific upload

    Returns per-product analytics including:
    - Best sellers (top 5 SKUs by revenue)
    - Slow movers (SKUs with sell-through rate < 20%)
    - Dead stock (SKUs with no sales in 60+ days)
    """
    async with AsyncSessionLocal() as session:
        # Get max date for this upload
        max_date_result = await session.execute(
            select(func.max(SalesData.date)).where(SalesData.upload_id == upload_id)
        )
        max_date = max_date_result.scalar()

        if not max_date:
            return {
                "upload_id": upload_id,
                "period_days": days,
                "date_range": {"start": None, "end": None},
                "best_sellers": [],
                "slow_movers": [],
                "dead_stock": [],
            }

        # Ensure max_date is a datetime object
        if isinstance(max_date, str):
            max_date = datetime.fromisoformat(max_date)
        elif not isinstance(max_date, datetime):
            max_date = datetime.combine(max_date, datetime.min.time())

        # Calculate date range
        period_end = max_date
        period_start = max_date - timedelta(days=days - 1)

        # --- Best Sellers: Top 5 SKUs by total revenue ---
        best_sellers_result = await session.execute(
            select(
                SalesData.sku_id,
                func.coalesce(func.sum(SalesData.sales_quantity), 0).label(
                    "total_units"
                ),
                func.coalesce(func.sum(SalesData.sales_revenue), 0.0).label(
                    "total_revenue"
                ),
            )
            .where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date >= period_start,
                    SalesData.date <= period_end,
                )
            )
            .group_by(SalesData.sku_id)
            .order_by(func.sum(SalesData.sales_revenue).desc())
            .limit(5)
        )
        best_sellers_records = best_sellers_result.all()

        best_sellers = []
        for record in best_sellers_records:
            total_units = float(record.total_units) if record.total_units else 0.0
            total_revenue = float(record.total_revenue) if record.total_revenue else 0.0
            avg_price = total_revenue / total_units if total_units > 0 else 0.0
            best_sellers.append(
                {
                    "sku_id": record.sku_id,
                    "total_units": total_units,
                    "total_revenue": round(total_revenue, 2),
                    "avg_price": round(avg_price, 2),
                }
            )

        # --- Slow Movers: SKUs with sell-through rate < 20% ---
        # Get units sold per SKU in the period
        units_sold_result = await session.execute(
            select(
                SalesData.sku_id,
                func.coalesce(func.sum(SalesData.sales_quantity), 0).label(
                    "units_sold"
                ),
            )
            .where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date >= period_start,
                    SalesData.date <= period_end,
                )
            )
            .group_by(SalesData.sku_id)
        )
        units_sold_map = {
            r.sku_id: float(r.units_sold) for r in units_sold_result.all()
        }

        # Get latest stock level for each SKU
        latest_stock_result = await session.execute(
            select(
                SalesData.sku_id,
                SalesData.stock_level,
            )
            .where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date <= period_end,
                )
            )
            .distinct(SalesData.sku_id)
            .order_by(SalesData.sku_id, SalesData.date.desc())
        )
        # Get unique SKUs with their latest stock levels
        latest_stock_subquery = (
            select(
                SalesData.sku_id,
                func.max(SalesData.date).label("latest_date"),
            )
            .where(
                and_(
                    SalesData.upload_id == upload_id,
                    SalesData.date <= period_end,
                )
            )
            .group_by(SalesData.sku_id)
            .subquery()
        )
        stock_result = await session.execute(
            select(
                SalesData.sku_id,
                SalesData.stock_level,
            ).join(
                latest_stock_subquery,
                and_(
                    SalesData.sku_id == latest_stock_subquery.c.sku_id,
                    SalesData.date == latest_stock_subquery.c.latest_date,
                    SalesData.upload_id == upload_id,
                ),
            )
        )
        stock_map = {
            r.sku_id: r.stock_level
            for r in stock_result.all()
            if r.stock_level is not None
        }

        # Calculate sell-through rate and filter slow movers
        slow_movers = []
        for sku_id, units_sold in units_sold_map.items():
            current_stock = stock_map.get(sku_id, 0)
            if current_stock is None or current_stock == 0:
                continue
            total_inventory = units_sold + current_stock
            if total_inventory > 0:
                sell_through_rate = (units_sold / total_inventory) * 100
                if sell_through_rate < 20:
                    slow_movers.append(
                        {
                            "sku_id": sku_id,
                            "units_sold": units_sold,
                            "stock_level": current_stock,
                            "sell_through_rate": round(sell_through_rate, 1),
                        }
                    )

        # Sort by sell-through rate ascending
        slow_movers.sort(key=lambda x: x["sell_through_rate"])

        # --- Dead Stock: SKUs with no sales in last 60 days ---
        dead_stock_cutoff = max_date - timedelta(days=60)

        # Get all unique SKUs in this upload
        all_skus_result = await session.execute(
            select(SalesData.sku_id).where(SalesData.upload_id == upload_id).distinct()
        )
        all_skus = [r.sku_id for r in all_skus_result.all()]

        dead_stock = []
        for sku_id in all_skus:
            # Find last sale date (where sales_quantity > 0)
            last_sale_result = await session.execute(
                select(func.max(SalesData.date)).where(
                    and_(
                        SalesData.upload_id == upload_id,
                        SalesData.sku_id == sku_id,
                        SalesData.sales_quantity > 0,
                    )
                )
            )
            last_sale_date = last_sale_result.scalar()

            if last_sale_date:
                # Ensure last_sale_date is datetime
                if isinstance(last_sale_date, str):
                    last_sale_date = datetime.fromisoformat(last_sale_date)
                elif not isinstance(last_sale_date, datetime):
                    last_sale_date = datetime.combine(
                        last_sale_date, datetime.min.time()
                    )

                if last_sale_date < dead_stock_cutoff:
                    # Get current stock level
                    current_stock = stock_map.get(sku_id, 0)
                    if current_stock is None:
                        current_stock = 0

                    days_since_sale = (max_date - last_sale_date).days
                    dead_stock.append(
                        {
                            "sku_id": sku_id,
                            "last_sale_date": last_sale_date.strftime("%Y-%m-%d"),
                            "days_since_sale": days_since_sale,
                            "current_stock": current_stock,
                        }
                    )

        # Sort dead stock by days since sale descending
        dead_stock.sort(key=lambda x: x["days_since_sale"], reverse=True)

        return {
            "upload_id": upload_id,
            "period_days": days,
            "date_range": {
                "start": period_start.strftime("%Y-%m-%d"),
                "end": period_end.strftime("%Y-%m-%d"),
            },
            "best_sellers": best_sellers,
            "slow_movers": slow_movers,
            "dead_stock": dead_stock,
        }


@router.get("/{upload_id}/inventory")
async def get_inventory_performance(upload_id: str):
    """
    Get inventory performance metrics for a specific upload

    Returns inventory analytics including:
    - Stock levels overview
    - Inventory turnover
    - Low stock alerts
    - Stock coverage days
    """
    async with AsyncSessionLocal() as session:
        return {
            "upload_id": upload_id,
            "endpoint": "/performance/{upload_id}/inventory",
            "status": "defined",
            "message": "Inventory performance metrics endpoint - implementation pending",
        }

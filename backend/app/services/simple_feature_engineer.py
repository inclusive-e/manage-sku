"""MVP Feature Engineering Service

Simple, fast feature generation with only 10 core features.
Focus: Get E2E flow working, not comprehensive feature engineering.
"""

from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Feature, SalesData


class SimpleFeatureEngineer:
    """
    MVP Feature Engineer - 10 core features only

    Features:
    - date, sku_id, sales_quantity (core)
    - lag_7d, lag_28d (lags)
    - rolling_mean_7d, rolling_mean_28d (trends)
    - day_of_week, week_of_year (calendar)
    - unit_price (price)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {"records_created": 0, "skus_processed": 0}

    async def engineer_features(self, upload_id: str) -> Dict[str, Any]:
        """
        Generate 10 core features for an upload

        Args:
            upload_id: Upload UUID to process

        Returns:
            Stats about feature generation
        """
        # Load sales data
        df = await self._load_sales_data(upload_id)

        if len(df) == 0:
            return {"error": "No sales data found", "upload_id": upload_id}

        self.stats["skus_processed"] = df["sku_id"].nunique()

        # Add 10 features
        df = self._add_calendar_features(df)
        df = self._add_lag_features(df)
        df = self._add_rolling_features(df)

        # Save to database
        await self._save_features(df, upload_id)

        return {
            "upload_id": upload_id,
            "records_created": self.stats["records_created"],
            "skus_processed": self.stats["skus_processed"],
            "date_range": {
                "start": df["date"].min().isoformat(),
                "end": df["date"].max().isoformat(),
            },
        }

    def _add_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add day_of_week and week_of_year"""
        df = df.copy()
        df["day_of_week"] = df["date"].dt.dayofweek
        df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lag_7d and lag_28d"""
        df = df.sort_values(["sku_id", "date"])

        # Lag 7 days (1 week)
        df["lag_7d"] = df.groupby("sku_id")["sales_quantity"].shift(7)

        # Lag 28 days (4 weeks)
        df["lag_28d"] = df.groupby("sku_id")["sales_quantity"].shift(28)

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling_mean_7d and rolling_mean_28d"""
        # 7-day rolling mean (excluding current day to avoid leakage)
        df["rolling_mean_7d"] = df.groupby("sku_id")["sales_quantity"].transform(
            lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
        )

        # 28-day rolling mean
        df["rolling_mean_28d"] = df.groupby("sku_id")["sales_quantity"].transform(
            lambda x: x.shift(1).rolling(window=28, min_periods=1).mean()
        )

        return df

    async def _load_sales_data(self, upload_id: str) -> pd.DataFrame:
        """Load sales data from database"""
        result = await self.session.execute(
            select(SalesData).where(SalesData.upload_id == upload_id)
        )
        records = result.scalars().all()

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(
            [
                {
                    "id": r.id,
                    "upload_id": r.upload_id,
                    "date": pd.to_datetime(r.date),
                    "sku_id": r.sku_id,
                    "sales_quantity": float(r.sales_quantity)
                    if r.sales_quantity
                    else 0.0,
                    "unit_price": float(r.unit_price) if r.unit_price else None,
                }
                for r in records
            ]
        )

        return df

    async def _save_features(self, df: pd.DataFrame, upload_id: str):
        """Save features to database in batches"""
        records = []

        for _, row in df.iterrows():
            if pd.isna(row.get("sku_id")) or pd.isna(row.get("date")):
                continue

            def safe_float(val):
                if pd.isna(val):
                    return None
                return float(val)

            def safe_int(val):
                if pd.isna(val):
                    return None
                return int(val)

            record = Feature(
                upload_id=upload_id,
                sku_id=str(row["sku_id"]),
                date=row["date"].to_pydatetime()
                if isinstance(row["date"], pd.Timestamp)
                else row["date"],
                sales_quantity=safe_float(row.get("sales_quantity", 0)) or 0.0,
                unit_price=safe_float(row.get("unit_price")),
                lag_7d=safe_float(row.get("lag_7d")),
                lag_28d=safe_float(row.get("lag_28d")),
                rolling_mean_7d=safe_float(row.get("rolling_mean_7d")),
                rolling_mean_28d=safe_float(row.get("rolling_mean_28d")),
                day_of_week=safe_int(row.get("day_of_week")),
                week_of_year=safe_int(row.get("week_of_year")),
            )
            records.append(record)

        # Bulk insert in batches
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            self.session.add_all(batch)
            await self.session.commit()

        self.stats["records_created"] = len(records)

    async def get_features_for_sku(self, upload_id: str, sku_id: str) -> pd.DataFrame:
        """Get features for a specific SKU"""
        result = await self.session.execute(
            select(Feature)
            .where(Feature.upload_id == upload_id)
            .where(Feature.sku_id == sku_id)
            .order_by(Feature.date)
        )
        records = result.scalars().all()

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame([r.to_dict() for r in records])
        return df

    async def get_all_skus(self, upload_id: str) -> List[str]:
        """Get list of all SKUs for an upload"""
        from sqlalchemy import distinct

        result = await self.session.execute(
            select(distinct(Feature.sku_id)).where(Feature.upload_id == upload_id)
        )
        return [row[0] for row in result.all()]

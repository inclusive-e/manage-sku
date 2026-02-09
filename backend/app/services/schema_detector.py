"""
Schema Detection Service
Automatically detects column types and suggests schema mappings
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class ColumnType(str, Enum):
    """Supported column types"""

    DATE = "date"
    DATETIME = "datetime"
    NUMERIC = "numeric"
    INTEGER = "integer"
    STRING = "string"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class SchemaDetector:
    """Detects schema from uploaded data files"""

    # Keywords to identify common columns
    COLUMN_KEYWORDS = {
        "date": ["date", "day", "time", "timestamp", "datetime", "dt", "period"],
        "sku": ["sku", "product_id", "item_id", "product_code", "item_code", "id"],
        "quantity": ["quantity", "qty", "amount", "count", "units", "volume"],
        "revenue": [
            "revenue",
            "sales",
            "price",
            "total",
            "amount",
            "value",
            "turnover",
        ],
        "stock": ["stock", "inventory", "on_hand", "available", "balance"],
        "category": ["category", "type", "group", "department", "class", "segment"],
    }

    @staticmethod
    def detect_column_type(series: pd.Series) -> ColumnType:
        """Detect the type of a pandas Series"""
        # Drop nulls for type detection
        non_null = series.dropna()

        if len(non_null) == 0:
            return ColumnType.UNKNOWN

        # Try datetime first
        try:
            pd.to_datetime(non_null, errors="raise")
            # Check if it's date only or datetime
            sample = pd.to_datetime(non_null.iloc[0])
            if sample.hour == 0 and sample.minute == 0 and sample.second == 0:
                return ColumnType.DATE
            return ColumnType.DATETIME
        except:
            pass

        # Try numeric
        try:
            numeric_series = pd.to_numeric(non_null, errors="coerce")
            if numeric_series.notna().all():
                # Check if integer
                if (numeric_series == numeric_series.astype(int)).all():
                    return ColumnType.INTEGER
                return ColumnType.NUMERIC
        except:
            pass

        # Try boolean
        if non_null.isin(
            [
                True,
                False,
                0,
                1,
                "True",
                "False",
                "true",
                "false",
                "YES",
                "NO",
                "yes",
                "no",
            ]
        ).all():
            return ColumnType.BOOLEAN

        # Check if categorical (low cardinality)
        unique_ratio = non_null.nunique() / len(non_null)
        if unique_ratio < 0.1 and non_null.nunique() < 50:
            return ColumnType.CATEGORICAL

        return ColumnType.STRING

    @staticmethod
    def suggest_column_mapping(column_name: str) -> Optional[str]:
        """Suggest what a column might be based on its name"""
        col_lower = column_name.lower().replace(" ", "_").replace("-", "_")

        for field, keywords in SchemaDetector.COLUMN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in col_lower:
                    return field

        return None

    @staticmethod
    def detect_schema(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect complete schema from DataFrame

        Returns:
            {
                'columns': [
                    {
                        'name': 'column_name',
                        'detected_type': 'numeric',
                        'suggested_mapping': 'revenue',
                        'null_count': 5,
                        'unique_count': 100,
                        'sample_values': [1, 2, 3]
                    }
                ],
                'row_count': 1000,
                'suggested_date_column': 'date',
                'suggested_sku_column': 'sku_id'
            }
        """
        columns = []
        suggested_date = None
        suggested_sku = None

        for col in df.columns:
            series = df[col]
            col_type = SchemaDetector.detect_column_type(series)
            suggested = SchemaDetector.suggest_column_mapping(col)

            # Get sample values (non-null)
            sample_values = series.dropna().head(5).tolist()
            # Convert to string for JSON serialization
            sample_values = [str(v) for v in sample_values]

            column_info = {
                "name": col,
                "detected_type": col_type.value,
                "suggested_mapping": suggested,
                "null_count": int(series.isna().sum()),
                "null_percentage": float(series.isna().sum() / len(series) * 100),
                "unique_count": int(series.nunique()),
                "sample_values": sample_values,
            }

            columns.append(column_info)

            # Track suggested key columns
            if (
                suggested == "date"
                and not suggested_date
                and col_type in [ColumnType.DATE, ColumnType.DATETIME]
            ):
                suggested_date = col
            if suggested == "sku" and not suggested_sku:
                suggested_sku = col

        return {
            "columns": columns,
            "row_count": len(df),
            "column_count": len(df.columns),
            "suggested_date_column": suggested_date,
            "suggested_sku_column": suggested_sku,
            "memory_usage_mb": float(df.memory_usage(deep=True).sum() / 1024 / 1024),
        }

    @staticmethod
    def generate_preview(df: pd.DataFrame, rows: int = 10) -> List[Dict]:
        """Generate preview data for frontend"""
        preview_df = df.head(rows).copy()

        # Convert to dict with NaN handling
        records = preview_df.to_dict("records")

        # Replace NaN, NaT, and Inf values with None
        cleaned_records = []
        for record in records:
            cleaned = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned[key] = None
                elif isinstance(value, float) and (np.isinf(value) or np.isnan(value)):
                    cleaned[key] = None
                elif isinstance(value, pd.Timestamp):
                    cleaned[key] = value.isoformat()
                else:
                    cleaned[key] = value
            cleaned_records.append(cleaned)

        return cleaned_records

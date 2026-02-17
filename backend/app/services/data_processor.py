"""
Data Processing Service
Reads and processes uploaded files
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.core.timezone_utils import get_utc_timestamp


class DataProcessor:
    """Process uploaded data files"""

    @staticmethod
    def read_file(file_path: Path) -> pd.DataFrame:
        """Read file based on extension"""
        ext = file_path.suffix.lower()

        if ext == ".csv":
            # Try different encodings
            encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
            for encoding in encodings:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV file with common encodings")

        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)

        elif ext == ".txt":
            # Try tab-delimited first, then comma
            try:
                return pd.read_csv(file_path, sep="\t")
            except:
                return pd.read_csv(file_path)

        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names"""
        df.columns = df.columns.str.strip()  # Remove whitespace
        df.columns = df.columns.str.lower()  # Lowercase
        df.columns = df.columns.str.replace(" ", "_")  # Spaces to underscores
        df.columns = df.columns.str.replace("-", "_")  # Hyphens to underscores
        df.columns = df.columns.str.replace(
            r"[^a-z0-9_]", "", regex=True
        )  # Remove special chars
        return df

    @staticmethod
    def infer_and_convert_types(df: pd.DataFrame) -> pd.DataFrame:
        """Infer and convert column types"""
        for col in df.columns:
            # Try numeric first
            try:
                numeric_data = pd.to_numeric(df[col], errors="coerce")
                if numeric_data.notna().sum() / len(df) > 0.8:  # 80% numeric
                    df[col] = numeric_data
                    continue
            except:
                pass

            # Try datetime with format inference
            try:
                date_data = pd.to_datetime(
                    df[col], errors="coerce", format="mixed", dayfirst=False
                )
                if date_data.notna().sum() / len(df) > 0.8:  # 80% dates
                    df[col] = date_data
                    continue
            except:
                pass

        return df

    @staticmethod
    def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill NaN values with appropriate defaults based on column type.

        This handles cases where pandas creates NaN values for missing columns
        or when data is explicitly missing.
        """
        for col in df.columns:
            if df[col].isna().any():
                # Check if column is numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(0.0)
                # Check if column is datetime
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    # For dates, use the most common date or today's date
                    mode_date = df[col].mode()
                    if len(mode_date) > 0:
                        df[col] = df[col].fillna(mode_date[0])
                    else:
                        df[col] = df[col].fillna(get_utc_timestamp().normalize())
                # Check if column is boolean
                elif pd.api.types.is_bool_dtype(df[col]):
                    df[col] = df[col].fillna(False)
                # Otherwise treat as string/object
                else:
                    df[col] = df[col].fillna("")

        return df

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning steps in sequence"""
        df = df.copy()
        df = DataProcessor.clean_column_names(df)
        df = DataProcessor.infer_and_convert_types(df)
        df = DataProcessor.fill_missing_values(df)
        return df

    @staticmethod
    def standardize_column_mapping(
        df: pd.DataFrame, mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """Rename columns based on mapping {'old_name': 'new_name'}"""
        return df.rename(columns=mapping)

    @staticmethod
    def prepare_for_database(
        df: pd.DataFrame, column_mapping: Dict[str, str] = None
    ) -> pd.DataFrame:
        """Ensure all required columns exist with defaults"""
        if column_mapping:
            df = DataProcessor.standardize_column_mapping(df, column_mapping)

        required_columns = {
            "date": get_utc_timestamp().normalize(),
            "sku_id": "UNKNOWN",
            "sales_quantity": 0.0,
            "unit_price": 0.0,
            "sales_revenue": 0.0,
            "stock_level": 0,
            "category": "",
        }

        for col, default in required_columns.items():
            if col not in df.columns:
                df[col] = default

        return df

    @staticmethod
    def create_complete_daily_series(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform sparse transaction data into complete daily time series.

        For each SKU, creates a row for every day in the date range.
        Missing days are filled with sales_quantity=0.
        Tracks source_type: 'user' = from CSV, 'system' = filled gaps

        Args:
            df: DataFrame with columns [date, sku_id, sales_quantity,
                                        unit_price, sales_revenue,
                                        stock_level, category]

        Returns:
            DataFrame with complete daily series (no date gaps per SKU)
        """
        if len(df) == 0:
            return df

        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])

        # Aggregate transactions to daily level per SKU
        # These are the actual data points from the user's CSV
        daily = df.groupby(['sku_id', df['date'].dt.date]).agg({
            'sales_quantity': 'sum',
            'unit_price': 'mean',
            'sales_revenue': 'sum',
            'stock_level': 'last',
            'category': 'first'
        }).reset_index()

        daily['date'] = pd.to_datetime(daily['date'])
        daily['source_type'] = 'user'  # Mark as user-provided data

        # Get all unique SKUs and date range
        skus = daily['sku_id'].unique()
        start_date = daily['date'].min()
        end_date = daily['date'].max()

        # Create complete date range
        complete_dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Build complete series for all SKUs
        complete_rows = []

        for sku in skus:
            sku_data = daily[daily['sku_id'] == sku].copy()
            sku_data = sku_data.set_index('date')

            # Reindex to complete date range
            sku_complete = sku_data.reindex(complete_dates)
            sku_complete.index.name = 'date'
            sku_complete = sku_complete.reset_index()

            # Fill missing values
            sku_complete['sku_id'] = sku

            # Track which rows were system-generated (filled gaps)
            sku_complete['source_type'] = sku_complete['source_type'].fillna('system')

            sku_complete['sales_quantity'] = sku_complete['sales_quantity'].fillna(0)
            sku_complete['sales_revenue'] = sku_complete['sales_revenue'].fillna(0)
            sku_complete['unit_price'] = sku_complete['unit_price'].fillna(
                sku_data['unit_price'].mean() if len(sku_data) > 0 else 0
            )
            sku_complete['stock_level'] = sku_complete['stock_level'].fillna(0)
            sku_complete['category'] = sku_complete['category'].fillna(
                sku_data['category'].iloc[0] if len(sku_data) > 0 else ''
            )

            complete_rows.append(sku_complete)

        # Combine all SKUs
        result = pd.concat(complete_rows, ignore_index=True)

        # Sort by sku_id and date
        result = result.sort_values(['sku_id', 'date']).reset_index(drop=True)

        return result

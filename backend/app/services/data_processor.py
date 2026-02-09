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

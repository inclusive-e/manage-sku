"""
Processing Pipeline
Orchestrates data cleaning and database insertion
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone_utils import get_utc_timestamp
from app.models.prediction import RawUpload, SalesData
from app.services.data_processor import DataProcessor


class ProcessingPipeline:
    """Process uploaded files and save to database"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {"rows_processed": 0, "rows_inserted": 0, "errors": []}

    async def process_upload(
        self, upload_id: str, column_mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process a raw upload and save to sales_data

        Args:
            upload_id: The UUID of the raw upload
            column_mapping: Optional mapping of column names {'old': 'new'}

        Returns:
            Processing statistics and status
        """
        # Get upload record
        upload = await self.session.get(RawUpload, upload_id)
        if not upload:
            raise ValueError(f"Upload {upload_id} not found")

        if upload.status == "processed":
            raise ValueError(f"Upload {upload_id} already processed")

        try:
            # Update status
            upload.status = "processing"
            await self.session.commit()

            # Load raw file
            file_path = Path(upload.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read data
            df = DataProcessor.read_file(file_path)
            self.stats["rows_processed"] = len(df)

            # Clean data
            df = DataProcessor.clean_dataframe(df)

            # Apply column mapping if provided
            if column_mapping:
                df = DataProcessor.standardize_column_mapping(df, column_mapping)

            # Prepare for database
            df = DataProcessor.prepare_for_database(df)

            # Insert into sales_data
            await self._insert_to_database(df, upload_id)

            # Update upload status
            upload.status = "processed"
            upload.processed_at = get_utc_timestamp()
            await self.session.commit()

            self.stats["success"] = True
            return self.stats

        except Exception as e:
            upload.status = "error"
            upload.error_message = str(e)
            await self.session.commit()
            self.stats["errors"].append(str(e))
            self.stats["success"] = False
            raise

    async def _insert_to_database(self, df: pd.DataFrame, upload_id: str):
        """Insert cleaned data into sales_data table"""
        records = []

        for _, row in df.iterrows():
            record = SalesData(
                upload_id=upload_id,
                date=row.get("date"),
                sku_id=row.get("sku_id"),
                sales_quantity=float(row.get("sales_quantity", 0)),
                unit_price=float(row.get("unit_price", 0)),
                sales_revenue=float(row.get("sales_revenue", 0)),
                stock_level=int(row.get("stock_level", 0))
                if pd.notna(row.get("stock_level"))
                else 0,
                category=str(row.get("category", "")),
            )
            records.append(record)

        # Bulk insert
        self.session.add_all(records)
        await self.session.commit()

        self.stats["rows_inserted"] = len(records)

    async def preview_cleaned_data(
        self, upload_id: str, column_mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Preview cleaned data without saving to database

        Returns:
            Preview rows and processing statistics
        """
        upload = await self.session.get(RawUpload, upload_id)
        if not upload:
            raise ValueError(f"Upload {upload_id} not found")

        file_path = Path(upload.file_path)
        df = DataProcessor.read_file(file_path)

        # Clean
        df = DataProcessor.clean_dataframe(df)

        if column_mapping:
            df = DataProcessor.standardize_column_mapping(df, column_mapping)

        df = DataProcessor.prepare_for_database(df)

        # Convert to dict for JSON response
        records = df.head(20).to_dict("records")

        # Handle NaN values for JSON
        clean_records = []
        for record in records:
            clean_record = {}
            for k, v in record.items():
                if pd.isna(v):
                    clean_record[k] = None
                elif isinstance(v, pd.Timestamp):
                    clean_record[k] = v.isoformat()
                else:
                    clean_record[k] = v
            clean_records.append(clean_record)

        return {
            "preview": clean_records,
            "total_rows": len(df),
            "columns": list(df.columns),
        }

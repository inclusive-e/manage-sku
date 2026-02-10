"""
Upload API Endpoints
"""

import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.prediction import RawUpload
from app.services.data_processor import DataProcessor
from app.services.data_upload import UploadService
from app.services.data_validator import DataValidator
from app.services.processing_pipeline import ProcessingPipeline
from app.services.schema_detector import SchemaDetector

router = APIRouter()


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = None,
):
    """
    Upload a data file (CSV, XLSX, XLS, TXT)

    Returns:
        {
            "upload_id": "uuid",
            "filename": "sales_data.csv",
            "status": "uploaded",
            "schema": {...},
            "validation": {...},
            "preview": [...]
        }
    """
    # Generate upload ID
    upload_id = str(uuid.uuid4())

    try:
        # 1. Save file
        file_path = await UploadService.save_upload_file(file, upload_id)

        # 2. Read file
        df = DataProcessor.read_file(file_path)

        # 3. Clean column names
        df = DataProcessor.clean_column_names(df)

        # 4. Infer and convert types
        df = DataProcessor.infer_and_convert_types(df)

        # 5. Fill missing values with appropriate defaults
        # NOTE: Commented out for now - will be used in Phase 2 processing pipeline
        # df = DataProcessor.fill_missing_values(df)

        # 6. Detect schema
        schema = SchemaDetector.detect_schema(df)

        # 5. Validate data
        validation = DataValidator.validate_data(df, schema)

        # 6. Generate preview
        preview = SchemaDetector.generate_preview(df, rows=10)

        # 7. Save to database (async)
        async with AsyncSessionLocal() as session:
            upload_record = RawUpload(
                id=upload_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size_bytes=file_path.stat().st_size,
                row_count=len(df),
                column_count=len(df.columns),
                detected_schema=schema,
                validation_report=validation,
                status="uploaded",
            )
            session.add(upload_record)
            await session.commit()

        return {
            "upload_id": upload_id,
            "filename": file.filename,
            "status": "uploaded",
            "row_count": len(df),
            "column_count": len(df.columns),
            "schema": schema,
            "validation": validation,
            "preview": preview,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        UploadService.delete_file(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/uploads/{upload_id}")
async def get_upload_status(upload_id: str):
    """Get upload status and details"""
    async with AsyncSessionLocal() as session:
        upload = await session.get(RawUpload, upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        return {
            "upload_id": upload.id,
            "filename": upload.filename,
            "status": upload.status,
            "row_count": upload.row_count,
            "schema": upload.detected_schema,
            "validation": upload.validation_report,
            "uploaded_at": upload.uploaded_at,
        }


@router.get("/uploads")
async def list_uploads(skip: int = 0, limit: int = 10):
    """List all uploads without schema details"""
    async with AsyncSessionLocal() as session:
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(RawUpload)
        )
        total = count_result.scalar()

        # Get uploads with pagination
        result = await session.execute(
            select(RawUpload)
            .order_by(RawUpload.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        uploads = result.scalars().all()

        # Format response without schema
        upload_list = []
        for upload in uploads:
            upload_list.append(
                {
                    "upload_id": upload.id,
                    "filename": upload.filename,
                    "status": upload.status,
                    "row_count": upload.row_count,
                    "column_count": upload.column_count,
                    "uploaded_at": upload.uploaded_at,
                    "processed_at": upload.processed_at,
                    "validation": upload.validation_report,
                }
            )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "uploads": upload_list,
        }


@router.post("/uploads/process")
async def process_upload(body: dict):
    """
    Process uploaded file and save to sales_data table

    Body: {"upload_id": "uuid"}
    """
    upload_id = body.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="upload_id is required")

    async with AsyncSessionLocal() as session:
        upload = await session.get(RawUpload, upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        pipeline = ProcessingPipeline(session)

        try:
            stats = await pipeline.process_upload(
                upload_id, column_mapping=upload.column_mapping
            )

            return {
                "upload_id": upload_id,
                "status": "processed",
                "rows_processed": stats["rows_processed"],
                "rows_inserted": stats["rows_inserted"],
                "message": "Data processed successfully",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/uploads/preview")
async def preview_processing(body: dict):
    """
    Preview how the data will look after processing

    Body: {"upload_id": "uuid"}
    """
    upload_id = body.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="upload_id is required")

    async with AsyncSessionLocal() as session:
        upload = await session.get(RawUpload, upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        pipeline = ProcessingPipeline(session)

        try:
            preview = await pipeline.preview_cleaned_data(
                upload_id, column_mapping=upload.column_mapping
            )
            return preview
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/uploads/{upload_id}/mapping")
async def set_column_mapping(upload_id: str, mapping: dict):
    """
    Set column mappings for processing

    mapping: {
        "date": "order_date",
        "sku_id": "product_code",
        "sales_quantity": "quantity",
        "sales_revenue": "total_amount"
    }
    """
    async with AsyncSessionLocal() as session:
        upload = await session.get(RawUpload, upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        upload.column_mapping = mapping
        await session.commit()

        return {
            "upload_id": upload_id,
            "mapping": mapping,
            "message": "Mapping saved successfully",
        }

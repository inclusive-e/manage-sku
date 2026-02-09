"""
Data Upload Service
Handles file uploads, storage, and processing
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import magic
from fastapi import UploadFile, HTTPException
from app.core.config import settings

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class UploadService:
    """Service for handling file uploads"""
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Check if file extension is allowed"""
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_type(file_path: Path) -> bool:
        """Validate actual file type using magic numbers"""
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(file_path))
        
        allowed_types = {
            'text/csv',
            'text/plain',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/octet-stream'  # Some CSVs are detected as this
        }
        
        return file_type in allowed_types or 'csv' in file_type.lower()
    
    @staticmethod
    async def save_upload_file(upload_file: UploadFile, upload_id: str) -> Path:
        """Save uploaded file to disk"""
        # Validate extension
        if not UploadService.validate_file_extension(upload_file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Create file path
        ext = Path(upload_file.filename).suffix
        file_path = UPLOAD_DIR / f"{upload_id}{ext}"
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            upload_file.file.close()
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            file_path.unlink()  # Delete file
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Validate file type
        if not UploadService.validate_file_type(file_path):
            file_path.unlink()  # Delete file
            raise HTTPException(
                status_code=400,
                detail="Invalid file content. File may be corrupted."
            )
        
        return file_path
    
    @staticmethod
    def delete_file(file_path: Path) -> None:
        """Delete uploaded file"""
        if file_path.exists():
            file_path.unlink()

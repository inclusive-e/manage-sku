from sqlalchemy import JSON, BigInteger, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class RawUpload(Base):
    """Stores metadata about uploaded files"""

    __tablename__ = "raw_uploads"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)

    # Schema and validation info
    detected_schema = Column(JSON, nullable=True)
    validation_report = Column(JSON, nullable=True)
    column_mapping = Column(JSON, nullable=True)  # User-confirmed mappings

    # Status tracking
    status = Column(
        String(50), default="uploaded"
    )  # uploaded, processing, processed, error
    error_message = Column(Text, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


class SalesData(Base):
    """Cleaned and processed sales data"""

    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False, index=True)

    # Core fields
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    sku_id = Column(String(100), nullable=False, index=True)
    sales_quantity = Column(Float, nullable=True)
    sales_revenue = Column(Float, nullable=True)
    stock_level = Column(Float, nullable=True)

    # Additional fields
    category = Column(String(100), nullable=True)
    unit_price = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Prediction(Base):
    """Database model for storing predictions"""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    input_data = Column(JSON, nullable=False)
    prediction_result = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    model_version = Column(String, default="latest")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    upload_id = Column(String(36), nullable=False, index=True)

    # Core fields
    date = Column(DateTime(timezone=False), nullable=False, index=True)
    sku_id = Column(String(100), nullable=False, index=True)
    sales_quantity = Column(Float, nullable=True)
    sales_revenue = Column(Float, nullable=True)
    stock_level = Column(Float, nullable=True)

    # Additional fields
    category = Column(String(100), nullable=True)
    unit_price = Column(Float, nullable=True)

    # Source tracking: 'user' = from CSV, 'system' = filled gaps by processor
    source_type = Column(String(20), nullable=False, default="user")

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


class Feature(Base):
    """MVP: Minimal feature store with 10 core features for heuristic forecasting"""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(36), nullable=False, index=True)
    sku_id = Column(String(100), nullable=False, index=True)
    date = Column(DateTime(timezone=False), nullable=False, index=True)

    # Core target
    sales_quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=True)

    # Lags (essential for heuristics)
    lag_7d = Column(Float, nullable=True)  # Last week
    lag_28d = Column(Float, nullable=True)  # Same week last month

    # Rolling averages (trends)
    rolling_mean_7d = Column(Float, nullable=True)  # Short-term trend
    rolling_mean_28d = Column(Float, nullable=True)  # Monthly average

    # Calendar features (seasonality)
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    week_of_year = Column(Integer, nullable=True)  # 1-53

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "upload_id": self.upload_id,
            "sku_id": self.sku_id,
            "date": self.date.isoformat() if self.date else None,
            "sales_quantity": self.sales_quantity,
            "unit_price": self.unit_price,
            "lag_7d": self.lag_7d,
            "lag_28d": self.lag_28d,
            "rolling_mean_7d": self.rolling_mean_7d,
            "rolling_mean_28d": self.rolling_mean_28d,
            "day_of_week": self.day_of_week,
            "week_of_year": self.week_of_year,
        }

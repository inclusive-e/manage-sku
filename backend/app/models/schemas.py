from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class PredictionRequest(BaseModel):
    """Request model for prediction endpoint"""
    data: dict = Field(..., description="Input data for prediction")
    model_version: Optional[str] = Field(default="latest", description="Model version to use")

class PredictionResponse(BaseModel):
    """Response model for prediction endpoint"""
    prediction: Any = Field(..., description="Prediction result")
    confidence: Optional[float] = Field(None, description="Confidence score")
    model_version: str = Field(..., description="Version of model used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    database_connected: bool

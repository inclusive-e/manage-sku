"""MVP Forecasting API Endpoints

Simple heuristic forecasting - no ML models needed.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.analysis_pipeline import AnalysisPipeline
from app.services.heuristic_forecaster import ForecastEvaluator, HeuristicForecaster
from app.services.simple_feature_engineer import SimpleFeatureEngineer

router = APIRouter()


class ForecastRequest(BaseModel):
    """Request body for generating forecasts"""

    upload_id: str
    horizon_weeks: int = 4
    sku_ids: Optional[List[str]] = None
    method: Optional[str] = "auto"  # auto, naive, rolling_mean_7d, etc.


class WeeklyForecast(BaseModel):
    """Single week forecast"""

    week: int
    forecast: float
    lower_bound: float
    upper_bound: float


class SKUForecast(BaseModel):
    """Forecast for a single SKU"""

    sku_id: str
    horizon_weeks: int
    method: str
    historical_avg: float
    historical_std: float
    weekly_forecasts: List[WeeklyForecast]
    analysis: Dict = {}
    backtest_results: Dict = {}
    reasoning: str = ""


class ForecastResponse(BaseModel):
    """Response from forecast generation"""

    upload_id: str
    generated_at: str
    sku_count: int
    forecasts: List[SKUForecast]


@router.post("/generate", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest):
    """
    Generate heuristic forecasts for uploaded data

    Simple, explainable forecasts using rule-based heuristics.
    No ML models required - works immediately.

    Example:
        POST /api/v1/forecasts/generate
        {
            "upload_id": "abc-123",
            "horizon_weeks": 4,
            "sku_ids": ["SKU0046"],
            "method": "auto"
        }
    """
    async with AsyncSessionLocal() as session:
        # Initialize services
        feature_engineer = SimpleFeatureEngineer(session)
        forecaster = HeuristicForecaster()

        # Check if features exist, generate if needed
        skus = await feature_engineer.get_all_skus(request.upload_id)

        if not skus:
            # Generate features
            result = await feature_engineer.engineer_features(request.upload_id)
            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])
            skus = await feature_engineer.get_all_skus(request.upload_id)

        if not skus:
            raise HTTPException(
                status_code=404, detail=f"No data found for upload {request.upload_id}"
            )

        # Filter SKUs if specified
        if request.sku_ids:
            skus = [s for s in skus if s in request.sku_ids]

        if not skus:
            raise HTTPException(
                status_code=404, detail="No SKUs found matching the request"
            )

        # Generate forecasts for each SKU
        sku_forecasts = []
        for sku_id in skus[:100]:  # Limit to 100 SKUs for MVP
            try:
                # Get features for SKU
                df = await feature_engineer.get_features_for_sku(
                    request.upload_id, sku_id
                )

                if len(df) == 0:
                    continue

                # Generate forecast using AnalysisPipeline
                # Step 1: Analyze data and select best method
                pipeline = AnalysisPipeline()
                selection_result = pipeline.select_best_method(df)

                # Step 2: Generate forecast using selected method
                forecast_result = forecaster.generate_forecast(
                    df,
                    horizon_weeks=request.horizon_weeks,
                    method=selection_result["selected_method"],
                )

                # Step 3: Combine results
                forecast_result["analysis"] = selection_result["analysis"]
                forecast_result["backtest_results"] = selection_result[
                    "backtest_results"
                ]
                forecast_result["reasoning"] = selection_result["reasoning"]

                # Format response
                weekly_forecasts = [
                    WeeklyForecast(**week)
                    for week in forecast_result["weekly_forecasts"]
                ]

                sku_forecasts.append(
                    SKUForecast(
                        sku_id=sku_id,
                        horizon_weeks=request.horizon_weeks,
                        method=forecast_result["method"],
                        historical_avg=forecast_result["historical_avg"],
                        historical_std=forecast_result["historical_std"],
                        weekly_forecasts=weekly_forecasts,
                        analysis=forecast_result.get("analysis", {}),
                        backtest_results=forecast_result.get("backtest_results", {}),
                        reasoning=forecast_result.get("reasoning", ""),
                    )
                )

            except Exception as e:
                # Log error but continue with other SKUs
                print(f"Error forecasting SKU {sku_id}: {e}")
                continue

        return ForecastResponse(
            upload_id=request.upload_id,
            generated_at=datetime.utcnow().isoformat(),
            sku_count=len(sku_forecasts),
            forecasts=sku_forecasts,
        )


@router.get("/{upload_id}/accuracy")
async def get_forecast_accuracy(
    upload_id: str,
    sku_id: Optional[str] = Query(None, description="Specific SKU to analyze"),
):
    """
    Compare heuristic accuracy via backtesting

    Tests all heuristics on recent data and returns comparison.
    """
    async with AsyncSessionLocal() as session:
        feature_engineer = SimpleFeatureEngineer(session)

        # Get SKUs
        if sku_id:
            skus = [sku_id]
        else:
            skus = await feature_engineer.get_all_skus(upload_id)

        if not skus:
            raise HTTPException(status_code=404, detail="No data found")

        # Analyze first SKU (MVP: just one for simplicity)
        df = await feature_engineer.get_features_for_sku(upload_id, skus[0])

        if len(df) < 14:
            return {
                "error": "Not enough data for backtest (need 14+ days)",
                "sku_id": skus[0],
                "data_points": len(df),
            }

        # Run backtest
        results = ForecastEvaluator.backtest_all_methods(df, test_days=7)

        return {
            "upload_id": upload_id,
            "sku_id": skus[0],
            "backtest_days": 7,
            "methods": results,
            "recommendation": results[0]["method"] if results else None,
        }


@router.post("/{upload_id}/features/generate")
async def generate_features(upload_id: str):
    """
    Generate 10 core features for an upload

    Call this before forecasting if features don't exist.
    """
    async with AsyncSessionLocal() as session:
        engineer = SimpleFeatureEngineer(session)
        result = await engineer.engineer_features(upload_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return {
            "status": "success",
            "upload_id": upload_id,
            "records_created": result["records_created"],
            "skus_processed": result["skus_processed"],
            "date_range": result["date_range"],
        }

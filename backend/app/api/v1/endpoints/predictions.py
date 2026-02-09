from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.predictor import PredictorService

router = APIRouter()
predictor_service = PredictorService()

@router.post("/predict", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a prediction based on input data
    """
    try:
        result = predictor_service.predict(request.data)
        
        # TODO: Save prediction to database
        # prediction = Prediction(
        #     input_data=request.data,
        #     prediction_result=result,
        #     confidence=result.get("confidence"),
        #     model_version=request.model_version
        # )
        # db.add(prediction)
        
        return PredictionResponse(
            prediction=result.get("prediction"),
            confidence=result.get("confidence"),
            model_version=request.model_version
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@router.get("/predictions")
async def get_predictions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get prediction history
    """
    # TODO: Implement fetching predictions from database
    return {"message": "Not implemented yet", "skip": skip, "limit": limit}

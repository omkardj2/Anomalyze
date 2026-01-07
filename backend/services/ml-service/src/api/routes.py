"""
Anomalyze ML Service - Enhanced API Routes

Production-grade REST API with:
- User-specific profile endpoints
- Enhanced inference with feature contributions
- Training with validation
- Comprehensive error handling
"""
from datetime import datetime
import time
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import structlog

from src.config import get_settings
from src.api.schemas import (
    HealthResponse, TrainingRequest, TrainingStatusResponse,
    ModelInfo, ModelListResponse, PromoteResponse,
    InferenceRequest, InferenceResponse, AnalysisResult, Verdict, Severity,
    TrainingJobStatus, TransactionData
)
from src.ml.model import get_model
from src.ml.features import get_feature_engineer

logger = structlog.get_logger()
router = APIRouter(prefix="/v1", tags=["ML Service"])

# In-memory job tracking
_training_jobs: dict[str, TrainingStatusResponse] = {}


# ============================================
# Enhanced Response Models
# ============================================

class EnhancedInferenceResponse(BaseModel):
    """Enhanced inference response with user context."""
    analysis: AnalysisResult
    verdict: Verdict
    user_context: dict = Field(default_factory=dict)
    feature_contributions: list[dict] = Field(default_factory=list)
    processing_time_ms: float


class UserProfileResponse(BaseModel):
    """User profile summary."""
    user_id: str
    total_transactions: int
    is_mature: bool
    avg_spend: float
    std_spend: float
    peak_hours: list[int]
    top_merchants: list[str]


# ============================================
# Health Check
# ============================================

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check with service status."""
    model = get_model()
    feature_engineer = get_feature_engineer()
    
    return HealthResponse(
        status="healthy",
        model_version=model.version if model.is_loaded else None,
        kafka_connected=True,
        redis_connected=feature_engineer.is_connected
    )


# ============================================
# Training Endpoints
# ============================================

@router.post("/train", response_model=TrainingStatusResponse)
async def trigger_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
) -> TrainingStatusResponse:
    """
    Trigger model training with enhanced 10-feature dataset.
    """
    job_id = str(uuid.uuid4())
    
    job = TrainingStatusResponse(
        job_id=job_id,
        status=TrainingJobStatus.QUEUED,
        progress=0.0,
        message="Training job queued",
        started_at=datetime.now()
    )
    
    _training_jobs[job_id] = job
    background_tasks.add_task(_run_training, job_id, request)
    
    logger.info("training_queued", job_id=job_id)
    return job


async def _run_training(job_id: str, request: TrainingRequest) -> None:
    """Background training job with enhanced features."""
    from src.ml.training import generate_enhanced_dataset, preprocess_data
    
    job = _training_jobs.get(job_id)
    if not job:
        return
    
    try:
        job.status = TrainingJobStatus.RUNNING
        job.message = "Generating training data..."
        job.progress = 0.1
        
        # Generate enhanced dataset
        logger.info("generating_training_data", job_id=job_id)
        df = generate_enhanced_dataset(n_samples=15000, anomaly_ratio=0.05)
        
        job.progress = 0.3
        job.message = "Preprocessing features..."
        
        X = preprocess_data(df)
        
        job.progress = 0.5
        job.message = "Training Isolation Forest (10 features)..."
        
        # Train with enhanced settings
        model = get_model()
        training_result = model.train(
            X,
            contamination=0.05,
            n_estimators=150
        )
        
        job.progress = 0.8
        job.message = "Saving model..."
        
        # Save model
        settings = get_settings()
        new_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model._version = new_version
        model.save(settings.model_path)
        
        job.progress = 1.0
        job.status = TrainingJobStatus.COMPLETED
        job.message = (
            f"Training completed. Model: {new_version}. "
            f"Detected {training_result['detected_anomalies']} anomalies "
            f"({training_result['anomaly_rate']*100:.1f}%)"
        )
        job.completed_at = datetime.now()
        
        logger.info("training_completed", job_id=job_id, version=new_version)
        
    except Exception as e:
        logger.error("training_failed", job_id=job_id, error=str(e))
        job.status = TrainingJobStatus.FAILED
        job.message = f"Training failed: {str(e)}"


@router.get("/train/{job_id}", response_model=TrainingStatusResponse)
async def get_training_status(job_id: str) -> TrainingStatusResponse:
    """Get training job status."""
    job = _training_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


# ============================================
# Model Management
# ============================================

@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """List available models."""
    model = get_model()
    
    models = []
    if model.is_loaded:
        models.append(ModelInfo(
            version=model.version,
            is_active=True,
            trained_at=datetime.now(),
        ))
    
    return ModelListResponse(
        models=models,
        active_version=model.version if model.is_loaded else None
    )


@router.post("/models/{version}/promote", response_model=PromoteResponse)
async def promote_model(version: str) -> PromoteResponse:
    """Promote a model version to active."""
    model = get_model()
    model_path = f"./models/{version}.pkl"
    
    if model.load(model_path, version=version):
        return PromoteResponse(
            success=True,
            message=f"Model {version} promoted",
            promoted_version=version
        )
    else:
        raise HTTPException(status_code=404, detail=f"Model {version} not found")


# ============================================
# Inference Endpoints
# ============================================

@router.post("/inference", response_model=EnhancedInferenceResponse)
async def enhanced_inference(request: InferenceRequest) -> EnhancedInferenceResponse:
    """
    Run inference with user-specific features.
    
    Returns enhanced response with:
    - User context (profile maturity, avg spend)
    - Feature contributions (why it's anomalous)
    - Detailed verdict with explanation
    """
    start_time = time.time()
    
    model = get_model()
    if not model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run POST /v1/train first."
        )
    
    feature_engineer = get_feature_engineer()
    if not feature_engineer.is_connected:
        feature_engineer.connect()
    
    # Extract enhanced features
    features, enrichment, profile = feature_engineer.extract_features(
        user_id=request.user_id,
        amount=request.transaction.amount,
        timestamp=datetime.now(),
        merchant=request.transaction.merchant,
        category=request.transaction.category
    )
    
    # Run inference
    ml_score, ml_prediction, details = model.predict(features)
    
    # Generate verdict
    verdict = _generate_enhanced_verdict(
        transaction=request.transaction,
        enrichment=enrichment,
        ml_score=ml_score,
        ml_prediction=ml_prediction,
        contributions=details.get("top_contributors", [])
    )
    
    # Build user context
    user_context = {
        "is_mature_profile": profile.is_mature,
        "total_transactions": profile.total_transactions,
        "avg_spend": round(profile.spending.avg_amount, 2),
        "std_spend": round(profile.spending.std_amount, 2),
    }
    
    processing_time = (time.time() - start_time) * 1000
    
    return EnhancedInferenceResponse(
        analysis=AnalysisResult(
            rule_flags=[],
            ml_score=ml_score,
            ml_prediction=ml_prediction
        ),
        verdict=verdict,
        user_context=user_context,
        feature_contributions=details.get("top_contributors", []),
        processing_time_ms=round(processing_time, 2)
    )


def _generate_enhanced_verdict(
    transaction: TransactionData,
    enrichment: dict,
    ml_score: float,
    ml_prediction: str,
    contributions: list[dict]
) -> Verdict:
    """Generate detailed verdict with explanation."""
    
    explanations = []
    
    # Check amount-based explanations
    zscore = enrichment.get("amount_zscore", 0)
    if zscore > 3:
        explanations.append(
            f"Amount ${transaction.amount:.2f} is {zscore:.1f} std above your average"
        )
    
    # Check velocity
    velocity_ratio = enrichment.get("velocity_ratio", 1)
    if velocity_ratio > 3:
        explanations.append(
            f"Transaction velocity is {velocity_ratio:.1f}x your normal rate"
        )
    
    # Check hour deviation
    hour_dev = enrichment.get("hour_deviation", 0)
    if hour_dev > 0.7:
        explanations.append("Unusual transaction hour for your profile")
    
    # Add feature contributions
    for contrib in contributions[:2]:
        feature = contrib["feature"]
        if feature == "amount_zscore" and "amount" not in str(explanations):
            explanations.append(f"Amount deviation: {contrib['deviation']:.1f} from expected")
        elif feature == "velocity_ratio" and "velocity" not in str(explanations):
            explanations.append(f"Velocity spike detected")
        elif feature == "merchant_familiarity":
            explanations.append("Unknown merchant for your profile")
    
    # Determine severity
    if ml_score >= 0.8 or zscore > 5:
        severity = Severity.CRITICAL
    elif ml_score >= 0.6 or zscore > 3:
        severity = Severity.HIGH
    elif ml_score >= 0.4 or zscore > 2:
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW
    
    # Build explanation string
    if explanations:
        explanation = ". ".join(explanations) + f". ML Score: {ml_score:.2f}"
    elif ml_prediction == "ANOMALY":
        explanation = f"ML model flagged transaction. Score: {ml_score:.2f}"
    else:
        explanation = f"Transaction appears normal. Score: {ml_score:.2f}"
    
    return Verdict(final_severity=severity, explanation=explanation)


# ============================================
# User Profile Endpoints
# ============================================

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str) -> UserProfileResponse:
    """Get user behavioral profile summary."""
    feature_engineer = get_feature_engineer()
    if not feature_engineer.is_connected:
        feature_engineer.connect()
    
    profile = feature_engineer.get_user_profile(user_id)
    
    return UserProfileResponse(
        user_id=profile.user_id,
        total_transactions=profile.total_transactions,
        is_mature=profile.is_mature,
        avg_spend=round(profile.spending.avg_amount, 2),
        std_spend=round(profile.spending.std_amount, 2),
        peak_hours=profile.time_patterns.peak_hours,
        top_merchants=list(profile.merchants.merchant_counts.keys())[:5]
    )


@router.delete("/users/{user_id}/profile")
async def reset_user_profile(user_id: str) -> dict:
    """Reset user profile (for testing)."""
    feature_engineer = get_feature_engineer()
    
    if feature_engineer._redis:
        key = f"user_profile:{user_id}"
        feature_engineer._redis.delete(key)
        
        # Also clear from cache
        if user_id in feature_engineer._profile_cache:
            del feature_engineer._profile_cache[user_id]
    
    return {"message": f"Profile for {user_id} reset"}


# ============================================
# Scheduled Retraining Endpoints
# ============================================

class RetrainStatusResponse(BaseModel):
    """Scheduled retraining status."""
    is_running: bool
    last_retrain: Optional[str] = None
    next_retrain_in_hours: Optional[float] = None
    retrain_interval_hours: int = 24


class ManualRetrainResponse(BaseModel):
    """Manual retrain result."""
    success: bool
    version: Optional[str] = None
    samples_used: Optional[int] = None
    anomaly_rate: Optional[float] = None
    error: Optional[str] = None


@router.get("/retrain/status", response_model=RetrainStatusResponse)
async def get_retrain_status() -> RetrainStatusResponse:
    """Get scheduled retraining status."""
    from src.ml.scheduler import get_retrainer
    
    retrainer = get_retrainer()
    
    next_in_hours = None
    if retrainer.last_retrain:
        elapsed = (datetime.now() - retrainer.last_retrain).total_seconds() / 3600
        next_in_hours = max(0, 24 - elapsed)
    
    return RetrainStatusResponse(
        is_running=retrainer.is_running,
        last_retrain=retrainer.last_retrain.isoformat() if retrainer.last_retrain else None,
        next_retrain_in_hours=round(next_in_hours, 1) if next_in_hours else None,
        retrain_interval_hours=24
    )


@router.post("/retrain/trigger", response_model=ManualRetrainResponse)
async def trigger_manual_retrain() -> ManualRetrainResponse:
    """
    Manually trigger model retraining using recent transaction data.
    
    This fetches transactions from the last 7 days, extracts features,
    and retrains the Isolation Forest model.
    """
    from src.ml.scheduler import get_retrainer
    
    retrainer = get_retrainer()
    
    if not retrainer.is_running:
        return ManualRetrainResponse(
            success=False,
            error="Retrainer not running. Set DATABASE_URL to enable."
        )
    
    logger.info("manual_retrain_triggered")
    result = await retrainer.retrain_from_transactions()
    
    return ManualRetrainResponse(
        success=result.get("success", False),
        version=result.get("version"),
        samples_used=result.get("samples_used"),
        anomaly_rate=result.get("anomaly_rate"),
        error=result.get("error") or result.get("reason")
    )

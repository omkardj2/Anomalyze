"""Anomalyze ML Service - API Schemas (Pydantic Models)"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================
# Enums
# ============================================

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransactionSource(str, Enum):
    REALTIME_API = "REALTIME_API"
    BATCH_CSV = "BATCH_CSV"


class TrainingJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================
# Kafka Event Schema (from DOCUMENTATION.md)
# ============================================

class TransactionMeta(BaseModel):
    """Metadata for a transaction event."""
    trace_id: str
    timestamp: datetime
    source: TransactionSource
    user_id: str


class TransactionData(BaseModel):
    """Core transaction data."""
    tx_id: str
    amount: float
    currency: str = "USD"
    location: str | None = None
    merchant: str | None = None
    category: str | None = None


class TransactionEnrichment(BaseModel):
    """Feature enrichment data computed from Redis."""
    user_avg_spend: float = 0.0
    tx_count_last_10min: int = 0
    distance_from_last_tx: float | None = None


class AnalysisResult(BaseModel):
    """ML analysis results."""
    rule_flags: list[str] = Field(default_factory=list)
    ml_score: float  # 0.0 - 1.0
    ml_prediction: str  # "NORMAL" or "ANOMALY"


class Verdict(BaseModel):
    """Final anomaly verdict with explanation."""
    final_severity: Severity
    explanation: str


class TransactionEvent(BaseModel):
    """Complete transaction event from Kafka."""
    meta: TransactionMeta
    data: TransactionData
    enrichment: TransactionEnrichment | None = None
    analysis: AnalysisResult | None = None
    verdict: Verdict | None = None


class AnomalyEvent(BaseModel):
    """Anomaly event published to Kafka."""
    meta: TransactionMeta
    data: TransactionData
    enrichment: TransactionEnrichment
    analysis: AnalysisResult
    verdict: Verdict


# ============================================
# API Request/Response Schemas
# ============================================

class DateRange(BaseModel):
    """Date range for filtering."""
    start: datetime
    end: datetime


class TrainingRequest(BaseModel):
    """Request to trigger model training."""
    user_id: str | None = None  # Train specific user model
    date_range: DateRange | None = None


class TrainingStatusResponse(BaseModel):
    """Response for training job status."""
    job_id: str
    status: TrainingJobStatus
    progress: float = 0.0  # 0.0 - 1.0
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ModelInfo(BaseModel):
    """Model metadata."""
    version: str
    accuracy: float | None = None
    is_active: bool = False
    trained_at: datetime | None = None
    path: str | None = None


class ModelListResponse(BaseModel):
    """Response for listing models."""
    models: list[ModelInfo]
    active_version: str | None = None


class PromoteResponse(BaseModel):
    """Response for model promotion."""
    success: bool
    message: str
    promoted_version: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_version: str | None = None
    kafka_connected: bool = False
    redis_connected: bool = False


class InferenceRequest(BaseModel):
    """Manual inference request (for testing)."""
    transaction: TransactionData
    user_id: str


class InferenceResponse(BaseModel):
    """Manual inference response."""
    analysis: AnalysisResult
    verdict: Verdict
    processing_time_ms: float

"""
Anomalyze ML Service - Main FastAPI Application

This is the entry point for the ML service. It provides:
- Health check endpoint
- Training management API
- Model management API  
- Manual inference endpoint (for testing)
- Background Kafka consumer for real-time transaction processing
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from src.config import get_settings
from src.api.routes import router
from src.ml.model import get_model
from src.ml.features import get_feature_engineer
from src.ml.scheduler import get_retrainer
from src.kafka.consumer import get_consumer
from src.kafka.producer import get_producer
from src.repositories.profile_repository import get_profile_repository

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
    - Load ML model
    - Connect to Redis
    - Connect to PostgreSQL (for profile persistence)
    - Connect to Kafka
    - Start consumer loop
    
    Shutdown:
    - Flush profiles to PostgreSQL
    - Stop consumer
    - Disconnect from services
    """
    settings = get_settings()
    logger.info("starting_ml_service", service=settings.service_name)
    
    # Initialize model
    model = get_model()
    try:
        if model.load(settings.model_path, version=settings.model_version):
            logger.info("model_loaded_on_startup", version=model.version)
        else:
            logger.warning("no_model_found_training_required")
    except Exception as e:
        logger.warning("model_load_failed_on_startup", error=str(e))
    
    # Initialize profile repository (Redis + PostgreSQL)
    profile_repo = get_profile_repository()
    try:
        await profile_repo.connect()
        if profile_repo.is_postgres_connected:
            logger.info("profile_persistence_enabled", backend="PostgreSQL")
        else:
            logger.info("profile_persistence_disabled", reason="Redis-only mode")
    except Exception as e:
        logger.warning("profile_repo_init_failed", error=str(e))
    
    # Initialize feature engineer (connects to Redis)
    feature_engineer = get_feature_engineer()
    try:
        feature_engineer.connect()
    except Exception as e:
        logger.warning("redis_connection_failed_on_startup", error=str(e))
    
    # Initialize Kafka producer
    producer = get_producer()
    try:
        producer.connect()
    except Exception as e:
        logger.warning("kafka_producer_connection_failed", error=str(e))
    
    # Initialize and start Kafka consumer
    consumer = get_consumer()
    consumer._producer = producer
    
    consumer_task = None
    try:
        if consumer.connect():
            # Start consumer in background task
            consumer_task = asyncio.create_task(consumer.start())
            logger.info("kafka_consumer_started_in_background")
    except Exception as e:
        logger.warning("kafka_consumer_start_failed", error=str(e))
    
    # Initialize scheduled retrainer (daily auto-retrain)
    retrainer = get_retrainer()
    try:
        if await retrainer.start():
            logger.info("scheduled_retrainer_enabled")
        else:
            logger.info("scheduled_retrainer_disabled", reason="No DATABASE_URL")
    except Exception as e:
        logger.warning("retrainer_start_failed", error=str(e))
    
    yield  # Application is running
    
    # Shutdown
    logger.info("shutting_down_ml_service")
    
    # Stop scheduled retrainer
    try:
        await retrainer.stop()
    except Exception as e:
        logger.warning("retrainer_stop_failed", error=str(e))
    
    # Flush profiles to PostgreSQL and close repository
    try:
        await profile_repo.close()
        logger.info("profile_repo_closed")
    except Exception as e:
        logger.warning("profile_repo_close_failed", error=str(e))
    
    # Stop consumer
    consumer.disconnect()
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    # Disconnect producer
    producer.disconnect()
    
    logger.info("ml_service_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="Anomalyze ML Service",
    description="Machine Learning service for real-time anomaly detection",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Anomalyze ML Service",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.debug
    )

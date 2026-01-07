"""Anomalyze ML Service - Configuration Management"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    service_name: str = Field(default="ml-service")
    service_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    kafka_group_id: str = Field(default="ml-service-group")
    kafka_transactions_topic: str = Field(default="transactions")
    kafka_anomalies_topic: str = Field(default="anomalies")
    kafka_security_protocol: str = Field(default="PLAINTEXT")
    kafka_sasl_mechanism: str | None = Field(default=None)
    kafka_sasl_username: str | None = Field(default=None)
    kafka_sasl_password: str | None = Field(default=None)
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # PostgreSQL Configuration (for profile persistence)
    database_url: str | None = Field(default=None)
    
    # Model Configuration
    model_path: str = Field(default="./models/current_model.pkl")
    model_version: str = Field(default="v1.0.0")
    anomaly_threshold: float = Field(default=0.5)
    
    # Feature Engineering
    velocity_window_seconds: int = Field(default=600)  # 10 minutes
    
    # Storage Configuration
    storage_type: Literal["local", "s3"] = Field(default="local")
    local_storage_path: str = Field(default="./data")
    s3_endpoint_url: str | None = Field(default=None)
    s3_bucket_name: str | None = Field(default=None)
    s3_access_key_id: str | None = Field(default=None)
    s3_secret_access_key: str | None = Field(default=None)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

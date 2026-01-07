"""
Basic tests for ML Service components.
Run with: pytest tests/ -v
"""
import pytest
import numpy as np
from datetime import datetime


class TestAnomalyModel:
    """Tests for the Isolation Forest model wrapper."""
    
    def test_model_initialization(self):
        """Test model can be initialized."""
        from src.ml.model import AnomalyModel
        
        model = AnomalyModel()
        assert model.version == "none"
        assert not model.is_loaded
        assert len(model.feature_names) == 5
    
    def test_model_training(self):
        """Test model can be trained on sample data."""
        from src.ml.model import AnomalyModel
        
        model = AnomalyModel()
        
        # Create sample training data
        np.random.seed(42)
        X = np.random.randn(1000, 5).astype(np.float32)
        
        # Train
        result = model.train(X, contamination=0.1)
        
        assert model.is_loaded
        assert result["n_samples"] == 1000
        assert result["n_features"] == 5
    
    def test_model_prediction(self):
        """Test model can make predictions."""
        from src.ml.model import AnomalyModel
        
        model = AnomalyModel()
        
        # Train on simple data
        np.random.seed(42)
        X = np.random.randn(1000, 5).astype(np.float32)
        model.train(X)
        
        # Make prediction
        test_features = np.array([0.5, 0.5, 0.5, 0.5, 0.5], dtype=np.float32)
        score, prediction = model.predict(test_features)
        
        assert 0.0 <= score <= 1.0
        assert prediction in ["NORMAL", "ANOMALY"]
    
    def test_model_save_load(self, tmp_path):
        """Test model can be saved and loaded."""
        from src.ml.model import AnomalyModel
        
        model = AnomalyModel()
        
        # Train
        X = np.random.randn(500, 5).astype(np.float32)
        model.train(X)
        model._version = "test_v1"
        
        # Save
        model_path = tmp_path / "test_model.pkl"
        assert model.save(model_path)
        
        # Load into new instance
        model2 = AnomalyModel()
        assert model2.load(model_path, version="test_v1")
        assert model2.version == "test_v1"
        assert model2.is_loaded


class TestSampleDataGeneration:
    """Tests for training data generation."""
    
    def test_generate_sample_dataset(self):
        """Test sample dataset generation."""
        from src.ml.training import generate_sample_dataset
        
        df = generate_sample_dataset(n_samples=100, anomaly_ratio=0.1)
        
        assert len(df) == 100
        assert "amount" in df.columns
        assert "velocity" in df.columns
        assert df["amount"].min() > 0
    
    def test_preprocess_data(self):
        """Test data preprocessing."""
        from src.ml.training import generate_sample_dataset, preprocess_data
        
        df = generate_sample_dataset(n_samples=100)
        X = preprocess_data(df)
        
        assert X.shape == (100, 5)
        assert X.dtype == np.float32
        # Check values are in reasonable range after normalization
        assert X.max() <= 1.0
        assert X.min() >= 0.0


class TestSchemas:
    """Tests for Pydantic schemas."""
    
    def test_transaction_data_validation(self):
        """Test TransactionData schema."""
        from src.api.schemas import TransactionData
        
        tx = TransactionData(
            tx_id="tx_001",
            amount=150.00,
            currency="USD",
            merchant="Test Store"
        )
        
        assert tx.tx_id == "tx_001"
        assert tx.amount == 150.00
    
    def test_transaction_event_parsing(self):
        """Test full transaction event parsing."""
        from src.api.schemas import TransactionEvent
        
        event_data = {
            "meta": {
                "trace_id": "trace-123",
                "timestamp": "2025-01-01T12:00:00Z",
                "source": "REALTIME_API",
                "user_id": "user_001"
            },
            "data": {
                "tx_id": "tx_001",
                "amount": 100.00,
                "currency": "USD"
            }
        }
        
        event = TransactionEvent.model_validate(event_data)
        
        assert event.meta.user_id == "user_001"
        assert event.data.amount == 100.00


class TestConfig:
    """Tests for configuration."""
    
    def test_default_config(self, monkeypatch):
        """Test default configuration values."""
        # Clear any cached settings
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.service_name == "ml-service"
        assert settings.service_port == 8000
        assert settings.anomaly_threshold == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

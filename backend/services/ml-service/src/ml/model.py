"""
Anomalyze ML Service - Enhanced Isolation Forest Model

This module wraps the Isolation Forest model with:
- Support for 10 user-specific features
- Thread-safe model loading and hot-swapping
- Hybrid detection (global model + user-specific thresholds)
- Detailed logging and explainability
"""
import math
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
import structlog
from threading import Lock
from typing import Optional

logger = structlog.get_logger()


class AnomalyModel:
    """
    Enhanced Isolation Forest model for user-specific anomaly detection.
    
    Features:
    - 10 user-specific features
    - Thread-safe model operations
    - Hot-swap model versions
    - Sigmoid-based score normalization
    """
    
    # Must match EnhancedFeatureEngineer.FEATURE_NAMES
    FEATURE_NAMES = [
        "log_amount",
        "amount_zscore",
        "amount_percentile",
        "velocity_ratio",
        "hour_deviation",
        "day_deviation",
        "time_since_last",
        "merchant_familiarity",
        "is_new_user",
        "global_amount_flag",
    ]
    
    def __init__(self):
        self._model: Optional[IsolationForest] = None
        self._version: str = "none"
        self._lock = Lock()
        self._n_features = len(self.FEATURE_NAMES)
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def is_loaded(self) -> bool:
        return self._model is not None
    
    @property
    def feature_names(self) -> list[str]:
        return self.FEATURE_NAMES.copy()
    
    @property
    def n_features(self) -> int:
        return self._n_features
    
    def load(self, path: str | Path, version: str = "unknown") -> bool:
        """
        Load a model from disk (thread-safe).
        
        Args:
            path: Path to .pkl file
            version: Version string for tracking
        
        Returns:
            True if loaded successfully
        """
        try:
            path = Path(path)
            if not path.exists():
                logger.warning("model_not_found", path=str(path))
                return False
            
            new_model = joblib.load(path)
            
            with self._lock:
                self._model = new_model
                self._version = version
            
            logger.info("model_loaded", version=version, path=str(path))
            return True
        except Exception as e:
            logger.error("model_load_failed", error=str(e), path=str(path))
            return False
    
    def predict(self, features: np.ndarray) -> tuple[float, str, dict]:
        """
        Run inference on feature array.
        
        Args:
            features: Array of shape (n_features,) or (1, n_features)
        
        Returns:
            tuple: (anomaly_score, prediction, details)
            - anomaly_score: 0.0 (normal) to 1.0 (highly anomalous)
            - prediction: "NORMAL" or "ANOMALY"
            - details: Dict with raw scores and feature contributions
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call train() or load() first.")
        
        # Ensure correct shape
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        if features.shape[1] != self._n_features:
            raise ValueError(
                f"Expected {self._n_features} features, got {features.shape[1]}"
            )
        
        with self._lock:
            # Get raw prediction (-1 = anomaly, 1 = normal)
            raw_prediction = int(self._model.predict(features)[0])
            
            # Get decision function score
            # Positive = normal, Negative = anomaly
            raw_score = float(self._model.decision_function(features)[0])
            
            # Convert to 0-1 scale using sigmoid
            # Negative raw_score → high anomaly_score
            k = 8  # Scaling factor
            anomaly_score = 1.0 / (1.0 + math.exp(raw_score * k))
            anomaly_score = float(max(0.0, min(1.0, anomaly_score)))
            
            prediction = "ANOMALY" if raw_prediction == -1 else "NORMAL"
            
            # Calculate feature contributions (approximate)
            contributions = self._calculate_contributions(features[0])
            
            details = {
                "raw_decision_score": round(raw_score, 4),
                "raw_prediction": int(raw_prediction),
                "anomaly_score": round(anomaly_score, 4),
                "top_contributors": contributions,
            }
            
            logger.debug(
                "prediction_made",
                anomaly_score=round(anomaly_score, 3),
                prediction=prediction,
                raw_score=round(raw_score, 3)
            )
            
            return anomaly_score, prediction, details
    
    def _calculate_contributions(self, features: np.ndarray) -> list[dict]:
        """
        Calculate approximate feature contributions to anomaly score.
        
        Uses deviation from expected values to estimate contribution.
        """
        contributions = []
        
        # Expected values for normal transactions (from training)
        expected = {
            "log_amount": 4.0,
            "amount_zscore": 0.0,
            "amount_percentile": 0.5,
            "velocity_ratio": 1.0,
            "hour_deviation": 0.15,
            "day_deviation": 0.1,
            "time_since_last": 0.15,
            "merchant_familiarity": 0.6,
            "is_new_user": 0.0,
            "global_amount_flag": 0.0,
        }
        
        for i, name in enumerate(self.FEATURE_NAMES):
            value = float(features[i])  # Convert numpy to native Python
            exp_value = expected.get(name, 0.5)
            
            # Calculate deviation
            if name in ["amount_zscore", "velocity_ratio"]:
                # Higher is worse
                deviation = max(0.0, value - exp_value)
            elif name in ["merchant_familiarity"]:
                # Lower is worse
                deviation = max(0.0, exp_value - value)
            else:
                deviation = abs(value - exp_value)
            
            if deviation > 0.3:  # Only significant deviations
                contributions.append({
                    "feature": name,
                    "value": round(value, 3),
                    "expected": round(exp_value, 3),
                    "deviation": round(float(deviation), 3),
                })
        
        # Sort by deviation
        contributions.sort(key=lambda x: x["deviation"], reverse=True)
        
        return contributions[:3]  # Top 3 contributors
    
    def save(self, path: str | Path) -> bool:
        """Save current model to disk."""
        if self._model is None:
            logger.error("cannot_save_no_model")
            return False
        
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                joblib.dump(self._model, path)
            
            logger.info("model_saved", path=str(path), version=self._version)
            return True
        except Exception as e:
            logger.error("model_save_failed", error=str(e))
            return False
    
    def train(
        self,
        X: np.ndarray,
        contamination: float = 0.05,
        n_estimators: int = 150,
        max_samples: str | int = "auto",
        random_state: int = 42
    ) -> dict:
        """
        Train a new Isolation Forest model.
        
        Args:
            X: Training data (n_samples, n_features)
            contamination: Expected proportion of anomalies
            n_estimators: Number of trees
            max_samples: Samples per tree
            random_state: Random seed
        
        Returns:
            dict: Training metadata
        """
        if X.shape[1] != self._n_features:
            raise ValueError(
                f"Expected {self._n_features} features, got {X.shape[1]}"
            )
        
        logger.info(
            "training_started",
            n_samples=len(X),
            n_features=X.shape[1],
            contamination=contamination,
            n_estimators=n_estimators
        )
        
        new_model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_samples=max_samples,
            random_state=random_state,
            n_jobs=-1,
            bootstrap=True,
        )
        
        new_model.fit(X)
        
        with self._lock:
            self._model = new_model
        
        # Validate on training data
        scores = new_model.decision_function(X)
        predictions = new_model.predict(X)
        n_anomalies = sum(predictions == -1)
        
        logger.info(
            "training_completed",
            n_samples=len(X),
            detected_anomalies=n_anomalies,
            anomaly_rate=round(n_anomalies / len(X), 3),
            score_range=(round(scores.min(), 3), round(scores.max(), 3))
        )
        
        return {
            "n_samples": len(X),
            "n_features": X.shape[1],
            "contamination": contamination,
            "n_estimators": n_estimators,
            "detected_anomalies": int(n_anomalies),
            "anomaly_rate": round(n_anomalies / len(X), 4),
        }


# Global model instance (singleton)
_model_instance: Optional[AnomalyModel] = None


def get_model() -> AnomalyModel:
    """Get the global model instance."""
    global _model_instance
    if _model_instance is None:
        _model_instance = AnomalyModel()
    return _model_instance

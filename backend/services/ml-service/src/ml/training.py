"""
Anomalyze ML Service - Enhanced Training Pipeline

Generates training data that matches the 10-feature format used by
EnhancedFeatureEngineer. Creates realistic user behavior patterns
including normal transactions and various types of anomalies.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import structlog

logger = structlog.get_logger()

# Feature names must match EnhancedFeatureEngineer.FEATURE_NAMES
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


def generate_enhanced_dataset(
    n_samples: int = 10000,
    anomaly_ratio: float = 0.05
) -> pd.DataFrame:
    """
    Generate training dataset with 10 user-specific features.
    
    Creates realistic patterns for:
    - Normal transactions (varied amounts, business hours, known merchants)
    - Amount anomalies (unusually high for user)
    - Velocity anomalies (burst of transactions)
    - Time anomalies (late night, unusual days)
    - Merchant anomalies (new/unknown merchants)
    
    Args:
        n_samples: Total samples to generate
        anomaly_ratio: Proportion of anomalies (default 5%)
    
    Returns:
        DataFrame with features matching FEATURE_NAMES
    """
    logger.info("generating_enhanced_dataset", n_samples=n_samples, anomaly_ratio=anomaly_ratio)
    
    n_anomalies = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalies
    
    # =========================================
    # NORMAL TRANSACTIONS
    # =========================================
    normal_data = {
        # Typical amounts with log transform
        'log_amount': np.log1p(np.random.lognormal(mean=4.0, sigma=0.6, size=n_normal)),
        # Z-score close to 0 for normal (within 2 std)
        'amount_zscore': np.random.normal(0, 0.8, size=n_normal),
        # Percentile evenly distributed
        'amount_percentile': np.random.uniform(0.1, 0.9, size=n_normal),
        # Velocity close to user's average
        'velocity_ratio': np.random.lognormal(0, 0.3, size=n_normal).clip(0.1, 3),
        # Transacting during typical hours
        'hour_deviation': np.random.uniform(0, 0.3, size=n_normal),
        # Transacting on typical days
        'day_deviation': np.random.uniform(0, 0.2, size=n_normal),
        # Normal gaps between transactions
        'time_since_last': np.random.uniform(0, 0.3, size=n_normal),
        # Known merchants
        'merchant_familiarity': np.random.uniform(0.3, 1.0, size=n_normal),
        # Mix of new and established users
        'is_new_user': np.random.choice([0, 1], size=n_normal, p=[0.7, 0.3]),
        # Normal amounts globally
        'global_amount_flag': np.zeros(n_normal),
    }
    
    # =========================================
    # ANOMALOUS TRANSACTIONS (Mixed types)
    # =========================================
    # Split anomalies into different types
    n_amount = n_anomalies // 4
    n_velocity = n_anomalies // 4
    n_time = n_anomalies // 4
    n_combined = n_anomalies - n_amount - n_velocity - n_time
    
    anomaly_data = {
        'log_amount': [],
        'amount_zscore': [],
        'amount_percentile': [],
        'velocity_ratio': [],
        'hour_deviation': [],
        'day_deviation': [],
        'time_since_last': [],
        'merchant_familiarity': [],
        'is_new_user': [],
        'global_amount_flag': [],
    }
    
    # Type 1: Amount anomalies (high spending)
    for _ in range(n_amount):
        anomaly_data['log_amount'].append(np.log1p(np.random.lognormal(7, 0.8)))
        anomaly_data['amount_zscore'].append(np.random.uniform(3, 8))  # 3-8 std above
        anomaly_data['amount_percentile'].append(np.random.uniform(0.95, 1.0))
        anomaly_data['velocity_ratio'].append(np.random.uniform(0.5, 2.0))  # Normal velocity
        anomaly_data['hour_deviation'].append(np.random.uniform(0, 0.4))
        anomaly_data['day_deviation'].append(np.random.uniform(0, 0.3))
        anomaly_data['time_since_last'].append(np.random.uniform(0, 0.4))
        anomaly_data['merchant_familiarity'].append(np.random.uniform(0, 0.5))
        anomaly_data['is_new_user'].append(np.random.choice([0, 1], p=[0.6, 0.4]))
        anomaly_data['global_amount_flag'].append(np.random.uniform(0.5, 1.0))
    
    # Type 2: Velocity anomalies (rapid transactions)
    for _ in range(n_velocity):
        anomaly_data['log_amount'].append(np.log1p(np.random.lognormal(4, 0.6)))
        anomaly_data['amount_zscore'].append(np.random.uniform(-1, 2))
        anomaly_data['amount_percentile'].append(np.random.uniform(0.3, 0.8))
        anomaly_data['velocity_ratio'].append(np.random.uniform(4, 10))  # 4-10x normal
        anomaly_data['hour_deviation'].append(np.random.uniform(0, 0.5))
        anomaly_data['day_deviation'].append(np.random.uniform(0, 0.4))
        anomaly_data['time_since_last'].append(np.random.uniform(0.7, 1.0))  # Very recent
        anomaly_data['merchant_familiarity'].append(np.random.uniform(0, 0.4))
        anomaly_data['is_new_user'].append(np.random.choice([0, 1], p=[0.5, 0.5]))
        anomaly_data['global_amount_flag'].append(np.random.uniform(0, 0.3))
    
    # Type 3: Time anomalies (unusual hours/days)
    for _ in range(n_time):
        anomaly_data['log_amount'].append(np.log1p(np.random.lognormal(4.5, 0.7)))
        anomaly_data['amount_zscore'].append(np.random.uniform(-0.5, 1.5))
        anomaly_data['amount_percentile'].append(np.random.uniform(0.4, 0.85))
        anomaly_data['velocity_ratio'].append(np.random.uniform(0.5, 2.5))
        anomaly_data['hour_deviation'].append(np.random.uniform(0.7, 1.0))  # Very unusual hour
        anomaly_data['day_deviation'].append(np.random.uniform(0.6, 1.0))  # Unusual day
        anomaly_data['time_since_last'].append(np.random.uniform(0, 0.5))
        anomaly_data['merchant_familiarity'].append(np.random.uniform(0.1, 0.6))
        anomaly_data['is_new_user'].append(np.random.choice([0, 1], p=[0.7, 0.3]))
        anomaly_data['global_amount_flag'].append(np.random.uniform(0, 0.2))
    
    # Type 4: Combined anomalies (multiple red flags)
    for _ in range(n_combined):
        anomaly_data['log_amount'].append(np.log1p(np.random.lognormal(6, 1.0)))
        anomaly_data['amount_zscore'].append(np.random.uniform(2, 6))
        anomaly_data['amount_percentile'].append(np.random.uniform(0.9, 1.0))
        anomaly_data['velocity_ratio'].append(np.random.uniform(3, 8))
        anomaly_data['hour_deviation'].append(np.random.uniform(0.5, 0.9))
        anomaly_data['day_deviation'].append(np.random.uniform(0.4, 0.8))
        anomaly_data['time_since_last'].append(np.random.uniform(0.5, 1.0))
        anomaly_data['merchant_familiarity'].append(np.random.uniform(0, 0.2))  # Unknown
        anomaly_data['is_new_user'].append(np.random.choice([0, 1], p=[0.4, 0.6]))
        anomaly_data['global_amount_flag'].append(np.random.uniform(0.3, 0.8))
    
    # Convert to DataFrame
    df_normal = pd.DataFrame(normal_data)
    df_anomaly = pd.DataFrame(anomaly_data)
    
    # Combine and shuffle
    df = pd.concat([df_normal, df_anomaly], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Ensure correct column order
    df = df[FEATURE_NAMES]
    
    logger.info(
        "dataset_generated",
        n_samples=len(df),
        n_normal=n_normal,
        n_anomalies=n_anomalies,
        features=len(FEATURE_NAMES)
    )
    
    return df


def preprocess_data(df: pd.DataFrame) -> np.ndarray:
    """Convert DataFrame to numpy array for training."""
    return df[FEATURE_NAMES].values.astype(np.float32)


def generate_test_scenarios() -> list[dict]:
    """
    Generate specific test scenarios for validation.
    
    Returns list of scenarios with expected outcomes.
    """
    scenarios = [
        # Normal transactions
        {
            "name": "normal_coffee",
            "features": {
                "log_amount": np.log1p(5),
                "amount_zscore": 0.0,
                "amount_percentile": 0.5,
                "velocity_ratio": 1.0,
                "hour_deviation": 0.1,
                "day_deviation": 0.1,
                "time_since_last": 0.1,
                "merchant_familiarity": 0.8,
                "is_new_user": 0,
                "global_amount_flag": 0,
            },
            "expected": "NORMAL",
            "max_score": 0.35,
        },
        {
            "name": "normal_groceries",
            "features": {
                "log_amount": np.log1p(150),
                "amount_zscore": 0.5,
                "amount_percentile": 0.6,
                "velocity_ratio": 0.8,
                "hour_deviation": 0.2,
                "day_deviation": 0.1,
                "time_since_last": 0.05,
                "merchant_familiarity": 0.9,
                "is_new_user": 0,
                "global_amount_flag": 0,
            },
            "expected": "NORMAL",
            "max_score": 0.35,
        },
        # Anomalous transactions
        {
            "name": "anomaly_high_amount",
            "features": {
                "log_amount": np.log1p(5000),
                "amount_zscore": 6.0,  # 6 std above average
                "amount_percentile": 0.99,
                "velocity_ratio": 1.0,
                "hour_deviation": 0.2,
                "day_deviation": 0.1,
                "time_since_last": 0.1,
                "merchant_familiarity": 0.3,
                "is_new_user": 0,
                "global_amount_flag": 0.7,
            },
            "expected": "ANOMALY",
            "min_score": 0.5,
        },
        {
            "name": "anomaly_velocity_burst",
            "features": {
                "log_amount": np.log1p(50),
                "amount_zscore": 0.3,
                "amount_percentile": 0.55,
                "velocity_ratio": 8.0,  # 8x normal velocity
                "hour_deviation": 0.3,
                "day_deviation": 0.2,
                "time_since_last": 0.9,  # Very recent tx
                "merchant_familiarity": 0.2,
                "is_new_user": 0,
                "global_amount_flag": 0,
            },
            "expected": "ANOMALY",
            "min_score": 0.45,
        },
        {
            "name": "anomaly_late_night",
            "features": {
                "log_amount": np.log1p(200),
                "amount_zscore": 1.0,
                "amount_percentile": 0.7,
                "velocity_ratio": 1.5,
                "hour_deviation": 0.9,  # Very unusual hour
                "day_deviation": 0.8,  # Unusual day too
                "time_since_last": 0.2,
                "merchant_familiarity": 0.1,  # Unknown merchant
                "is_new_user": 0,
                "global_amount_flag": 0,
            },
            "expected": "ANOMALY",
            "min_score": 0.4,
        },
        {
            "name": "anomaly_new_user_high_amount",
            "features": {
                "log_amount": np.log1p(3000),
                "amount_zscore": 4.0,
                "amount_percentile": 0.95,
                "velocity_ratio": 2.0,
                "hour_deviation": 0.5,
                "day_deviation": 0.4,
                "time_since_last": 0.3,
                "merchant_familiarity": 0.0,  # Unknown
                "is_new_user": 1,  # New user
                "global_amount_flag": 0.5,
            },
            "expected": "ANOMALY",
            "min_score": 0.5,
        },
    ]
    
    return scenarios


def scenario_to_features(scenario: dict) -> np.ndarray:
    """Convert scenario dict to feature array."""
    return np.array([
        scenario["features"][name] for name in FEATURE_NAMES
    ], dtype=np.float32)

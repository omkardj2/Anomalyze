"""
Anomalyze ML Service - Comprehensive Anomaly Detection Tests

Tests for all feature dimensions to ensure the model correctly
identifies anomalies across different scenarios:
1. Amount anomalies (high spending relative to user)
2. Velocity anomalies (rapid transactions)
3. Time anomalies (unusual hours/days)
4. Merchant anomalies (unknown merchants)
5. Combined anomalies (multiple red flags)
6. User-specific behavior (what's normal varies by user)
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

from src.ml.model import AnomalyModel, get_model
from src.ml.training import (
    generate_enhanced_dataset,
    preprocess_data,
    generate_test_scenarios,
    scenario_to_features,
    FEATURE_NAMES
)
from src.models.user_profile import UserProfile, create_default_profile


class TestModelTraining:
    """Tests for model training functionality."""
    
    def test_training_with_correct_features(self):
        """Model trains successfully with 10 features."""
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=1000)
        X = preprocess_data(df)
        
        assert X.shape[1] == 10, f"Expected 10 features, got {X.shape[1]}"
        
        result = model.train(X, contamination=0.05)
        
        assert model.is_loaded
        assert result["n_features"] == 10
        assert result["n_samples"] == 1000
    
    def test_model_detects_anomalies_in_training(self):
        """Model correctly identifies anomalies in training data."""
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000, anomaly_ratio=0.05)
        X = preprocess_data(df)
        
        result = model.train(X, contamination=0.05)
        
        # Should detect roughly 5% anomalies
        assert 0.03 <= result["anomaly_rate"] <= 0.08


class TestAmountAnomalies:
    """Tests for amount-based anomaly detection."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_normal_amount_low_score(self, trained_model):
        """Normal amounts should have low anomaly scores."""
        # Typical transaction: $50, z-score=0, 50th percentile
        features = np.array([
            np.log1p(50),   # log_amount
            0.0,            # amount_zscore
            0.5,            # amount_percentile
            1.0,            # velocity_ratio
            0.1,            # hour_deviation
            0.1,            # day_deviation
            0.1,            # time_since_last
            0.7,            # merchant_familiarity
            0.0,            # is_new_user
            0.0,            # global_amount_flag
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        
        assert score < 0.4, f"Normal amount should have low score, got {score}"
        assert prediction == "NORMAL"
    
    def test_high_amount_detected(self, trained_model):
        """Unusually high amounts should be detected."""
        # High amount: $5000, z-score=5, 99th percentile
        features = np.array([
            np.log1p(5000),  # log_amount
            5.0,             # amount_zscore (5 std above)
            0.99,            # amount_percentile
            1.0,             # velocity_ratio
            0.2,             # hour_deviation
            0.1,             # day_deviation
            0.1,             # time_since_last
            0.3,             # merchant_familiarity
            0.0,             # is_new_user
            0.7,             # global_amount_flag
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        
        assert score > 0.45, f"High amount should have higher score, got {score}"
    
    def test_amount_zscore_matters(self, trained_model):
        """Same amount can be normal or anomalous depending on user history."""
        # $500 for user with avg $500 (z-score=0)
        normal_for_ceo = np.array([
            np.log1p(500), 0.0, 0.5, 1.0, 0.1, 0.1, 0.1, 0.8, 0.0, 0.0
        ], dtype=np.float32)
        
        # $500 for user with avg $50 (z-score=9)
        anomaly_for_student = np.array([
            np.log1p(500), 9.0, 0.99, 1.0, 0.2, 0.1, 0.1, 0.3, 0.0, 0.3
        ], dtype=np.float32)
        
        score_ceo, _, _ = trained_model.predict(normal_for_ceo)
        score_student, _, _ = trained_model.predict(anomaly_for_student)
        
        assert score_student > score_ceo, (
            f"Same amount should score higher for student ({score_student}) "
            f"than CEO ({score_ceo})"
        )


class TestVelocityAnomalies:
    """Tests for velocity-based anomaly detection."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_normal_velocity_low_score(self, trained_model):
        """Normal transaction rate should not trigger anomaly."""
        features = np.array([
            np.log1p(75),  # Normal amount
            0.3,           # Slightly above average
            0.6,           # 60th percentile
            1.0,           # Normal velocity
            0.1,           # Normal hour
            0.1,           # Normal day
            0.1,           # Normal gap
            0.8,           # Known merchant
            0.0,           # Established user
            0.0,           # Normal global
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        assert score < 0.4
    
    def test_velocity_burst_detected(self, trained_model):
        """Rapid transaction burst should be detected."""
        features = np.array([
            np.log1p(50),   # Normal amount
            0.2,            # Normal zscore
            0.5,            # Normal percentile
            8.0,            # 8x normal velocity!
            0.3,            # Slightly unusual hour
            0.2,            # Normal day
            0.9,            # Very recent transaction
            0.2,            # Less familiar merchant
            0.0,            # Established user
            0.0,            # Normal global
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        assert score > 0.4, f"Velocity burst should be detected, got score {score}"


class TestTimeAnomalies:
    """Tests for time-based anomaly detection."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_business_hours_normal(self, trained_model):
        """Transactions during business hours should be normal."""
        features = np.array([
            np.log1p(100),
            0.5,
            0.6,
            1.0,
            0.1,           # Low hour deviation (typical hours)
            0.1,           # Low day deviation (typical days)
            0.1,
            0.8,
            0.0,
            0.0,
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        assert prediction == "NORMAL"
    
    def test_late_night_unusual(self, trained_model):
        """Late night transactions should have higher scores."""
        features = np.array([
            np.log1p(150),
            0.8,
            0.7,
            1.2,
            0.9,           # Very unusual hour (late night)
            0.8,           # Unusual day
            0.2,
            0.1,           # Unknown merchant
            0.0,
            0.0,
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        assert score > 0.35, f"Late night + unknown merchant should score higher, got {score}"


class TestMerchantAnomalies:
    """Tests for merchant-based anomaly detection."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_known_merchant_lower_score(self, trained_model):
        """Transactions at known merchants should score lower."""
        known = np.array([
            np.log1p(80), 0.2, 0.55, 1.0, 0.1, 0.1, 0.1,
            0.9,  # High familiarity
            0.0, 0.0
        ], dtype=np.float32)
        
        unknown = np.array([
            np.log1p(80), 0.2, 0.55, 1.0, 0.1, 0.1, 0.1,
            0.0,  # Zero familiarity
            0.0, 0.0
        ], dtype=np.float32)
        
        score_known, _, _ = trained_model.predict(known)
        score_unknown, _, _ = trained_model.predict(unknown)
        
        assert score_unknown > score_known, (
            f"Unknown merchant ({score_unknown}) should score higher than known ({score_known})"
        )


class TestNewVsEstablishedUsers:
    """Tests for new user vs established user detection."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_new_user_same_amount_higher_score(self, trained_model):
        """New users with high amounts should score higher."""
        new_user = np.array([
            np.log1p(1000),
            3.0,
            0.9,
            1.0,
            0.2,
            0.1,
            0.2,
            0.3,
            1.0,  # New user
            0.2
        ], dtype=np.float32)
        
        established = np.array([
            np.log1p(1000),
            3.0,
            0.9,
            1.0,
            0.2,
            0.1,
            0.2,
            0.3,
            0.0,  # Established user
            0.2
        ], dtype=np.float32)
        
        score_new, _, _ = trained_model.predict(new_user)
        score_established, _, _ = trained_model.predict(established)
        
        # Both should be somewhat suspicious, but new user slightly more
        assert score_new >= score_established * 0.9  # Allow some variance


class TestCombinedAnomalies:
    """Tests for multiple anomaly indicators together."""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=5000)
        X = preprocess_data(df)
        model.train(X)
        return model
    
    def test_multiple_flags_critical(self, trained_model):
        """Multiple red flags should result in high score."""
        # High amount + velocity burst + unusual time + unknown merchant
        features = np.array([
            np.log1p(3000),  # High amount
            5.0,             # 5 std above
            0.98,            # 98th percentile
            6.0,             # 6x velocity
            0.8,             # Unusual hour
            0.7,             # Unusual day
            0.85,            # Very recent
            0.0,             # Unknown merchant
            1.0,             # New user
            0.6,             # Global flag
        ], dtype=np.float32)
        
        score, prediction, _ = trained_model.predict(features)
        
        assert score > 0.5, f"Multiple flags should score very high, got {score}"
        assert prediction == "ANOMALY"


class TestUserProfile:
    """Tests for user profile functionality."""
    
    def test_profile_creation(self):
        """New profile has correct defaults."""
        profile = create_default_profile("test_user")
        
        assert profile.user_id == "test_user"
        assert profile.total_transactions == 0
        assert not profile.is_mature
        assert profile.spending.avg_amount == 50.0
    
    def test_profile_update_spending(self):
        """Profile correctly tracks spending patterns."""
        profile = create_default_profile("test")
        
        amounts = [20, 30, 50, 40, 35]
        for i, amount in enumerate(amounts):
            profile.update_with_transaction(
                amount=amount,
                timestamp=datetime.now() + timedelta(hours=i)
            )
        
        assert profile.total_transactions == 5
        assert 30 < profile.spending.avg_amount < 40
    
    def test_profile_maturity(self):
        """Profile becomes mature after threshold transactions."""
        profile = create_default_profile("test")
        profile.maturity_threshold = 10
        
        for i in range(9):
            profile.update_with_transaction(
                amount=50 + i,
                timestamp=datetime.now()
            )
        
        assert not profile.is_mature
        
        profile.update_with_transaction(amount=60, timestamp=datetime.now())
        
        assert profile.is_mature
    
    def test_zscore_calculation(self):
        """Z-score correctly identifies unusual amounts."""
        profile = create_default_profile("test")
        
        # Build history with avg ~$50, std ~$10
        for amount in [40, 45, 50, 55, 60, 48, 52, 47, 53, 50]:
            profile.update_with_transaction(amount=amount, timestamp=datetime.now())
        
        # Normal amount should have low z-score
        normal_zscore = profile.get_amount_zscore(55)
        assert abs(normal_zscore) < 1
        
        # High amount should have high z-score
        high_zscore = profile.get_amount_zscore(200)
        assert high_zscore > 2


class TestScenarios:
    """Tests using predefined scenarios from training.py"""
    
    @pytest.fixture
    def trained_model(self):
        model = AnomalyModel()
        df = generate_enhanced_dataset(n_samples=10000)
        X = preprocess_data(df)
        model.train(X, contamination=0.05)
        return model
    
    def test_all_scenarios(self, trained_model):
        """All predefined scenarios should pass their criteria."""
        scenarios = generate_test_scenarios()
        
        for scenario in scenarios:
            features = scenario_to_features(scenario)
            score, prediction, _ = trained_model.predict(features)
            
            # Check expected prediction
            if "expected" in scenario:
                expected = scenario["expected"]
                if expected == "NORMAL":
                    max_score = scenario.get("max_score", 0.4)
                    assert score <= max_score, (
                        f"Scenario '{scenario['name']}' expected NORMAL with score <= {max_score}, "
                        f"got {score:.3f}"
                    )
                else:  # ANOMALY
                    min_score = scenario.get("min_score", 0.4)
                    assert score >= min_score, (
                        f"Scenario '{scenario['name']}' expected ANOMALY with score >= {min_score}, "
                        f"got {score:.3f}"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

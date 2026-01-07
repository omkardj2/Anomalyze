"""
Anomalyze ML Service - Enhanced Feature Engineering with User Profiles

This module extracts user-specific features for anomaly detection.
Features are designed to capture deviations from a user's typical behavior,
not just global anomalies.

Feature Categories:
1. Amount Features - Z-score, percentile relative to user history
2. Time Features - Deviation from user's typical hours/days
3. Velocity Features - Current vs user's typical transaction rate
4. Merchant Features - Familiarity with the merchant
5. Session Features - Behavior in current transaction burst
"""
import numpy as np
from datetime import datetime
from typing import Optional
import json
import redis
import structlog

from src.config import get_settings
from src.models.user_profile import UserProfile, create_default_profile

logger = structlog.get_logger()


class EnhancedFeatureEngineer:
    """
    Enhanced feature engineering with user-specific behavioral profiles.
    
    This class maintains user profiles in Redis and extracts features
    that capture deviations from each user's normal behavior.
    """
    
    # Feature names must match training data exactly
    FEATURE_NAMES = [
        "log_amount",           # 0: Log-transformed amount
        "amount_zscore",        # 1: Z-score relative to user's history
        "amount_percentile",    # 2: Percentile in user's history (0-1)
        "velocity_ratio",       # 3: Current velocity / user's typical velocity
        "hour_deviation",       # 4: How unusual is this hour for user (0-1)
        "day_deviation",        # 5: How unusual is this day for user (0-1)
        "time_since_last",      # 6: Normalized time since last transaction
        "merchant_familiarity", # 7: Has user used this merchant before (0-1)
        "is_new_user",          # 8: User has < 20 transactions (0 or 1)
        "global_amount_flag",   # 9: Is amount globally unusual (log scale)
    ]
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.settings = get_settings()
        self._redis = redis_client
        self._profile_cache: dict[str, UserProfile] = {}
        self._profile_ttl = 3600  # Cache TTL in seconds
    
    def connect(self) -> bool:
        """Connect to Redis."""
        if self._redis is not None:
            return True
        
        try:
            self._redis = redis.from_url(
                self.settings.redis_url,
                decode_responses=True
            )
            self._redis.ping()
            logger.info("redis_connected", url=self.settings.redis_url)
            return True
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            self._redis = None
            return False
    
    @property
    def is_connected(self) -> bool:
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except:
            return False
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Get or create user profile from Redis.
        
        Uses local cache to reduce Redis calls.
        """
        # Check local cache first
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]
        
        # Try to load from Redis
        if self._redis:
            try:
                key = f"user_profile:{user_id}"
                data = self._redis.get(key)
                if data:
                    profile = UserProfile.from_redis_dict(json.loads(data))
                    self._profile_cache[user_id] = profile
                    return profile
            except Exception as e:
                logger.warning("profile_load_failed", user_id=user_id, error=str(e))
        
        # Create new profile
        profile = create_default_profile(user_id)
        self._profile_cache[user_id] = profile
        return profile
    
    def save_user_profile(self, profile: UserProfile) -> bool:
        """Save user profile to Redis."""
        if not self._redis:
            return False
        
        try:
            key = f"user_profile:{profile.user_id}"
            data = json.dumps(profile.to_redis_dict())
            self._redis.setex(key, self._profile_ttl * 24, data)  # 24 hour TTL
            self._profile_cache[profile.user_id] = profile
            return True
        except Exception as e:
            logger.warning("profile_save_failed", user_id=profile.user_id, error=str(e))
            return False
    
    def extract_features(
        self,
        user_id: str,
        amount: float,
        timestamp: datetime,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
    ) -> tuple[np.ndarray, dict, UserProfile]:
        """
        Extract enhanced features for a transaction.
        
        Args:
            user_id: User identifier
            amount: Transaction amount (raw dollars)
            timestamp: Transaction time
            merchant: Optional merchant name
            category: Optional category
        
        Returns:
            tuple: (features_array, enrichment_dict, updated_profile)
        """
        # Get user profile
        profile = self.get_user_profile(user_id)
        
        # Get current velocity from Redis
        current_velocity = self._get_current_velocity(user_id)
        
        # ==================================================
        # FEATURE 0: Log Amount (global scale)
        # ==================================================
        log_amount = np.log1p(amount)
        
        # ==================================================
        # FEATURE 1: Amount Z-Score (user-specific)
        # ==================================================
        if profile.is_mature:
            amount_zscore = profile.get_amount_zscore(amount)
            # Clip to reasonable range
            amount_zscore = np.clip(amount_zscore, -5, 10)
        else:
            # For new users, use global baseline
            global_avg = 50.0
            global_std = 30.0
            amount_zscore = (amount - global_avg) / global_std
            amount_zscore = np.clip(amount_zscore, -5, 10)
        
        # ==================================================
        # FEATURE 2: Amount Percentile (user-specific)
        # ==================================================
        if profile.is_mature:
            amount_percentile = profile.get_amount_percentile(amount) / 100.0
        else:
            # For new users, estimate from global distribution
            # Assume log-normal with mean $50
            if amount < 25:
                amount_percentile = 0.25
            elif amount < 75:
                amount_percentile = 0.5
            elif amount < 200:
                amount_percentile = 0.75
            else:
                amount_percentile = 0.95
        
        # ==================================================
        # FEATURE 3: Velocity Ratio (user-specific)
        # ==================================================
        if profile.is_mature and profile.velocity.avg_10min_count > 0:
            velocity_ratio = current_velocity / max(profile.velocity.avg_10min_count, 0.1)
        else:
            # For new users, compare to global baseline
            velocity_ratio = current_velocity / 1.0  # Expect ~1 tx per 10 min
        velocity_ratio = min(velocity_ratio, 10.0)  # Cap at 10x
        
        # ==================================================
        # FEATURE 4: Hour Deviation (user-specific)
        # ==================================================
        hour = timestamp.hour
        if profile.is_mature:
            hour_prob = profile.get_hour_probability(hour)
            # Convert to deviation: lower prob = higher deviation
            hour_deviation = 1.0 - min(hour_prob * 24, 1.0)  # Normalize
        else:
            # For new users, flag late night hours
            if 2 <= hour <= 5:
                hour_deviation = 0.9  # Very unusual
            elif 6 <= hour <= 8 or 21 <= hour <= 23:
                hour_deviation = 0.3  # Slightly unusual
            else:
                hour_deviation = 0.1  # Normal business hours
        
        # ==================================================
        # FEATURE 5: Day Deviation (user-specific)
        # ==================================================
        day = timestamp.weekday()
        if profile.is_mature:
            day_prob = profile.get_day_probability(day)
            day_deviation = 1.0 - min(day_prob * 7, 1.0)
        else:
            # Weekends slightly more suspicious for new users
            if day >= 5:  # Saturday, Sunday
                day_deviation = 0.3
            else:
                day_deviation = 0.1
        
        # ==================================================
        # FEATURE 6: Time Since Last Transaction
        # ==================================================
        if profile.last_transaction_at:
            gap_seconds = (timestamp - profile.last_transaction_at).total_seconds()
            # Normalize: very short gaps are suspicious
            # Use sigmoid to map seconds to 0-1
            # < 60 seconds → high value (suspicious)
            # > 1 hour → low value (normal)
            time_since_last = 1.0 / (1.0 + np.exp((gap_seconds - 300) / 100))
        else:
            time_since_last = 0.0  # First transaction
        
        # ==================================================
        # FEATURE 7: Merchant Familiarity
        # ==================================================
        if merchant and profile.is_mature:
            if profile.is_known_merchant(merchant):
                merchant_freq = profile.get_merchant_frequency(merchant)
                merchant_familiarity = min(merchant_freq * 10, 1.0)  # Familiar = low risk
            else:
                merchant_familiarity = 0.0  # Unknown merchant
        else:
            merchant_familiarity = 0.5  # Neutral for new users
        
        # ==================================================
        # FEATURE 8: Is New User
        # ==================================================
        is_new_user = 0.0 if profile.is_mature else 1.0
        
        # ==================================================
        # FEATURE 9: Global Amount Flag
        # ==================================================
        # Flag globally unusual amounts (regardless of user)
        if amount > 1000:
            global_amount_flag = min(np.log1p(amount - 1000) / 5, 1.0)
        else:
            global_amount_flag = 0.0
        
        # ==================================================
        # Build feature vector
        # ==================================================
        features = np.array([
            log_amount,
            amount_zscore,
            amount_percentile,
            velocity_ratio,
            hour_deviation,
            day_deviation,
            time_since_last,
            merchant_familiarity,
            is_new_user,
            global_amount_flag,
        ], dtype=np.float32)
        
        # ==================================================
        # Update profile with this transaction
        # ==================================================
        profile.update_with_transaction(
            amount=amount,
            timestamp=timestamp,
            merchant=merchant,
            category=category
        )
        
        # Update velocity in Redis
        self._record_transaction(user_id, amount, timestamp)
        
        # Save updated profile
        self.save_user_profile(profile)
        
        # ==================================================
        # Build enrichment dict for Kafka/API response
        # ==================================================
        enrichment = {
            "user_avg_spend": float(round(profile.spending.avg_amount, 2)),
            "user_std_spend": float(round(profile.spending.std_amount, 2)),
            "amount_zscore": float(round(amount_zscore, 2)),
            "amount_percentile": float(round(amount_percentile * 100, 1)),
            "tx_count_last_10min": int(current_velocity),
            "velocity_ratio": float(round(velocity_ratio, 2)),
            "hour_deviation": float(round(hour_deviation, 2)),
            "is_mature_profile": bool(profile.is_mature),
            "total_transactions": int(profile.total_transactions),
            "distance_from_last_tx": None,
        }
        
        logger.debug(
            "features_extracted",
            user_id=user_id,
            is_mature=profile.is_mature,
            amount=amount,
            zscore=round(amount_zscore, 2),
            features_shape=features.shape
        )
        
        return features, enrichment, profile
    
    def _get_current_velocity(self, user_id: str) -> int:
        """Get current 10-minute transaction velocity from Redis."""
        if not self._redis:
            return 0
        
        try:
            key = f"velocity:{user_id}"
            min_time = datetime.now().timestamp() - self.settings.velocity_window_seconds
            count = self._redis.zcount(key, min_time, "+inf")
            return int(count)
        except Exception as e:
            logger.warning("get_velocity_failed", user_id=user_id, error=str(e))
            return 0
    
    def _record_transaction(
        self,
        user_id: str,
        amount: float,
        timestamp: datetime
    ) -> None:
        """Record transaction in Redis for velocity tracking."""
        if not self._redis:
            return
        
        try:
            pipe = self._redis.pipeline()
            
            # Update velocity sorted set
            velocity_key = f"velocity:{user_id}"
            tx_id = f"{timestamp.timestamp()}"
            pipe.zadd(velocity_key, {tx_id: timestamp.timestamp()})
            
            # Cleanup old entries
            min_time = timestamp.timestamp() - self.settings.velocity_window_seconds
            pipe.zremrangebyscore(velocity_key, "-inf", min_time)
            
            # Set TTL
            pipe.expire(velocity_key, self.settings.velocity_window_seconds * 2)
            
            pipe.execute()
        except Exception as e:
            logger.warning("record_tx_failed", user_id=user_id, error=str(e))
    
    def get_feature_names(self) -> list[str]:
        """Get list of feature names in order."""
        return self.FEATURE_NAMES.copy()
    
    def get_enrichment_for_user(self, user_id: str) -> dict:
        """Get current enrichment data for a user (debugging)."""
        profile = self.get_user_profile(user_id)
        return {
            "user_avg_spend": profile.spending.avg_amount,
            "user_std_spend": profile.spending.std_amount,
            "total_transactions": profile.total_transactions,
            "is_mature": profile.is_mature,
            "tx_count_last_10min": self._get_current_velocity(user_id),
        }


# Global instance
_feature_engineer: Optional[EnhancedFeatureEngineer] = None


def get_feature_engineer() -> EnhancedFeatureEngineer:
    """Get the global feature engineer instance."""
    global _feature_engineer
    if _feature_engineer is None:
        _feature_engineer = EnhancedFeatureEngineer()
    return _feature_engineer

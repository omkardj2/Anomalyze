"""
Anomalyze ML Service - User Behavioral Profile Model

This module defines the UserProfile class that stores comprehensive behavioral
patterns for each user. The profile enables user-specific anomaly detection
where what's normal for one user might be anomalous for another.

Example:
    Student (avg $25) spending $500 → ANOMALY
    CEO (avg $500) spending $500 → NORMAL
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import numpy as np


class SpendingStats(BaseModel):
    """Statistical summary of user's spending behavior."""
    avg_amount: float = Field(default=0.0, description="Average transaction amount")
    std_amount: float = Field(default=1.0, description="Standard deviation of amounts")
    min_amount: float = Field(default=0.0, description="Minimum transaction amount")
    max_amount: float = Field(default=0.0, description="Maximum transaction amount")
    median_amount: float = Field(default=0.0, description="Median transaction amount")
    p25_amount: float = Field(default=0.0, description="25th percentile")
    p75_amount: float = Field(default=0.0, description="75th percentile")
    p95_amount: float = Field(default=0.0, description="95th percentile (high amounts)")


class TimePatterns(BaseModel):
    """User's typical transaction time patterns."""
    # Hourly distribution (24 values, how often they transact at each hour)
    hour_distribution: list[float] = Field(
        default_factory=lambda: [1/24] * 24,
        description="Probability distribution over hours (0-23)"
    )
    # Day of week distribution (7 values)
    day_distribution: list[float] = Field(
        default_factory=lambda: [1/7] * 7,
        description="Probability distribution over days (0=Mon, 6=Sun)"
    )
    # Peak activity hours
    peak_hours: list[int] = Field(
        default_factory=lambda: list(range(9, 21)),
        description="Hours when user typically transacts"
    )
    # Active days
    active_days: list[int] = Field(
        default_factory=lambda: list(range(5)),
        description="Days when user typically transacts (0=Mon)"
    )


class VelocityPatterns(BaseModel):
    """User's transaction velocity patterns."""
    avg_daily_count: float = Field(default=1.0, description="Average transactions per day")
    avg_hourly_count: float = Field(default=0.1, description="Average transactions per hour")
    avg_10min_count: float = Field(default=0.02, description="Average transactions per 10min")
    max_10min_count: int = Field(default=3, description="Max transactions seen in 10min window")
    avg_gap_seconds: float = Field(default=86400, description="Average time between transactions")


class MerchantPatterns(BaseModel):
    """User's merchant and category preferences."""
    # Top merchants by frequency
    merchant_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Merchant name → transaction count"
    )
    # Category distribution
    category_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Category name → transaction count"
    )
    # Unique merchants count
    unique_merchants: int = Field(default=0)


class UserProfile(BaseModel):
    """
    Comprehensive behavioral profile for a user.
    
    This profile is built incrementally as transactions are processed.
    It enables personalized anomaly detection where the model learns
    what's "normal" specifically for this user.
    """
    # Identity
    user_id: str
    
    # Behavioral Patterns
    spending: SpendingStats = Field(default_factory=SpendingStats)
    time_patterns: TimePatterns = Field(default_factory=TimePatterns)
    velocity: VelocityPatterns = Field(default_factory=VelocityPatterns)
    merchants: MerchantPatterns = Field(default_factory=MerchantPatterns)
    
    # Profile Maturity
    total_transactions: int = Field(default=0, description="Total transactions processed")
    is_mature: bool = Field(default=False, description="Has enough history for personalization")
    maturity_threshold: int = Field(default=20, description="Transactions needed for maturity")
    
    # Timestamps
    first_transaction_at: Optional[datetime] = None
    last_transaction_at: Optional[datetime] = None
    profile_created_at: datetime = Field(default_factory=datetime.now)
    profile_updated_at: datetime = Field(default_factory=datetime.now)
    
    # Recent amounts for percentile calculation (last 100)
    recent_amounts: list[float] = Field(
        default_factory=list,
        description="Recent transaction amounts for percentile calculation"
    )
    
    def update_with_transaction(
        self,
        amount: float,
        timestamp: datetime,
        merchant: Optional[str] = None,
        category: Optional[str] = None
    ) -> None:
        """
        Update the profile with a new transaction.
        
        This method incrementally updates all statistics using
        online algorithms to avoid storing full history.
        """
        self.total_transactions += 1
        now = timestamp
        
        # Update timestamps
        if self.first_transaction_at is None:
            self.first_transaction_at = now
        
        # Update velocity (time since last transaction)
        if self.last_transaction_at:
            gap = (now - self.last_transaction_at).total_seconds()
            # Exponential moving average for gap
            alpha = 0.1
            self.velocity.avg_gap_seconds = (
                alpha * gap + (1 - alpha) * self.velocity.avg_gap_seconds
            )
        
        self.last_transaction_at = now
        
        # Update spending stats (online algorithm)
        self._update_spending_stats(amount)
        
        # Update time patterns
        self._update_time_patterns(now)
        
        # Update merchant patterns
        if merchant:
            self.merchants.merchant_counts[merchant] = (
                self.merchants.merchant_counts.get(merchant, 0) + 1
            )
            self.merchants.unique_merchants = len(self.merchants.merchant_counts)
        
        if category:
            self.merchants.category_counts[category] = (
                self.merchants.category_counts.get(category, 0) + 1
            )
        
        # Check maturity
        self.is_mature = self.total_transactions >= self.maturity_threshold
        self.profile_updated_at = datetime.now()
    
    def _update_spending_stats(self, amount: float) -> None:
        """Update spending statistics using Welford's online algorithm."""
        n = self.total_transactions
        
        # Keep recent amounts for percentiles (max 100)
        self.recent_amounts.append(amount)
        if len(self.recent_amounts) > 100:
            self.recent_amounts.pop(0)
        
        # Update min/max
        if n == 1:
            self.spending.min_amount = amount
            self.spending.max_amount = amount
            self.spending.avg_amount = amount
            self.spending.std_amount = 0.0
        else:
            self.spending.min_amount = min(self.spending.min_amount, amount)
            self.spending.max_amount = max(self.spending.max_amount, amount)
            
            # Welford's online algorithm for mean and variance
            old_mean = self.spending.avg_amount
            self.spending.avg_amount = old_mean + (amount - old_mean) / n
            
            # Update variance (using online algorithm)
            if n > 1:
                old_std = self.spending.std_amount
                new_variance = (
                    (n - 2) / (n - 1) * (old_std ** 2) +
                    (amount - old_mean) ** 2 / n
                )
                self.spending.std_amount = max(1.0, np.sqrt(new_variance))
        
        # Update percentiles from recent amounts
        if len(self.recent_amounts) >= 10:
            sorted_amounts = sorted(self.recent_amounts)
            self.spending.median_amount = np.median(sorted_amounts)
            self.spending.p25_amount = np.percentile(sorted_amounts, 25)
            self.spending.p75_amount = np.percentile(sorted_amounts, 75)
            self.spending.p95_amount = np.percentile(sorted_amounts, 95)
    
    def _update_time_patterns(self, timestamp: datetime) -> None:
        """Update time-based patterns."""
        hour = timestamp.hour
        day = timestamp.weekday()
        
        # Update hour distribution (exponential smoothing)
        alpha = 0.05  # Slow adaptation
        for h in range(24):
            if h == hour:
                self.time_patterns.hour_distribution[h] = (
                    alpha * 1.0 + (1 - alpha) * self.time_patterns.hour_distribution[h]
                )
            else:
                self.time_patterns.hour_distribution[h] *= (1 - alpha)
        
        # Normalize
        total = sum(self.time_patterns.hour_distribution)
        if total > 0:
            self.time_patterns.hour_distribution = [
                h / total for h in self.time_patterns.hour_distribution
            ]
        
        # Update peak hours (hours with above-average activity)
        avg_prob = 1 / 24
        self.time_patterns.peak_hours = [
            h for h, prob in enumerate(self.time_patterns.hour_distribution)
            if prob > avg_prob * 0.8
        ]
        
        # Similar for days
        for d in range(7):
            if d == day:
                self.time_patterns.day_distribution[d] = (
                    alpha * 1.0 + (1 - alpha) * self.time_patterns.day_distribution[d]
                )
            else:
                self.time_patterns.day_distribution[d] *= (1 - alpha)
        
        # Normalize
        total = sum(self.time_patterns.day_distribution)
        if total > 0:
            self.time_patterns.day_distribution = [
                d / total for d in self.time_patterns.day_distribution
            ]
    
    def get_amount_zscore(self, amount: float) -> float:
        """Calculate z-score for an amount relative to user's history."""
        if self.spending.std_amount == 0 or self.spending.std_amount == 1.0:
            return 0.0
        return (amount - self.spending.avg_amount) / self.spending.std_amount
    
    def get_amount_percentile(self, amount: float) -> float:
        """Calculate what percentile this amount falls in (0-100)."""
        if not self.recent_amounts:
            return 50.0
        
        count_below = sum(1 for a in self.recent_amounts if a < amount)
        return (count_below / len(self.recent_amounts)) * 100
    
    def get_hour_probability(self, hour: int) -> float:
        """Get probability of user transacting at this hour."""
        if 0 <= hour < 24:
            return self.time_patterns.hour_distribution[hour]
        return 1 / 24
    
    def get_day_probability(self, day: int) -> float:
        """Get probability of user transacting on this day."""
        if 0 <= day < 7:
            return self.time_patterns.day_distribution[day]
        return 1 / 7
    
    def is_known_merchant(self, merchant: str) -> bool:
        """Check if user has transacted with this merchant before."""
        return merchant in self.merchants.merchant_counts
    
    def get_merchant_frequency(self, merchant: str) -> float:
        """Get how often user transacts with this merchant (0-1)."""
        if not self.merchants.merchant_counts:
            return 0.0
        count = self.merchants.merchant_counts.get(merchant, 0)
        total = sum(self.merchants.merchant_counts.values())
        return count / total if total > 0 else 0.0
    
    def to_redis_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_redis_dict(cls, data: dict) -> "UserProfile":
        """Create from Redis dictionary."""
        return cls.model_validate(data)


# Default profile for new users
def create_default_profile(user_id: str) -> UserProfile:
    """Create a default profile for a new user."""
    return UserProfile(
        user_id=user_id,
        spending=SpendingStats(
            avg_amount=50.0,  # Conservative default
            std_amount=30.0,
        ),
        time_patterns=TimePatterns(),
        velocity=VelocityPatterns(),
        merchants=MerchantPatterns(),
    )

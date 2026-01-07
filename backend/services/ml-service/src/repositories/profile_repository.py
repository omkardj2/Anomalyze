"""
Anomalyze ML Service - Profile Repository

Hybrid storage layer that uses:
- Redis: Hot cache for fast reads (real-time inference)
- PostgreSQL: Persistent storage (survives restarts, enables analytics)

Data Flow:
1. Read: Check Redis cache → If miss, load from Postgres → Cache in Redis
2. Write: Update Redis immediately → Async batch write to Postgres
"""
import asyncio
import json
from datetime import datetime
from typing import Optional
import structlog
import redis
import asyncpg
from contextlib import asynccontextmanager

from src.config import get_settings
from src.models.user_profile import UserProfile, create_default_profile

logger = structlog.get_logger()


class ProfileRepository:
    """
    Hybrid repository for user behavioral profiles.
    
    Uses Redis for real-time access and PostgreSQL for persistence.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._local_cache: dict[str, UserProfile] = {}
        
        # Write buffer for async Postgres updates
        self._write_buffer: dict[str, UserProfile] = {}
        self._write_task: Optional[asyncio.Task] = None
        
        # Config
        self._cache_ttl = 3600  # 1 hour Redis TTL
        self._flush_interval = 60  # Flush to Postgres every 60 seconds
    
    async def connect(self) -> bool:
        """Connect to both Redis and PostgreSQL."""
        redis_ok = self._connect_redis()
        pg_ok = await self._connect_postgres()
        
        # Start background flush task
        if pg_ok and self._write_task is None:
            self._write_task = asyncio.create_task(self._flush_loop())
        
        return redis_ok and pg_ok
    
    def _connect_redis(self) -> bool:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(
                self.settings.redis_url,
                decode_responses=True
            )
            self._redis.ping()
            logger.info("profile_repo_redis_connected")
            return True
        except Exception as e:
            logger.warning("profile_repo_redis_failed", error=str(e))
            return False
    
    async def _connect_postgres(self) -> bool:
        """Connect to PostgreSQL."""
        if not self.settings.database_url:
            logger.info("profile_repo_postgres_disabled", reason="No DATABASE_URL")
            return False
        
        try:
            self._pg_pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("profile_repo_postgres_connected")
            return True
        except Exception as e:
            logger.warning("profile_repo_postgres_failed", error=str(e))
            return False
    
    async def close(self) -> None:
        """Close connections and flush pending writes."""
        # Cancel flush task
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_to_postgres()
        
        # Close Postgres pool
        if self._pg_pool:
            await self._pg_pool.close()
        
        logger.info("profile_repo_closed")
    
    async def get_profile(self, user_id: str) -> UserProfile:
        """
        Get user profile with cache-through pattern.
        
        1. Check local cache
        2. Check Redis
        3. Load from PostgreSQL
        4. Create default if not found
        """
        # 1. Local cache (fastest)
        if user_id in self._local_cache:
            return self._local_cache[user_id]
        
        # 2. Redis cache
        profile = self._get_from_redis(user_id)
        if profile:
            self._local_cache[user_id] = profile
            return profile
        
        # 3. PostgreSQL (persistent)
        profile = await self._get_from_postgres(user_id)
        if profile:
            self._cache_profile(profile)
            return profile
        
        # 4. Create default
        profile = create_default_profile(user_id)
        self._local_cache[user_id] = profile
        return profile
    
    async def save_profile(self, profile: UserProfile, immediate_persist: bool = False) -> bool:
        """
        Save profile with write-behind pattern.
        
        Always updates Redis immediately.
        PostgreSQL updates are buffered and flushed periodically,
        unless immediate_persist=True.
        """
        # Update local cache
        self._local_cache[profile.user_id] = profile
        
        # Update Redis immediately
        self._save_to_redis(profile)
        
        # Queue for PostgreSQL
        self._write_buffer[profile.user_id] = profile
        
        # Immediate persist if requested (e.g., on maturity threshold)
        if immediate_persist and self._pg_pool:
            await self._persist_profile(profile)
        
        return True
    
    def _get_from_redis(self, user_id: str) -> Optional[UserProfile]:
        """Load profile from Redis cache."""
        if not self._redis:
            return None
        
        try:
            key = f"profile:{user_id}"
            data = self._redis.get(key)
            if data:
                return UserProfile.from_redis_dict(json.loads(data))
            return None
        except Exception as e:
            logger.warning("redis_get_failed", user_id=user_id, error=str(e))
            return None
    
    def _save_to_redis(self, profile: UserProfile) -> bool:
        """Save profile to Redis cache."""
        if not self._redis:
            return False
        
        try:
            key = f"profile:{profile.user_id}"
            data = json.dumps(profile.to_redis_dict())
            self._redis.setex(key, self._cache_ttl, data)
            return True
        except Exception as e:
            logger.warning("redis_save_failed", user_id=profile.user_id, error=str(e))
            return False
    
    async def _get_from_postgres(self, user_id: str) -> Optional[UserProfile]:
        """Load profile from PostgreSQL."""
        if not self._pg_pool:
            return None
        
        try:
            async with self._pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM user_behavior_profiles 
                    WHERE "userId" = $1
                    """,
                    user_id
                )
                
                if row:
                    return self._row_to_profile(row)
                return None
        except Exception as e:
            logger.warning("postgres_get_failed", user_id=user_id, error=str(e))
            return None
    
    async def _persist_profile(self, profile: UserProfile) -> bool:
        """Persist single profile to PostgreSQL."""
        if not self._pg_pool:
            return False
        
        try:
            async with self._pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_behavior_profiles (
                        id, "userId", 
                        "avgAmount", "stdAmount", "minAmount", "maxAmount", 
                        "medianAmount", "p95Amount",
                        "hourDistribution", "dayDistribution", 
                        "peakHours", "activeDays",
                        "avgDailyCount", "avg10minCount", "avgGapSeconds",
                        "merchantCounts", "uniqueMerchants",
                        "totalTransactions", "isMature", "maturityThreshold",
                        "recentAmounts",
                        "firstTransactionAt", "lastTransactionAt",
                        "createdAt", "updatedAt"
                    ) VALUES (
                        gen_random_uuid(), $1,
                        $2, $3, $4, $5, $6, $7,
                        $8, $9, $10, $11,
                        $12, $13, $14,
                        $15, $16,
                        $17, $18, $19,
                        $20,
                        $21, $22,
                        NOW(), NOW()
                    )
                    ON CONFLICT ("userId") DO UPDATE SET
                        "avgAmount" = EXCLUDED."avgAmount",
                        "stdAmount" = EXCLUDED."stdAmount",
                        "minAmount" = EXCLUDED."minAmount",
                        "maxAmount" = EXCLUDED."maxAmount",
                        "medianAmount" = EXCLUDED."medianAmount",
                        "p95Amount" = EXCLUDED."p95Amount",
                        "hourDistribution" = EXCLUDED."hourDistribution",
                        "dayDistribution" = EXCLUDED."dayDistribution",
                        "peakHours" = EXCLUDED."peakHours",
                        "activeDays" = EXCLUDED."activeDays",
                        "avgDailyCount" = EXCLUDED."avgDailyCount",
                        "avg10minCount" = EXCLUDED."avg10minCount",
                        "avgGapSeconds" = EXCLUDED."avgGapSeconds",
                        "merchantCounts" = EXCLUDED."merchantCounts",
                        "uniqueMerchants" = EXCLUDED."uniqueMerchants",
                        "totalTransactions" = EXCLUDED."totalTransactions",
                        "isMature" = EXCLUDED."isMature",
                        "recentAmounts" = EXCLUDED."recentAmounts",
                        "lastTransactionAt" = EXCLUDED."lastTransactionAt",
                        "updatedAt" = NOW()
                    """,
                    profile.user_id,
                    profile.spending.avg_amount,
                    profile.spending.std_amount,
                    profile.spending.min_amount,
                    profile.spending.max_amount,
                    profile.spending.median_amount,
                    profile.spending.p95_amount,
                    json.dumps(profile.time_patterns.hour_distribution),
                    json.dumps(profile.time_patterns.day_distribution),
                    profile.time_patterns.peak_hours,
                    profile.time_patterns.active_days,
                    profile.velocity.avg_daily_count,
                    profile.velocity.avg_10min_count,
                    profile.velocity.avg_gap_seconds,
                    json.dumps(profile.merchants.merchant_counts),
                    profile.merchants.unique_merchants,
                    profile.total_transactions,
                    profile.is_mature,
                    profile.maturity_threshold,
                    json.dumps(profile.recent_amounts),
                    profile.first_transaction_at,
                    profile.last_transaction_at,
                )
            return True
        except Exception as e:
            logger.error("postgres_persist_failed", user_id=profile.user_id, error=str(e))
            return False
    
    async def _flush_to_postgres(self) -> None:
        """Flush all buffered profiles to PostgreSQL."""
        if not self._write_buffer or not self._pg_pool:
            return
        
        profiles = list(self._write_buffer.values())
        self._write_buffer.clear()
        
        logger.info("flushing_profiles", count=len(profiles))
        
        for profile in profiles:
            await self._persist_profile(profile)
    
    async def _flush_loop(self) -> None:
        """Background task to periodically flush to PostgreSQL."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_to_postgres()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("flush_loop_error", error=str(e))
    
    def _row_to_profile(self, row: asyncpg.Record) -> UserProfile:
        """Convert PostgreSQL row to UserProfile."""
        from src.models.user_profile import (
            UserProfile, SpendingStats, TimePatterns, 
            VelocityPatterns, MerchantPatterns
        )
        
        return UserProfile(
            user_id=row["userId"],
            spending=SpendingStats(
                avg_amount=row["avgAmount"],
                std_amount=row["stdAmount"],
                min_amount=row["minAmount"],
                max_amount=row["maxAmount"],
                median_amount=row["medianAmount"],
                p95_amount=row["p95Amount"],
            ),
            time_patterns=TimePatterns(
                hour_distribution=json.loads(row["hourDistribution"]) if row["hourDistribution"] else [1/24]*24,
                day_distribution=json.loads(row["dayDistribution"]) if row["dayDistribution"] else [1/7]*7,
                peak_hours=list(row["peakHours"]) if row["peakHours"] else list(range(9, 21)),
                active_days=list(row["activeDays"]) if row["activeDays"] else list(range(5)),
            ),
            velocity=VelocityPatterns(
                avg_daily_count=row["avgDailyCount"],
                avg_10min_count=row["avg10minCount"],
                avg_gap_seconds=row["avgGapSeconds"],
            ),
            merchants=MerchantPatterns(
                merchant_counts=json.loads(row["merchantCounts"]) if row["merchantCounts"] else {},
                unique_merchants=row["uniqueMerchants"],
            ),
            total_transactions=row["totalTransactions"],
            is_mature=row["isMature"],
            maturity_threshold=row["maturityThreshold"],
            recent_amounts=json.loads(row["recentAmounts"]) if row["recentAmounts"] else [],
            first_transaction_at=row["firstTransactionAt"],
            last_transaction_at=row["lastTransactionAt"],
            profile_created_at=row["createdAt"],
            profile_updated_at=row["updatedAt"],
        )
    
    @property
    def is_redis_connected(self) -> bool:
        if not self._redis:
            return False
        try:
            self._redis.ping()
            return True
        except:
            return False
    
    @property
    def is_postgres_connected(self) -> bool:
        return self._pg_pool is not None


# Global instance
_profile_repo: Optional[ProfileRepository] = None


def get_profile_repository() -> ProfileRepository:
    """Get the global profile repository instance."""
    global _profile_repo
    if _profile_repo is None:
        _profile_repo = ProfileRepository()
    return _profile_repo

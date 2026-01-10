
import Redis from 'ioredis';
import dotenv from 'dotenv';

dotenv.config();

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const DEDUP_TTL_SECONDS = 3600; // 1 hour

export let redis: Redis | null = null;

try {
    redis = new Redis(REDIS_URL, {
        maxRetriesPerRequest: 3,
        retryStrategy(times) {
            if (times > 3) return null; // stop retrying
            return Math.min(times * 50, 2000);
        },
    });

    redis.on('error', (err) => {
        console.error('❌ Redis Client Error:', err.message);
    });

    redis.on('connect', () => {
        console.log(`✅ Redis connected for deduplication: ${REDIS_URL}`);
    });
} catch (error) {
    console.error('❌ Failed to initialize Redis:', error);
}

/**
 * Checks if an alert should be sent or suppressed.
 * Uses SETNX to acquire a lock on the alert ID.
 * 
 * @param userId - The user ID
 * @param txId - The transaction ID causing the anomaly
 * @returns true if alert should be sent, false if it's a duplicate
 */
export const shouldSendAlert = async (userId: string, txId: string): Promise<boolean> => {
    if (!redis || redis.status !== 'ready') {
        console.warn('⚠️ Redis not available. Skipping deduplication (Allowing alert).');
        return true; // Fail open: send alert if Redis is down
    }

    const key = `alert:${userId}:${txId}`;

    try {
        // SETNX key value EX ttl
        // Returns 'OK' if set, null if already exists (noreply) or 0/1 depending on client
        // ioredis set with NX returns 'OK' if set, null otherwise
        const result = await redis.set(key, 'sent', 'EX', DEDUP_TTL_SECONDS, 'NX');

        if (result === 'OK') {
            return true; // New alert, lock acquired
        } else {
            console.log(`🔒 Duplicate alert suppressed for user ${userId}, tx ${txId}`);
            return false; // Already exists
        }
    } catch (error) {
        console.error('❌ Deduplication check failed:', error);
        return true; // Fail open
    }
};

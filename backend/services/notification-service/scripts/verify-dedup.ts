
import { shouldSendAlert, redis as serviceRedis } from '../src/services/deduplication.service';
import Redis from 'ioredis';
import dotenv from 'dotenv';

dotenv.config();

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const redis = new Redis(REDIS_URL); // Verification client

async function main() {
    const userId = 'test_user_' + Date.now();
    const txId1 = 'tx_1';
    const txId2 = 'tx_2';

    console.log('🧪 Starting Deduplication Test...');

    // Wait for service Redis to connect
    if (serviceRedis) {
        console.log('Waiting for Service Redis connection...');
        let retries = 0;
        while (serviceRedis.status !== 'ready' && retries < 20) {
            await new Promise(r => setTimeout(r, 200));
            retries++;
        }
        if (serviceRedis.status !== 'ready') {
            console.error('❌ Service Redis failed to connect (timeout)');
            process.exit(1);
        }
        console.log('✅ Service Redis Connected!');
    }

    try {
        // 1. First Alert (Should Pass)
        console.log(`\nAttempt 1 (User: ${userId}, Tx: ${txId1})`);
        const sent1 = await shouldSendAlert(userId, txId1);
        console.log(`Result: ${sent1} (Expected: true)`);
        if (!sent1) throw new Error('First alert failed');

        // 2. Duplicate Alert (Should Fail)
        console.log(`\nAttempt 2 (User: ${userId}, Tx: ${txId1}) - DUPLICATE`);
        const sent2 = await shouldSendAlert(userId, txId1);
        console.log(`Result: ${sent2} (Expected: false)`);
        if (sent2) throw new Error('Duplicate alert passed (should have been blocked)');

        // 3. Different Transaction (Should Pass)
        console.log(`\nAttempt 3 (User: ${userId}, Tx: ${txId2}) - NEW TRANSACTION`);
        const sent3 = await shouldSendAlert(userId, txId2);
        console.log(`Result: ${sent3} (Expected: true)`);
        if (!sent3) throw new Error('New transaction failed');

        console.log('\n✅ DEDUPLICATION LOGIC VERIFIED!');
    } catch (err) {
        console.error('\n❌ TEST FAILED:', err);
        process.exit(1);
    } finally {
        redis.disconnect(); // Cleanup test connection
        if (serviceRedis) serviceRedis.disconnect(); // Cleanup service connection
        process.exit(0);
    }
}

main();

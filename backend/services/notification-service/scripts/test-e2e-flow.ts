/**
 * ============================================================
 * End-to-End Flow Test - Notification Service
 * ============================================================
 * 
 * This script tests the COMPLETE notification flow:
 * 1. Creates a test user in the database (PRO tier)
 * 2. Produces an anomaly event to Kafka
 * 3. The running service should:
 *    - Receive the event
 *    - Fetch user from DB
 *    - Send email to user's email address
 * 
 * ============================================================
 * PREREQUISITES
 * ============================================================
 * 
 * Option A: Docker Setup (Recommended)
 * ------------------------------------------------------------
 * # 1. Start all infrastructure:
 * cd /path/to/Anomalyze/backend
 * docker compose up -d redis redpanda postgres
 * 
 * # 2. Setup database:
 * cd services/notification-service
 * npx prisma generate
 * npx prisma db push
 * 
 * # 3. Start the notification service (in Terminal 1):
 * npm run dev
 * 
 * # 4. Run this test (in Terminal 2):
 * npx ts-node -r dotenv/config scripts/test-e2e-flow.ts your@email.com
 * 
 * 
 * Option B: Local Infrastructure
 * ------------------------------------------------------------
 * If you have Redis, Kafka, and Postgres running locally:
 * 
 * # 1. Ensure .env has correct DATABASE_URL, REDIS_URL, KAFKA_BOOTSTRAP_SERVERS
 * 
 * # 2. Setup database:
 * npx prisma generate
 * DATABASE_URL="postgresql://user:pass@localhost:5432/dbname" npx prisma db push
 * 
 * # 3. Start service (Terminal 1):
 * npm run dev
 * 
 * # 4. Run this test (Terminal 2):
 * DATABASE_URL="postgresql://user:pass@localhost:5432/dbname" npx ts-node -r dotenv/config scripts/test-e2e-flow.ts your@email.com
 * 
 * ============================================================
 * USAGE
 * ============================================================
 * 
 * npx ts-node -r dotenv/config scripts/test-e2e-flow.ts [email]
 * 
 * Examples:
 *   npx ts-node -r dotenv/config scripts/test-e2e-flow.ts
 *   npx ts-node -r dotenv/config scripts/test-e2e-flow.ts myemail@gmail.com
 * 
 * ============================================================
 */

import { Kafka } from 'kafkajs';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const KAFKA_BROKERS = process.env.KAFKA_BOOTSTRAP_SERVERS?.split(',') || ['localhost:9092'];
const KAFKA_TOPIC = process.env.KAFKA_ANOMALIES_TOPIC || 'anomalies';

// Test user config - UPDATE THIS EMAIL TO RECEIVE THE TEST!
const TEST_USER_ID = `user_e2e_test_${Date.now()}`;
const TEST_USER_EMAIL = process.argv[2] || 'aryangore.pict@gmail.com';

async function main() {
    console.log('🧪 Starting End-to-End Flow Test\n');
    console.log(`📧 Test email will be sent to: ${TEST_USER_EMAIL}\n`);

    // Step 1: Create test user in database
    console.log('Step 1: Creating test user in database...');
    try {
        const user = await prisma.user.create({
            data: {
                id: TEST_USER_ID,
                email: TEST_USER_EMAIL,
                name: 'E2E Test User',
                subscription: {
                    create: {
                        plan: 'PRO',
                        status: 'ACTIVE',
                        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
                        features: { sms: true, voice: true },
                    },
                },
                notificationSettings: {
                    create: {
                        emailEnabled: true,
                        phoneEnabled: true,
                        phoneNumber: '+1234567890',
                    },
                },
            },
            include: {
                subscription: true,
                notificationSettings: true,
            },
        });
        console.log(`   ✅ Created user: ${user.id}`);
        console.log(`   📧 Email: ${user.email}`);
        console.log(`   💳 Plan: ${user.subscription?.plan}`);
    } catch (err: any) {
        console.error('   ❌ Failed to create user:', err.message);
        process.exit(1);
    }

    // Step 2: Connect to Kafka
    console.log('\nStep 2: Connecting to Kafka...');
    const kafka = new Kafka({
        clientId: 'e2e-test-producer',
        brokers: KAFKA_BROKERS,
    });
    const producer = kafka.producer();
    await producer.connect();
    console.log('   ✅ Connected to Kafka');

    // Step 3: Produce anomaly event
    console.log('\nStep 3: Producing anomaly event...');
    const event = {
        userId: TEST_USER_ID,
        txId: `tx_e2e_${Date.now()}`,
        severity: 'CRITICAL',
        timestamp: new Date().toISOString(),
        details: 'E2E Test: This is a real test anomaly that should trigger an email!',
        data: {
            amount: 9999.99,
            location: 'Test Location',
        },
    };

    await producer.send({
        topic: KAFKA_TOPIC,
        messages: [{ key: TEST_USER_ID, value: JSON.stringify(event) }],
    });
    console.log('   ✅ Event sent to Kafka');
    console.log(`   📢 Event: ${JSON.stringify(event, null, 2)}`);

    await producer.disconnect();

    // Step 4: Wait and cleanup
    console.log('\n⏳ Waiting 5 seconds for service to process...\n');
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Cleanup: Delete test user
    console.log('Step 4: Cleaning up test user...');
    await prisma.user.delete({ where: { id: TEST_USER_ID } });
    console.log('   ✅ Test user deleted');

    await prisma.$disconnect();

    console.log('\n' + '='.repeat(50));
    console.log('✅ E2E TEST COMPLETE!');
    console.log('='.repeat(50));
    console.log(`\nCheck your email (${TEST_USER_EMAIL}) for the anomaly notification!`);
    console.log('Also check the running service logs for processing details.\n');
}

main().catch(async (err) => {
    console.error('❌ E2E Test Failed:', err);
    await prisma.$disconnect();
    process.exit(1);
});

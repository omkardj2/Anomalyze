
import { Kafka } from 'kafkajs';
import dotenv from 'dotenv';

dotenv.config();

const KAFKA_BROKERS = process.env.KAFKA_BOOTSTRAP_SERVERS?.split(',') || ['localhost:9092'];
const KAFKA_TOPIC = process.env.KAFKA_ANOMALIES_TOPIC || 'anomalies';

const kafka = new Kafka({
    clientId: 'test-producer',
    brokers: KAFKA_BROKERS,
});

const producer = kafka.producer();

async function main() {
    await producer.connect();
    console.log('✅ Connected to Kafka');

    const payload = {
        userId: 'user_test_e2e',
        txId: `tx_${Date.now()}`,
        severity: 'CRITICAL',
        email: 'test@example.com', // Log only
        // phone: '+1234567890', // Uncomment to test SMS (if creds exist)
        timestamp: new Date().toISOString(),
        details: 'This is an end-to-end test anomaly.'
    };

    await producer.send({
        topic: KAFKA_TOPIC,
        messages: [
            { value: JSON.stringify(payload) },
        ],
    });

    console.log('📢 Sent event:', payload);
    await producer.disconnect();
}

main().catch(console.error);

// src/scripts/produce-anomaly.ts
import { Kafka } from 'kafkajs';
import dotenv from 'dotenv';

dotenv.config();

const KAFKA_BROKERS = (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(',');
const KAFKA_TOPIC = process.env.KAFKA_ANOMALIES_TOPIC || 'anomalies';

const kafka = new Kafka({
  clientId: 'notification-producer',
  brokers: KAFKA_BROKERS,
});

const producer = kafka.producer();

async function produceTestAnomaly() {
  await producer.connect();

  const message = {
    userId: 'user_123',
    email: 'user@example.com',
    phone: '+919999999999',
    webhookUrl: 'https://webhook.site/5e12a939-1c32-44e9-850d-4393ed9f771e', // replace with your URL
    severity: 'CRITICAL',
    details: 'This is a test anomaly event',
    timestamp: new Date().toISOString(),
  };

  await producer.send({
    topic: KAFKA_TOPIC,
    messages: [
      { value: JSON.stringify(message) },
    ],
  });

  console.log('✅ Test anomaly produced:', message);

  await producer.disconnect();
}

produceTestAnomaly().catch(err => {
  console.error('❌ Failed to produce test anomaly:', err);
  process.exit(1);
});

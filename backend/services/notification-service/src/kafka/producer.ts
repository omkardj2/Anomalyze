// src/kafka/producer.ts
import { Kafka } from 'kafkajs';

const KAFKA_BROKERS =
  process.env.KAFKA_BOOTSTRAP_SERVERS?.split(',') || ['localhost:9092'];

const ALERTS_TOPIC =
  process.env.KAFKA_ALERTS_TOPIC || 'alerts';

const kafka = new Kafka({
  clientId: 'notification-service-producer',
  brokers: KAFKA_BROKERS,
});

const producer = kafka.producer();

export const startKafkaProducer = async () => {
  await producer.connect();
  console.log(`✅ Kafka producer connected (topic: ${ALERTS_TOPIC})`);
};

export const produceAlertEvent = async (alertEvent: {
  alertId: string;
  userId: string;
  severity: string;
  channels: {
    email: boolean;
    sms: boolean;
    webhook: boolean;
    call: boolean;
  };
  sourceEvent: any;
  timestamp: string;
}) => {
  await producer.send({
    topic: ALERTS_TOPIC,
    messages: [
      {
        key: alertEvent.userId,
        value: JSON.stringify(alertEvent),
      },
    ],
  });

  console.log(`📤 Alert event produced for user: ${alertEvent.userId}`);
};

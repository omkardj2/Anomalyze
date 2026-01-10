import { Kafka } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'alerts-consumer-test',
  brokers: ['localhost:9092'],
});

const consumer = kafka.consumer({ groupId: 'alerts-test-group' });

async function main() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'alerts', fromBeginning: true });

  console.log('👂 Listening to alerts topic...');

  await consumer.run({
    eachMessage: async ({ message }) => {
      console.log(
        '📥 ALERT EVENT RECEIVED:',
        JSON.parse(message.value!.toString())
      );
    },
  });
}

main();

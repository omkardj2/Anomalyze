
import app from '../src/app';
import { startKafkaConsumer } from '../src/kafka/consumer';

// Start consumer
startKafkaConsumer().catch(console.error);

// Keep alive for 15 seconds then exit
console.log('⏳ Running service for 15 seconds to process events...');
setTimeout(() => {
    console.log('🛑 Timeout reached. Exiting.');
    process.exit(0);
}, 15000);

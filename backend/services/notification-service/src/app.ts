import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { z } from 'zod';
import swaggerUi from 'swagger-ui-express';
import swaggerJsdoc from 'swagger-jsdoc';

import routes from './api/routes';
import { startKafkaConsumer } from './kafka/consumer';

// 1. Load Environment Variables
dotenv.config();

// 2. Validate Environment Variables
const envSchema = z.object({
    PORT: z.string().default('3001'),
    SERVICE_NAME: z.string().default('notification-service'),
    KAFKA_BOOTSTRAP_SERVERS: z.string().min(1, "KAFKA_BOOTSTRAP_SERVERS is required"),
    REDIS_URL: z.string().optional().default('redis://localhost:6379'),
    SMTP_HOST: z.string().optional(),
    TWILIO_ACCOUNT_SID: z.string().optional(),
});

try {
    envSchema.parse(process.env);
} catch (error) {
    if (error instanceof z.ZodError) {
        console.error('Invalid Environment Variables:', error.errors.map(e => `${e.path}: ${e.message}`).join(', '));
        process.exit(1);
    }
}

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Swagger
const swaggerOptions = {
    definition: {
        openapi: '3.0.0',
        info: { title: 'Notification Service API', version: '1.0.0' },
    },
    apis: ['./src/api/*.ts'],
};
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Health Check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: process.env.SERVICE_NAME });
});



// Start Server (Conditional)
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`✅ ${process.env.SERVICE_NAME} running on port ${PORT}`);
    });
}


if (process.env.ENABLE_KAFKA === 'true') {
    startKafkaConsumer().catch(err => {
        console.error('❌ Kafka consumer failed to start:', err);
    });
} else {
    console.log('⚠️ Kafka consumer disabled (ENABLE_KAFKA=false)');
}

app.use('/api', routes);


export default app;

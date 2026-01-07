import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { z } from 'zod';
import router from './api/routes';
import swaggerUi from 'swagger-ui-express';
import swaggerJsdoc from 'swagger-jsdoc';

// 1. Load Environment Variables
dotenv.config();

// 2. Validate Environment Variables
const envSchema = z.object({
    PORT: z.string().default('3000'),
    SERVICE_NAME: z.string().default('ingestion-service'),
    KAFKA_BOOTSTRAP_SERVERS: z.string().min(1, "KAFKA_BOOTSTRAP_SERVERS is required"),
    DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),
    REDIS_URL: z.string().min(1, "REDIS_URL is required"),
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
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Swagger
const swaggerOptions = {
    definition: {
        openapi: '3.0.0',
        info: { title: 'Ingestion Service API', version: '1.0.0' },
    },
    apis: ['./src/api/*.ts'],
};
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Routes
app.use('/v1', router);

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

export default app;

"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const zod_1 = require("zod");
const swagger_ui_express_1 = __importDefault(require("swagger-ui-express"));
const swagger_jsdoc_1 = __importDefault(require("swagger-jsdoc"));
const db_1 = require("./config/db");
const user_sync_1 = require("./webhooks/user.sync");
const auth_middleware_1 = require("./middleware/auth.middleware");
const user_controller_1 = require("./controllers/user.controller");
// 1. Load Environment Variables
dotenv_1.default.config();
// 2. Validate Environment Variables
const envSchema = zod_1.z.object({
    PORT: zod_1.z.string().default('3002'),
    SERVICE_NAME: zod_1.z.string().default('auth-service'),
    // CLERK_PUBLISHABLE_KEY: z.string().min(1, "CLERK_PUBLISHABLE_KEY is required"),
    // CLERK_SECRET_KEY: z.string().min(1, "CLERK_SECRET_KEY is required"),
    // DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),
});
try {
    envSchema.parse(process.env);
}
catch (error) {
    if (error instanceof zod_1.z.ZodError) {
        console.error('Invalid Environment Variables:', error.errors.map(e => `${e.path}: ${e.message}`).join(', '));
        process.exit(1);
    }
}
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3002;
app.use((0, cors_1.default)());
app.use(express_1.default.json());
// Swagger
const swaggerOptions = {
    definition: {
        openapi: '3.0.0',
        info: { title: 'Auth Service API', version: '1.0.0' },
    },
    apis: ['./src/api/*.ts'],
};
const swaggerSpec = (0, swagger_jsdoc_1.default)(swaggerOptions);
app.use('/docs', swagger_ui_express_1.default.serve, swagger_ui_express_1.default.setup(swaggerSpec));
// Routes
// Webhook for Clerk (Public)
app.post('/webhooks/clerk', user_sync_1.handleClerkWebhook);
// Protected Routes
app.get('/v1/me', auth_middleware_1.requireAuth, user_controller_1.getMe);
// Health Check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: process.env.SERVICE_NAME });
});
// Start Server (Conditional)
if (require.main === module) {
    (0, db_1.connectDB)().then(() => {
        app.listen(PORT, () => {
            console.log(`✅ ${process.env.SERVICE_NAME} running on port ${PORT}`);
        });
    });
}
exports.default = app;

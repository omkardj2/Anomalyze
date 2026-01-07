# Notification Service (`notification-service`)

## 📖 Overview
The **Notification Service** is a Node.js microservice responsible for delivering real-time alerts to users via multiple channels (Email, SMS, Webhooks) when anomalies are detected.

It consumes the `anomalies` Kafka topic and routes alerts based on user preferences.

## 🏗 Architecture
- **Language**: TypeScript (Node.js 20+)
- **Framework**: Express.js (Management API)
- **Message Broker**: Kafka (Consumer)
- **Email**: Nodemailer (SMTP)
- **SMS**: Twilio
- **Templates**: Handlebars

### Data Flow
```
┌─────────────┐    ┌───────────────────────────────────┐
│ Kafka Topic │───►│       Notification Service        │
│ "anomalies" │    └────────────────┬──────────────────┘
└─────────────┘                     │
                                    │
                  ┌─────────────────┼──────────────────┐
                  │                 │                  │
           ┌──────▼──────┐   ┌──────▼──────┐    ┌──────▼──────┐
           │    Email    │   │     SMS     │    │   Webhook   │
           │    (SMTP)   │   │   (Twilio)  │    │   (POST)    │
           └─────────────┘   └─────────────┘    └─────────────┘
```

## 📁 Project Structure
```
notification-service/
├── src/
│   ├── app.ts            # Express app setup
│   ├── config.ts         # Environment config
│   ├── api/              # Management API (preferences)
│   │   └── routes.ts
│   ├── kafka/
│   │   └── consumer.ts   # Anomaly event consumer
│   ├── services/
│   │   ├── email.service.ts
│   │   └── sms.service.ts
│   └── templates/        # Email/SMS templates
├── .env.example          # Environment template
├── Dockerfile
├── package.json
└── README.md
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd backend/services/notification-service
cp .env.example .env
npm install
```

### 2. Configure Environment
**CRITICAL**: You must set up the `.env` file.
```bash
cp .env.example .env
```
Required for emails: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`.
Required for SMS: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`.
**If missing, the service will start but LOG errors when trying to send.**

### 3. Run with Docker (Recommended)
This service is part of the master compose.
```bash
cd ../..
docker compose up -d notification-service
```

## 🩺 Monitoring & Troubleshooting

### Health Check
```bash
curl http://localhost:3001/health
```

### Common Errors
1.  **Error**: `ConnectTimeoutError` (Redis)
    *   **Fix**: Ensure Redis is running. If in Docker, `REDIS_URL` must be `redis://redis:6379`.
2.  **Error**: `Auth failed` (SMTP)
    *   **Fix**: Verify your Google App Password or SMTP credentials in `.env`.
```bash
# Development mode
npm run dev

# Production build
npm run build
npm start
```

---

## 🔌 API Reference

### Health Check
**GET** `/health`

### Test Notification
**POST** `/v1/notifications/test`
```json
{
  "userId": "user_123",
  "channel": "EMAIL",
  "message": "This is a test alert"
}
```

---

## 🔧 Environment Variables

See `.env.example` for full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker | localhost:9092 |
| `SMTP_HOST` | Email server host | - |
| `TWILIO_ACCOUNT_SID` | Twilio ID for SMS | - |


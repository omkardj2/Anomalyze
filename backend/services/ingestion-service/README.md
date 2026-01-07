# Ingestion Service (`ingestion-service`)

## 📖 Overview
The **Ingestion Service** is a high-throughput Node.js microservice responsible for accepting financial transactions from external clients, validating them, and publishing them to the processing pipeline.

It supports:
1.  **Real-time API**: `POST /transactions` for single transaction ingress.
2.  **Batch Uploads**: CSV file upload for bulk processing.

## 🏗 Architecture
- **Language**: TypeScript (Node.js 20+)
- **Framework**: Express.js
- **Validation**: Zod
- **Message Broker**: Kafka (Producer)
- **Database**: PostgreSQL (Store raw transactions)
- **Queue**: BullMQ (Redis) for batch file processing

### Data Flow
```
┌─────────────┐    ┌───────────────────────────────────┐
│ Client Apps │───►│         Ingestion Service         │
└─────────────┘    └────────────────┬──────────────────┘
                                    │
                  ┌─────────────────┼──────────────────┐
                  │                 │                  │
           ┌──────▼──────┐   ┌──────▼──────┐    ┌──────▼──────┐
           │    Kafka    │   │  PostgreSQL │    │ Redis Queue │
           │(Transactions)   │ (Raw Store) │    │ (Batch Jobs)│
           └─────────────┘   └─────────────┘    └─────────────┘
```

## 📁 Project Structure
```
ingestion-service/
├── src/
│   ├── app.ts            # Express app setup
│   ├── config.ts         # Environment config
│   ├── api/
│   │   ├── routes.ts     # API routes
│   │   ├── controllers.ts# Request handlers
│   │   └── validators.ts # Zod schemas
│   ├── kafka/
│   │   └── producer.ts   # Kafka producer wrapper
│   └── services/
│       ├── transaction.service.ts # Core logic
│       └── batch.service.ts       # File processing
├── .env.example          # Environment template
├── Dockerfile
├── package.json
└── README.md
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd backend/services/ingestion-service
cp .env.example .env
npm install
```

### 2. Configure Environment
**CRITICAL**: You must set up the `.env` file.
```bash
cp .env.example .env
```
Ensure `KAFKA_BOOTSTRAP_SERVERS`, `REDIS_URL`, and `DATABASE_URL` are set.
**Missing these will cause "Connection Refused" errors.**

### 3. Run with Docker (Recommended)
This service is part of the master compose.
```bash
cd ../..
docker compose up -d ingestion-service
```
*(This automatically handles Kafka/Redis networking)*

## 🩺 Monitoring & Troubleshooting

### Health Check
```bash
curl http://localhost:3000/health
# Returns: { "status": "ok", "timestamp": "..." }
```

### Common Errors
1.  **Error**: `KafkaJSConnectionError: Connection refused`
    *   **Fix**: Ensure Redpanda is running (`docker compose up -d redpanda`) and `KAFKA_BOOTSTRAP_SERVERS` is correct.
2.  **Error**: `Error: P3000 ...` (Postgres)
    *   **Fix**: Check `DATABASE_URL`. Inside Docker, host is `postgres`. Local is `localhost`.
```bash
# Development mode
npm run dev

# Production build
npm run build
npm start
```

---

## 🔌 API Reference

### Transactions
**POST** `/v1/transactions`
```json
{
  "txId": "tx_123",
  "amount": 150.00,
  "currency": "USD",
  "userId": "user_abc",
  "merchant": "Amazon",
  "timestamp": "2023-10-27T10:00:00Z"
}
```

### Batch Upload
**POST** `/v1/transactions/batch`
- `multipart/form-data`
- File: `transactions.csv`

---

## 🔧 Environment Variables

See `.env.example` for full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker | localhost:9092 |
| `DATABASE_URL` | Postgres connection | postgres://... |
| `UPLOAD_DIR` | Temp storage for uploads | ./uploads |


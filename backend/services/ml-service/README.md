# ML Service (`ml-service`)

## 📖 Overview
The **ML Service** is a Python-based microservice responsible for detecting anomalies in financial transactions using **Isolation Forest** machine learning. It operates in two modes:

1. **Inference (Real-time)**: Consumes Kafka stream, extracts features, applies ML model, produces anomaly verdicts
2. **Training (Batch)**: Generates/loads training data, trains Isolation Forest, saves model artifacts

## 🏗 Architecture
- **Language**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **ML**: scikit-learn (Isolation Forest)
- **Message Broker**: Kafka (Redpanda for local dev)
- **Hot Feature Store**: Redis (velocity, user cache)
- **Persistent Store**: PostgreSQL (user profiles, transactions)
- **Model Storage**: Local filesystem (S3/R2 ready)

### Hybrid Storage Architecture
```
┌─────────────┐    ┌───────────────────────────────────┐
│ Transaction │───►│            ML Service             │
└─────────────┘    └────────────────┬──────────────────┘
                                    │
                  ┌─────────────────┴──────────────────┐
                  │                                    │
           ┌──────▼──────┐                      ┌──────▼──────┐
           │ Redis Cache │◄─── Cache Miss ──────│  PostgreSQL │
           │ (Hot Data)  │                      │ (Cold Data) │
           └─────────────┘                      └─────────────┘
           • 1ms Read Time                      • Persistent
           • User Velocity                      • User Profiles
           • 100% Availability                  • Transactions
```

## 📁 Project Structure
```
ml-service/
├── src/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Pydantic settings
│   ├── api/
│   │   ├── routes.py     # REST API endpoints
│   │   └── schemas.py    # Pydantic models
│   ├── kafka/
│   │   ├── consumer.py   # Transaction consumer
│   │   └── producer.py   # Anomaly producer
│   ├── ml/
│   │   ├── model.py      # Isolation Forest wrapper
│   │   ├── features.py   # Feature engineering (10 features)
│   │   ├── training.py   # Training pipeline
│   │   └── scheduler.py  # Daily auto-retraining
│   └── repositories/
│       └── profile_repository.py  # Hybrid Redis+PostgreSQL repo
├── models/               # Trained model files
├── data/                 # Local data storage
├── tests/                # Comprehensive tests
├── docker-compose.yml    # Local dev environment
├── Dockerfile
└── pyproject.toml
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd backend/services/ml-service

# Copy environment template
cp .env.example .env

# Install Python dependencies
pip install -e .
```

### 2. Start Local Services (Kafka + Redis + Postgres)
```bash
docker compose up -d redpanda redis redpanda-console postgres
```

### 3. Run the ML Service
```bash
# Development mode with hot reload
uvicorn src.main:app --reload --port 8000

# Or run directly
python -m src.main
```

### 4. Train Initial Model
```bash
# Trigger training via API
curl -X POST http://localhost:8000/v1/train \
  -H "Content-Type: application/json" \
  -d '{}'

# Check training status
curl http://localhost:8000/v1/train/<job_id>
```

### 5. Test Inference
```bash
curl -X POST http://localhost:8000/v1/inference \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "transaction": {
      "tx_id": "tx_test_001",
      "amount": 5000.00,
      "currency": "USD",
      "merchant": "Test Store"
    }
  }'
```

---

## 🔄 Complete Data Flow

### 1. Ingestion → ML Service (Real-Time)
```
┌─────────────┐    ┌─────────────────┐    ┌────────────────┐
│  Client App │───▶│ Ingestion Svc   │───▶│ Kafka          │
│  POST /tx   │    │ Validates &     │    │ `transactions` │
│             │    │ Publishes       │    │ topic          │
└─────────────┘    └─────────────────┘    └───────┬────────┘
                                                  │
                   ┌──────────────────────────────▼────────────────────┐
                   │                   ML Service                       │
                   │  ┌──────────┐    ┌──────────┐    ┌──────────────┐ │
                   │  │ Kafka    │───▶│ Feature  │───▶│ Isolation    │ │
                   │  │ Consumer │    │ Engineer │    │ Forest Model │ │
                   │  └──────────┘    │ (Redis)  │    └──────┬───────┘ │
                   │                  └──────────┘           │         │
                   │                                         ▼         │
                   │  ┌──────────────────────────────────────────┐     │
                   │  │ Verdict Generator                        │     │
                   │  │ - Severity: LOW/MEDIUM/HIGH/CRITICAL     │     │
                   │  │ - Explanation: "Amount 37x above avg..." │     │
                   │  └────────────────────┬─────────────────────┘     │
                   └───────────────────────┼───────────────────────────┘
                                           │
                   ┌───────────────────────▼───────────────────────────┐
                   │            Kafka `anomalies` topic                 │
                   └───────────────────────┬───────────────────────────┘
                                           │
       ┌───────────────────────────────────┼───────────────────────────┐
       │                                   │                           │
       ▼                                   ▼                           ▼
┌──────────────┐                  ┌──────────────┐            ┌──────────────┐
│ Dashboard    │                  │ Notification │            │ Database     │
│ (Real-time)  │                  │ Service      │            │ (Postgres)   │
└──────────────┘                  │ (Alerts)     │            │ Store for    │
                                  └──────────────┘            │ history      │
                                                              └──────────────┘
```

### 2. Scheduled Retraining Flow (Every 24h)
```
┌─────────────────┐
│  Daily Trigger  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      Count < 1000
│   Check Data    │───────────────────────► [ Skip Retrain ]
│     Volume      │
└────────┬────────┘
         │ Count >= 1000
         ▼
┌─────────────────┐      ┌───────────────┐
│ Fetch Last 7 Days│◄────┤  PostgreSQL   │
│   Transactions  │      │ (Transactions)│
└────────┬────────┘      └───────────────┘
         │
         ▼
┌─────────────────┐      ┌───────────────┐
│ Extract Features│◄────┤  PostgreSQL   │
│ (& User Profiles)│      │  (Profiles)   │
└────────┬────────┘      └───────────────┘
         │
         ▼
┌─────────────────┐
│   Train New     │
│ Isolation Forest│
└────────┬────────┘
         │
         ▼
┌─────────────────┐      Validation Fail
│ Validate Model  │───────────────────────► [ Keep Old Model ]
│ (Anomaly Rate)  │
└────────┬────────┘
         │ Validation Pass
         ▼
┌─────────────────┐
│ Save & Promote  │
│   New Version   │
└─────────────────┘
```

---

## 🧠 Feature Engineering (10 Features)

User-specific features stored in Redis/Postgres:

| Feature | Description | User-Specific? |
|---------|-------------|----------------|
| `log_amount` | Log-transformed amount | ❌ |
| `amount_zscore` | How many std from user's avg | ✅ |
| `amount_percentile` | Where in user's history | ✅ |
| `velocity_ratio` | Current / user's typical rate | ✅ |
| `hour_deviation` | Unusual hour for this user? | ✅ |
| `day_deviation` | Unusual day for this user? | ✅ |
| `time_since_last` | Seconds since last tx | ✅ |
| `merchant_familiarity` | Known merchant? | ✅ |
| `is_new_user` | < 20 transactions | ✅ |
| `global_amount_flag` | Globally unusual | ❌ |

---

## 🔌 API Reference

### Health Check
**GET** `/v1/health`

### Retraining Controls
**GET** `/v1/retrain/status` - Check next scheduled retrain  
**POST** `/v1/retrain/trigger` - Force manual retrain

### User Profiles
**GET** `/v1/users/{user_id}/profile` - Get behavioral profile
**DELETE** `/v1/users/{user_id}/profile` - Reset profile (testing)

### Inference
**POST** `/v1/inference` - Run inference with user context

---

## 📊 Ports & Services (Local Dev)

| Service | Port | URL |
|---------|------|-----|
| ML Service | 8000 | http://localhost:8000 |
| ML Service Docs | 8000 | http://localhost:8000/docs |
| Redpanda Console | 8080 | http://localhost:8080 |
| Kafka | 9092 | localhost:9092 |
| Redis | 6379 | localhost:6379 |

---

## 🔧 Environment Variables

See `.env.example` for all configuration options. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | localhost:9092 |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `DATABASE_URL` | PostgreSQL connection string | None (optional) |
| `MODEL_PATH` | Path to model file | ./models/current_model.pkl |
| `ANOMALY_THRESHOLD` | Score threshold for anomaly | 0.5 |

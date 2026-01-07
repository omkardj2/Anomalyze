# Anomalyze Backend

This directory contains the central infrastructure and microservices for the Anomalyze platform.

## 🏗 Architecture

The system consists of **6 Microservices** orchestrated via Kafka and Redis:

| Service | Port | Role | Technology |
|---------|------|------|------------|
| **Ingestion** | 3000 | Traffic Gate, Uploads | Node.js (Express) |
| **ML Service** | 8000 | Anomaly Detection | Python (FastAPI, Sklearn) |
| **Notification** | 3001 | Alerts (Email/SMS) | Node.js (Express) |
| **Auth** | 3002 | Identity (Clerk) | Node.js (Express) |
| **Analytics** | 3003 | Dashboard Stats | Node.js (Express) |
| **Subscription** | 3004 | Billing (Razorpay) | Node.js (Express) |

## 🚀 Running the Full Stack (Docker Compose)

The easiest way to run the complete system is using the master `docker-compose.yml` in this directory.

### Prerequisites
*   Docker & Docker Compose installed
*   Git

### Steps

1.  **Clone & Setup Environment**
    Ensure you are in the `backend` directory.

    **CRITICAL**: You must set up `.env` files for ALL services before starting.

    ```bash
    cd backend
    
    # 1. ML Service
    cp services/ml-service/.env.example services/ml-service/.env
    # 2. Ingestion
    cp services/ingestion-service/.env.example services/ingestion-service/.env
    # 3. Notification
    cp services/notification-service/.env.example services/notification-service/.env
    # 4. Auth
    cp services/auth-service/.env.example services/auth-service/.env
    # 5. Analytics
    cp services/analytics-service/.env.example services/analytics-service/.env
    # 6. Subscription
    cp services/subscription-service/.env.example services/subscription-service/.env
    ```

2.  **Start All Services**
    This command will build the images and start all infrastructure (Kafka, Redis, Postgres) and services.

    ```bash
    docker compose up -d --build
    ```

3.  **Verify Running Services**
    ```bash
    docker compose ps
    ```

## 🩺 Monitoring & Health Checks

You can check the health of any service using `curl` or a browser:

```bash
# ML Service
curl http://localhost:8000/v1/health

# Ingestion Service
curl http://localhost:3000/health

# Redpanda Console (Kafka UI)
open http://localhost:8080
```

### Viewing Logs
To see what's happening live (e.g., if a transaction was processed):

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for specific service
docker compose logs -f ml-service
docker compose logs -f ingestion-service
```

## ⚠️ Troubleshooting & Exceptions

### 1. "Connection Refused" / Crash Loop
**Cause**: Missing Environment Variables.
**Symptom**: `docker compose ps` shows services as `Exited (1)`.
**Fix**:
Check the logs to see exactly which variable is missing:
```bash
docker compose logs ml-service
```
*Expected Error*: `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings... Field required [type=missing, input_value={}, input_type=dict]`

**Solution**:
Open the `.env` file for that service (e.g., `services/ml-service/.env`) and ensure ALL required variables (especially `DATABASE_URL`, `REDIS_URL`, `KAFKA_BOOTSTRAP_SERVERS`) are uncommented and set.

### 2. Kafka Connection Failed
**Symptom**: Services keep restarting with `KafkaJSConnectionError`.
**Fix**:
Kafka (Redpanda) takes a few seconds to start. The services are configured to retry, but if they fail permanently:
```bash
docker compose restart ingestion-service
```

### 3. Database "User does not exist"
**Symptom**: Postgres connection errors.
**Fix**:
Ensure your `DATABASE_URL` matches the docker-compose credentials:
`postgresql://user:password@postgres:5432/anomalyze`

(Note: `postgres` is the hostname inside Docker, `localhost` is for your machine).

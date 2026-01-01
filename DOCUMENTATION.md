# Anomalyze – End-to-End System Documentation

## Overview

Anomalyze is a production-grade anomaly detection platform designed to handle **both batch and real-time transactional data** using a **hybrid Rules + Machine Learning approach**. The system is built on a **fully Event-Driven Architecture (EDA)** to ensure scalability, fault tolerance, and clean separation of concerns.

This document describes the **complete system architecture, data flow, storage model, detection logic, and cloud stack**, exactly as designed in the project specification.

---

## 1. High-Level Architectural Flow

The system follows an **Event-Driven Architecture (EDA)** where all services are decoupled and communicate through a central message bus.

- Frontend (Dashboard) and Backend (Processing) are independent
- Kafka (Confluent Cloud) acts as the backbone
- All ingestion paths converge into a single detection pipeline

This design allows:
- Horizontal scalability
- Independent service deployment
- Event replay and fault recovery

---

## 2. Detailed Technical Flow

### Phase 1: Identity & Entitlements (Steps 1–3)

**Goal:** Identify the user and determine allowed capabilities without hardcoding logic.

#### 1. Authentication
- Provider: Clerk / Auth0
- User signs up via frontend
- Receives a JWT containing:
  ```json
  { "sub": "user_123" }
  ```
- Token is attached to all API requests

#### 2. Entitlement Service (Gatekeeper)

- Database: Neon Postgres
- Table: `user_subscriptions`

Workflow:
1. User purchases a plan via Stripe
2. Stripe triggers `checkout.session.completed` webhook
3. Go backend updates subscription data in Neon

```sql
INSERT INTO user_subscriptions (user_id, plan, features, expiry)
VALUES ('user_123', 'ADVANCED', '{"realtime": true, "alerting": true}', '2026-01-01');
```

Frontend behavior:
- Dashboard calls `GET /v1/user/me`
- Backend joins Clerk user ID with Neon subscription table
- UI features are enabled/disabled dynamically

---

### Phase 2: Unified Ingestion Layer (Steps 4 & 8)

**Goal:** Treat batch and real-time data identically downstream.

#### Path A: Batch Ingestion (CSV)

1. User uploads CSV via API
2. Backend streams file to Cloudflare R2
3. Background goroutine reads file line-by-line
4. Each record is validated
5. Valid records published to Kafka topic `transactions`
6. API responds immediately with `202 Accepted`
7. UI receives progress updates via polling or WebSockets

#### Path B: Real-Time Ingestion (API)

1. Client sends `POST /transaction`
2. Backend checks entitlement via Upstash Redis
3. If invalid → `403 Forbidden`
4. Valid transactions are published to Kafka topic `transactions`

**Key Advantage:**  
The detection engine does not differentiate between batch or real-time data.

---

### Phase 3: Detection Engine (Step 5)

**Goal:** Apply hybrid detection logic in parallel.

#### Kafka Topic: `transactions`
All data flows through this topic.

#### 5.1 Enrichment & Rules Engine
- Technology: Python worker / Flink
- Maintains rolling 10-minute transaction window
- Fetches historical baselines from Redis
- Executes deterministic rules:
  - Velocity checks
  - Geo-fencing
  - Amount spike detection

Output:
```json
{ "rules_triggered": ["VELOCITY_HIGH"] }
```

#### 5.2 ML Inference Engine
- Python Kafka consumer
- Model: Isolation Forest
- Runtime: ONNX Runtime
- Outputs anomaly probability score

```json
{ "ml_score": 0.92 }
```

This step is asynchronous and non-blocking.

#### 5.3 Decision & Explainability Layer

- Aggregates rule outputs and ML scores
- Generates human-readable explanations

Example:
> "High velocity detected: 5th transaction in 5 minutes. Amount ($5000) is significantly above user average ($150)."

---

### Phase 4: Storage & Presentation (Steps 6–7)

#### Database: Neon Postgres

- `transactions` table → raw data
- `anomalies` table → detected anomalies with explanations
- Tables can be partitioned by date

Dashboard query:
```sql
SELECT *
FROM anomalies
WHERE user_id = 'user_123'
ORDER BY timestamp DESC;
```

#### Dashboard API
- Endpoint: `GET /v1/anomalies`
- Returns paginated anomaly data

---

### Phase 5: Action & Evolution (Steps 9–10)

#### Alerting Engine
- Kafka consumer on `anomalies` topic
- Applies severity and subscription filters
- Deduplicates alerts using Redis (`SETNX`)
- Sends alerts via email (SendGrid) or logs

#### Model Retraining Pipeline
- Weekly scheduled job
- Pulls recent data from Neon
- Retrains Isolation Forest model
- Exports new `.onnx` file
- Uploads to Cloudflare R2
- Services load updated model on restart

---

## 3. Kafka Event Schema

```json
{
  "meta": {
    "trace_id": "abc-123-xyz",
    "timestamp": "2025-12-20T12:00:00Z",
    "source": "REALTIME_API",
    "user_id": "user_99"
  },
  "data": {
    "tx_id": "tx_555",
    "amount": 4500.50,
    "currency": "USD",
    "location": "NY"
  },
  "enrichment": {
    "user_avg_spend": 120.00,
    "distance_from_last_tx": 5000
  },
  "analysis": {
    "rule_flags": ["GEO_IMPOSSIBLE", "AMOUNT_SPIKE"],
    "ml_score": 0.98,
    "ml_prediction": "ANOMALY"
  },
  "verdict": {
    "final_severity": "CRITICAL",
    "explanation": "Transaction amount is 37x higher than average."
  }
}
```

---

## 4. Cloud Stack Summary

- Authentication: Clerk
- Messaging: Confluent Cloud (Kafka)
- Cache: Upstash Redis
- Database: Neon Postgres
- Object Storage: Cloudflare R2
- Compute: Local / Render / Railway

---

## 5. Key Architectural Strengths

- Fully decoupled services
- Uniform ingestion model
- Explainable ML decisions
- Free-tier friendly cloud stack
- Easy extensibility for research and production

---

**Project Name:** Anomalyze  
**Author:** Aditya

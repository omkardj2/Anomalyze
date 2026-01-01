# Unified Ingestion Service (`ingestion-service`)

## Overview
The **Unified Ingestion Service** is the high-performance gateway for data entry. It is designed to handle bursty traffic patterns and provides robust validation before data ever reaches the processing pipeline. It supports both single-event real-time ingestion and bulk CSV processing.

## Architecture
- **Input**: REST API (JSON & Multipart)
- **Buffer**: Kafka (`transactions` topic)
- **Storage**: Cloudflare R2 (Batch files)
- **Validation**: Zod Schemas + Entitlement Checks (Redis)

## API Reference

### 1. Real-Time Ingestion

#### Ingest Single Transaction
The primary endpoint for real-time integration.
- **Endpoint**: `POST /v1/transactions`
- **Auth**: Bearer Token OR `x-api-key` header
- **Rate Limit**: Enforced per plan tier.

**Request Body**:
```json
{
  "tx_id": "tx_555",
  "amount": 4500.50,
  "currency": "USD",
  "timestamp": "2025-12-20T12:00:00Z",
  "merchant_id": "merch_123",
  "location": {
    "lat": 40.7128,
    "lon": -74.0060,
    "city": "New York"
  },
  "metadata": {
    "device_id": "dev_999"
  }
}
```

**Response**:
- `202 Accepted`: `{ "status": "queued", "trace_id": "abc-123" }`
- `400 Bad Request`: Validation error (e.g., missing fields).
- `429 Too Many Requests`: Rate limit exceeded.

### 2. Batch Processing

#### Upload Batch File
Upload a CSV file for asynchronous processing.
- **Endpoint**: `POST /v1/batches`
- **Content-Type**: `multipart/form-data`
- **File Requirements**: CSV format, max 50MB.

**Response**:
```json
{
  "job_id": "job_888",
  "status": "UPLOADED",
  "estimated_rows": 5000
}
```

#### Get Batch Job Status
Poll for the progress of a batch ingestion job.
- **Endpoint**: `GET /v1/batches/:jobId`

**Response**:
```json
{
  "id": "job_888",
  "status": "PROCESSING",
  "progress": {
    "total": 5000,
    "processed": 2500,
    "failed": 5
  },
  "errors_url": "https://r2.cloudflarestorage.com/.../errors.csv"
}
```

#### List Batch Jobs
History of uploads.
- **Endpoint**: `GET /v1/batches`
- **Query**: `?status=FAILED&limit=10`

### 3. System & Health

#### Health Check
Used by Kubernetes/Load Balancer.
- **Endpoint**: `GET /health`
- **Response**: `{ "status": "ok", "kafka": "connected", "redis": "connected" }`

#### Metrics
Prometheus metrics for monitoring.
- **Endpoint**: `GET /metrics`
- **Metrics**: `ingestion_requests_total`, `ingestion_latency_seconds`, `batch_jobs_active`.

## Validation Rules
The service enforces the following constraints:
1. `amount`: Must be positive.
2. `currency`: Must be a valid ISO 4217 code.
3. `timestamp`: Cannot be in the future.
4. `tx_id`: Must be unique per user (deduplication window: 24h).

# Unified Ingestion Service (`ingestion-service`)

## 📖 Overview
The **Ingestion Service** is the high-throughput gateway for all data. It enforces the **Tiered Ingestion Model**:
- **Basic Plan**: Only CSV Uploads allowed.
- **Pro Plan**: CSV Uploads + **Real-time API** streaming.

It uses **Kafka** to buffer data, ensuring the API never blocks, even during traffic spikes.

## 🏗 Architecture
- **Buffer**: Kafka (`transactions` topic).
- **Storage**: Cloudflare R2 (for raw CSV retention).
- **Validation**: Zod Schemas.
- **Rate Limiting**: Redis-based sliding window.

## 🔌 API Reference

### 1. Real-Time Ingestion (Pro Only)
**Endpoint**: `POST /v1/ingest/live`
- **Headers**: `x-api-key: sk_live_...`
- **Body**:
  ```json
  {
    "tx_id": "tx_999",
    "amount": 5000,
    "currency": "INR",
    "timestamp": "2026-01-01T12:00:00Z",
    "merchant": "Amazon"
  }
  ```
- **Logic**:
    1.  **Validate API Key**: Call Auth Service (or check cache).
    2.  **Check Entitlement**: Is Plan == PRO? If not, return `403 Forbidden`.
    3.  **Push to Kafka**: Produce to `transactions` topic.
    4.  **Respond**: `202 Accepted`.

### 2. Batch Ingestion (All Plans)
**Endpoint**: `POST /v1/ingest/upload`
- **Content-Type**: `multipart/form-data` (CSV file).
- **Logic**:
    1.  **Stream to R2**: Upload file to `s3://raw-uploads/{user_id}/{file_id}.csv`.
    2.  **Queue Job**: Push job metadata to Kafka `batch-jobs` topic.
    3.  **Async Worker**:
        - Reads file from R2.
        - Validates row-by-row.
        - Produces valid rows to `transactions` Kafka topic.
        - Updates job status in DB.

### 3. Job Status
**Endpoint**: `GET /v1/ingest/jobs/:id`
- **Response**: `{ "status": "COMPLETED", "rows_processed": 10000, "errors": 0 }`

## 🚦 Rate Limiting
- **Basic**: 10 requests/min (API is blocked anyway, but for safety).
- **Pro**: 10,000 requests/min.
- **Implementation**: Redis `INCR` with expiry.

## 🔄 Data Flow
`Client` -> `Ingestion API` -> `Kafka (transactions)` -> `ML Service`
                                     |
                                     v
                               `Data Lake Archiver` (Saves to S3 for Training)

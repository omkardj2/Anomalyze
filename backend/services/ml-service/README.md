# ML Service (`ml-service`)

## 📖 Overview
The **ML Service** is a Python-based microservice responsible for detecting anomalies in financial transactions. It operates in two modes:
1.  **Inference (Real-time)**: Consumes Kafka stream, applies Isolation Forest model, produces verdicts.
2.  **Training (Batch)**: Pulls historical data from the Data Lake (S3/R2), retrains models, and versions artifacts.

## 🏗 Architecture
- **Language**: Python 3.11+
- **Libraries**: `scikit-learn`, `pandas`, `fastapi`, `confluent-kafka`.
- **Data Lake**: S3/R2 (Parquet files) - **NOT** Postgres.
- **Model Store**: S3/R2 (Versioned `.pkl` or `.onnx` files).

## 🔌 API Reference (Management)

### 1. Training Pipeline
#### Trigger Retraining
**Endpoint**: `POST /v1/train`
- **Auth**: Admin Key.
- **Body**:
  ```json
  {
    "user_id": "user_123", // Optional: Train specific user model
    "date_range": { "start": "2025-01-01", "end": "2025-12-31" }
  }
  ```
- **Process**:
    1.  Fetch Parquet datasets from S3 Data Lake.
    2.  Preprocess (One-hot encoding, scaling).
    3.  Train `IsolationForest`.
    4.  Evaluate against holdout set.
    5.  Serialize & Upload to S3 (`models/v2.pkl`).
    6.  Update `current_model_version` in DB/Redis.

#### Get Training Status
**Endpoint**: `GET /v1/train/:job_id`

### 2. Model Management
#### List Models
**Endpoint**: `GET /v1/models`
- **Response**: `[{ "version": "v1.2", "accuracy": 0.95, "active": true }]`

#### Promote Model
**Endpoint**: `POST /v1/models/:version/promote`
- **Description**: Hot-swaps the active model used by the inference consumer.

## 🧠 Inference Pipeline (Kafka Consumer)
**Topic**: `transactions`
**Logic**:
1.  **Deserialize**: Read JSON transaction.
2.  **Feature Engineering**:
    - Calculate rolling window stats (Velocity, Avg Amount) using Redis.
    - *Note*: State is kept in Redis, not local memory, for stateless scaling.
3.  **Predict**: `model.predict(features)`.
4.  **Verdict**:
    - If `score < threshold`: **ANOMALY**.
5.  **Publish**: Send to `anomalies` topic.

## 💾 Data Lake Strategy
- **Raw Data**: Ingestion service dumps raw CSVs/JSONs to `s3://anomalyze-datalake/raw/`.
- **Processed Data**: ETL jobs convert raw data to partitioned Parquet `s3://anomalyze-datalake/processed/yyyy/mm/dd/`.
- **Why?**: Postgres locks up during heavy training reads. S3 + Parquet is faster, cheaper, and scalable for ML workloads.

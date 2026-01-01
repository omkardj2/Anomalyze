# Analytics & Reporting Service (`analytics-service`)

## Overview
The **Analytics & Reporting Service** is the user-facing backend for the Anomalyze Dashboard. It provides rich querying capabilities over the anomaly dataset, generates statistical aggregations, and manages the feedback loop that improves model accuracy over time.

## Architecture
- **Database**: Neon Postgres (Read-heavy)
- **Cache**: Redis (Dashboard counters)
- **Alerting**: SendGrid / Webhook Dispatcher

## API Reference

### 1. Anomaly Explorer

#### List Anomalies (Search)
Advanced filtering for the dashboard grid.
- **Endpoint**: `GET /v1/anomalies`
- **Query Params**:
  - `page`, `limit`
  - `severity`: `HIGH,CRITICAL`
  - `start_date`, `end_date`
  - `status`: `NEW`, `REVIEWED`, `RESOLVED`
  - `search`: "tx_555"

#### Get Anomaly Details
- **Endpoint**: `GET /v1/anomalies/:id`

#### Update Anomaly Status
Workflow management for analysts.
- **Endpoint**: `PATCH /v1/anomalies/:id`
- **Body**: `{ "status": "RESOLVED", "notes": "Customer confirmed valid." }`

### 2. Feedback Loop (Model Training)

#### Submit Feedback
Crucial for Active Learning. Marks an anomaly as True Positive or False Positive.
- **Endpoint**: `POST /v1/anomalies/:id/feedback`
- **Body**:
  ```json
  {
    "verdict": "FALSE_POSITIVE",
    "reason": "Holiday shopping pattern"
  }
  ```
- **Effect**: Updates the database and tags the record for the next retraining batch.

### 3. Dashboard Statistics

#### Get Summary Metrics
Returns high-level cards for the dashboard.
- **Endpoint**: `GET /v1/stats/summary`
- **Query**: `?range=7d`

**Response**:
```json
{
  "total_transactions": 150000,
  "total_anomalies": 120,
  "anomaly_rate": 0.08,
  "false_positive_rate": 0.01,
  "saved_amount": 450000.00
}
```

#### Get Time-Series Data
Data for line charts (Transactions vs. Anomalies).
- **Endpoint**: `GET /v1/stats/timeseries`
- **Response**: `[{ "date": "2025-01-01", "tx_count": 500, "anomaly_count": 2 }, ...]`

### 4. Alert Configuration

#### List Alert Channels
- **Endpoint**: `GET /v1/alerts/channels`

#### Configure Alert Channel
Set up where notifications should go.
- **Endpoint**: `POST /v1/alerts/channels`
- **Body**:
  ```json
  {
    "type": "WEBHOOK",
    "config": { "url": "https://slack.com/webhook/..." },
    "min_severity": "HIGH"
  }
  ```

#### Test Alert
Sends a dummy alert to verify configuration.
- **Endpoint**: `POST /v1/alerts/test`

### 5. Reports

#### Export Data
Download CSV/PDF reports.
- **Endpoint**: `POST /v1/reports/export`
- **Body**: `{ "format": "csv", "filters": {...} }`

## Data Retention Policy
- **Free Plan**: 7 days
- **Pro Plan**: 90 days
- **Advanced**: 1 year (Cold storage in S3/R2)

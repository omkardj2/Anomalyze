# Analytics & Reporting Service (`analytics-service`)

## 📖 Overview
The **Analytics Service** powers the frontend dashboard. It aggregates data from the `anomalies` database and provides actionable insights. It is optimized for **Read Heavy** workloads.

## 🏗 Architecture
- **Database**: Postgres (Read Replica preferred).
- **Cache**: Redis (for pre-computed dashboard stats).
- **Export Engine**: Generates CSV/PDF reports on the fly.

## 🔌 API Reference

### 1. Dashboard Widgets
#### Summary Stats
**Endpoint**: `GET /v1/stats/summary`
- **Query**: `?range=24h`
- **Response**:
  ```json
  {
    "total_transactions": 50000,
    "anomalies_detected": 12,
    "money_saved": 450000,
    "risk_score": "LOW"
  }
  ```

#### Time Series (Charts)
**Endpoint**: `GET /v1/stats/timeline`
- **Response**: Data points for "Transactions vs Anomalies" line chart.

#### Category Breakdown (Pie Chart)
**Endpoint**: `GET /v1/stats/categories`
- **Response**: `{ "Electronics": 40, "Travel": 30, "Food": 30 }`

### 2. Anomaly Management
#### List Anomalies
**Endpoint**: `GET /v1/anomalies`
- **Filters**: `severity`, `status` (OPEN, RESOLVED), `date_range`.
- **Pagination**: Cursor-based pagination for performance.

#### Get Anomaly Details
**Endpoint**: `GET /v1/anomalies/:id`
- **Includes**: Full explanation, rule triggered, and raw transaction data.

#### Resolve Anomaly
**Endpoint**: `PATCH /v1/anomalies/:id`
- **Body**: `{ "status": "RESOLVED", "feedback": "FALSE_POSITIVE" }`
- **Note**: Feedback is pushed to a queue for the ML Service to improve future training.

### 3. Reporting
#### Export Report
**Endpoint**: `POST /v1/reports/export`
- **Body**: `{ "format": "PDF", "type": "WEEKLY_SUMMARY" }`
- **Response**: Download URL.

## 📊 Data Aggregation Strategy
- **Real-time**: Queries `anomalies` table directly for recent data.
- **Historical**: Uses materialized views (refreshed hourly) for long-range stats (e.g., "Last 6 Months") to avoid slow queries on millions of rows.

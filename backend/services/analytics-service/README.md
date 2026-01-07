# Analytics Service (`analytics-service`)

## 📖 Overview
The **Analytics Service** is the central dashboard API for the Anomalyze platform. It aggregates data from the `transactions` and `anomalies` Kafka topics to provide real-time insights to the frontend.

It serves as the user's primary interface for visualizing:
1.  **Spending Trends**: Daily/Weekly aggregation of transaction amounts.
2.  **Anomaly Insights**: Count and severity distribution of detected anomalies.
3.  **Real-time Feed**: Recent activity stream.

## 🏗 Architecture
- **Language**: TypeScript (Node.js 20+)
- **Database**: PostgreSQL (Shared) - Stores aggregated stats.
- **Cache**: Redis - Caches "hot" dashboard data for <100ms load times.
- **Kafka**: Consumer - Listens to all system events to build views.

### Data Flow
```
┌─────────────┐    ┌───────────────────────────────────┐
│  Dashboard  │◄───│         Analytics Service         │
│  (React)    │    └─┬──────────────────────┬──────────┘
└─────────────┘      │                      │
            ┌────────▼──────┐       ┌───────▼───────┐
            │   PostgreSQL  │       │  Redis Cache  │
            │ (Aggregations)│       │ (Live Stats)  │
            └───────▲───────┘       └───────────────┘
                    │
            ┌───────┴───────┐
            │ Kafka Consumer│◄─── [Transactions, Anomalies]
            └───────────────┘
```

## 📁 Project Structure
```
analytics-service/
├── src/
│   ├── app.ts            # Express app
│   ├── jobs/             # Aggregation Cron Jobs
│   ├── services/
│   │   └── stats.service.ts
│   └── api/
│       └── dashboard.routes.ts
├── .env.example
├── Dockerfile
└── README.md
```

## 🚀 Quick Start (Running with Full Stack)

> **Tip:** Run everything via the master compose in `backend/`:
> ```bash
> cd ../..
> docker compose up -d
> ```

### Local Dev
1.  **Configure `.env`**: Copy `.env.example`.
2.  **Start Service**:
    ```bash
    npm install
    npm run dev
    ```

## 🔌 API Reference

### Health
**GET** `/health`

### Dashboard Stats
**GET** `/v1/stats/overview?range=7d`
- Returns total spend, anomaly count, and risk score.

**GET** `/v1/stats/anomalies`
- Returns recent anomalies with explanations.

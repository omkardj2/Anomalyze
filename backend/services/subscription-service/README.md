# Subscription Service (`subscription-service`)

## 📖 Overview
The **Subscription Service** handles all billing and plan management via **Razorpay**. It ensures users are on the correct tier to access platform features.

### Plans
1.  **Free**: 5 CSV uploads / month
2.  **Basic**: 5 CSV uploads / day
3.  **Pro**: Live API access + Webhook anomaly alerts

## 🏗 Architecture
- **Language**: TypeScript (Node.js 20+)
- **Payment Gateway**: Razorpay
- **Database**: PostgreSQL (Subscriptions, Invoices tables)
- **Message Broker**: Kafka (Publishes payment events)

### Data Flow
```
┌─────────────┐    ┌───────────────────────────────────┐    ┌──────────────┐
│  Frontend   │───►│       Subscription Service        │───►│   Razorpay   │
│ (Checkout)  │    └─┬─────────────────────────────────┘    └──────┬───────┘
└─────────────┘      │                                             │
            ┌────────▼──────┐                              ┌───────▼───────┐
            │   PostgreSQL  │                              │    Webhook    │
            │(Subs Status)  │                              │   (Payment)   │
            └───────────────┘                              └───────────────┘
```

## 📁 Project Structure
```
subscription-service/
├── src/
│   ├── app.ts            # Express app
│   ├── webhooks/         # Razorpay Webhook Handler
│   ├── services/
│   │   └── razorpay.ts   # SDK wrapper
│   └── api/
│       └── checkout.ts   # Create order
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
1.  **Configure `.env`**: Copy `.env.example` and add **Razorpay Keys**.
2.  **Start Service**:
    ```bash
    npm install
    npm run dev
    ```

## 🔌 API Reference

### Health
**GET** `/health`

### Checkout
**POST** `/v1/orders/create`
- Inputs: `planId` (basic/pro)
- Returns: `orderId` (for Razorpay frontend SDK)

### Webhooks
**POST** `/webhooks/razorpay`
- Verified signature and updates DB status to 'active'.

# Auth Service (`auth-service`)

## 📖 Overview
The **Auth Service** manages user identity and security for the Anomalyze platform. It leverages **Clerk** for robust authentication (Sign Up, Sign In, MFA) and synchronizes user data to our local PostgreSQL database.

It supports:
1.  **Identity Management**: Wrapper around Clerk SDK.
2.  **User Sync**: Webhook receiver to sync Create/Update/Delete events from Clerk to Postgres `User` table.
3.  **Token Verification**: Middleware for other services to validate requests.

## 🏗 Architecture
- **Language**: TypeScript (Node.js 20+)
- **Auth Provider**: Clerk
- **Database**: PostgreSQL (User Table)
- **Message Broker**: Kafka (User created events)

### Data Flow (User Registration)
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Client App  │───►│    Clerk     │───►│  Auth Service   │
│ (Frontend)  │    │  (Identity)  │    │    Webhook      │
└─────────────┘    └──────────────┘    └────────┬────────┘
                                                │
                                       ┌────────▼────────┐
                                       │   PostgreSQL    │
                                       │  (User Table)   │
                                       └─────────────────┘
```

## 📁 Project Structure
```
auth-service/
├── src/
│   ├── app.ts            # Express app
│   ├── config/           # Envs (Clerk Keys)
│   ├── webhooks/         # Clerk Webhook Handlers
│   │   └── user.sync.ts  # Sync logic
│   └── middleware/       # JWT Verification
├── .env.example
├── Dockerfile
└── README.md
```

## 🚀 Quick Start (Running with Full Stack)

> **Tip:** You can run the entire Anomalyze stack using the master docker-compose in the `backend/` directory:
> ```bash
> cd ../..
> docker compose up -d
> ```

### Local Dev
1.  **Configure `.env`**: Copy `.env.example` and add your **Clerk Keys**.
2.  **Start Service**:
    ```bash
    npm install
    npm run dev
    ```

## 🔌 API Reference

### Health
**GET** `/health`

### Webhooks
**POST** `/webhooks/clerk` - Endpoint for Clerk to push user updates.

### User Management
**GET** `/v1/me` - Get current user profile (synced from DB).

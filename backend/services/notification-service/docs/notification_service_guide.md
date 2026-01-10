# Notification Service - Complete Technical Deep Dive

This document provides a **file-by-file, function-by-function** explanation of the Notification Service, including theoretical concepts and the complete logic flow.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Entry Point & Configuration](#3-entry-point--configuration)
4. [Kafka Integration](#4-kafka-integration)
5. [Core Services](#5-core-services)
6. [API Layer](#6-api-layer)
7. [Testing & Scripts](#7-testing--scripts)
8. [Deployment Configuration](#8-deployment-configuration)
9. [Complete Data Flow](#9-complete-data-flow)

---

## 1. Architecture Overview

### What is this service?
The Notification Service is a **Kafka Consumer** that listens for anomaly detection events and dispatches alerts to users through multiple channels (Email, SMS, Voice, Webhooks).

### Why is it a separate microservice?
In the Event-Driven Architecture (EDA) of Anomalyze:
- **Separation of Concerns**: The ML service detects anomalies; this service handles delivery.
- **Scalability**: Notification delivery can be scaled independently.
- **Fault Isolation**: If notification fails, it doesn't affect detection.

### Core Responsibilities
1. **Consume** events from Kafka `anomalies` topic.
2. **Deduplicate** alerts using Redis (prevent spam).
3. **Authorize** channels based on user subscription (Free vs Pro).
4. **Dispatch** notifications via Email/SMS/Webhook/Voice.
5. **Produce** an audit trail back to Kafka `alerts` topic.

---

## 2. Directory Structure

```
notification-service/
├── src/
│   ├── app.ts              # Application entry point
│   ├── config.ts           # (Empty - configured via app.ts)
│   ├── api/
│   │   └── routes.ts       # REST API endpoints for testing
│   ├── kafka/
│   │   ├── consumer.ts     # Core Kafka consumer logic
│   │   └── producer.ts     # Produces alert audit events
│   └── services/
│       ├── email.service.ts
│       ├── sms.service.ts
│       ├── call.service.ts
│       ├── webhook.service.ts
│       ├── deduplication.service.ts
│       └── subscription.service.ts
├── scripts/                 # Helper scripts for testing
├── tests/                   # Jest test files
├── prisma/                  # Database schema
├── docs/                    # Documentation (this file)
├── Dockerfile               # Production container build
├── package.json             # Dependencies & scripts
└── tsconfig.json            # TypeScript configuration
```

---

## 3. Entry Point & Configuration

### `src/app.ts` - Application Bootstrap

**Purpose**: Initialize the Express server, validate environment variables, and conditionally start the Kafka consumer.

#### Key Sections:

```typescript
// 1. Load Environment Variables
dotenv.config();
```
**Theory**: `dotenv` reads `.env` file and populates `process.env`. This allows secrets (like API keys) to be externalized from code.

```typescript
// 2. Validate Environment Variables using Zod
const envSchema = z.object({
    PORT: z.string().default('3001'),
    KAFKA_BOOTSTRAP_SERVERS: z.string().min(1, "Required"),
    REDIS_URL: z.string().optional(),
    // ...
});
```
**Theory**: Zod provides runtime validation. If a required variable is missing, the service exits immediately with a clear error instead of failing later at runtime.

```typescript
// 3. Conditional Kafka Consumer Start
if (process.env.ENABLE_KAFKA === 'true') {
    startKafkaConsumer();
}
```
**Theory**: This allows running the service in "API-only" mode for testing without needing Kafka infrastructure.

---

## 4. Kafka Integration

### `src/kafka/consumer.ts` - The Heart of the Service

**Purpose**: Subscribe to the `anomalies` topic, process each event, and dispatch notifications.

#### Key Functions:

##### `retry<T>(fn, retries, backoffMs)`
```typescript
async function retry<T>(fn: () => Promise<T>, retries = 3, backoffMs = 2000): Promise<T>
```
**Purpose**: Wrap external API calls (email, SMS) in a retry loop with exponential backoff.

**Theory**: External services can have transient failures. Retrying with increasing delays (2s → 4s → 8s) gives time for recovery without overwhelming the service.

##### `startKafkaConsumer()`
```typescript
export const startKafkaConsumer = async () => { ... }
```
**Purpose**: Main consumer loop.

**Flow**:
1. Create Kafka client with broker addresses.
2. Create consumer with a unique `groupId`.
3. Subscribe to `anomalies` topic.
4. For each message:
   - Parse JSON payload.
   - Extract `userId` and `txId`.
   - **Deduplication Check**: Call `shouldSendAlert(userId, txId)`.
   - **User Context Fetch**: Call `getUserContext(userId)`.
   - **Channel Authorization**: Call `canSendNotification(context, channel, severity)`.
   - **Dispatch**: Call appropriate service (email, SMS, etc.).
   - **Audit**: Produce alert event to `alerts` topic.

**Error Handling**: If any step fails, error is logged but consumer continues processing other messages.

---

### `src/kafka/producer.ts` - Audit Trail

**Purpose**: Produce audit events back to Kafka so other services can track what notifications were sent.

#### Key Functions:

##### `startKafkaProducer()`
```typescript
export const startKafkaProducer = async () => { ... }
```
**Purpose**: Connect the producer to Kafka. Called once at startup.

##### `produceAlertEvent(alertEvent)`
```typescript
export const produceAlertEvent = async (alertEvent: { ... }) => { ... }
```
**Purpose**: Send a structured event to the `alerts` topic.

**Event Schema**:
```json
{
  "alertId": "alert_1704067200000",
  "userId": "user_123",
  "severity": "CRITICAL",
  "channels": { "email": true, "sms": false, "webhook": true, "call": true },
  "sourceEvent": { ... },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

---

## 5. Core Services

### `src/services/email.service.ts`

**Purpose**: Send emails using SMTP (Nodemailer).

#### Key Functions:

##### `sendEmailNotification({ to, subject, body })`
```typescript
export const sendEmailNotification = async ({ to, subject, body }: EmailPayload) => { ... }
```
**Flow**:
1. Check if SMTP transporter is configured.
2. If not: **Log the email** (graceful degradation).
3. If yes: **Send via SMTP** and log the result.

**Theory**: Graceful degradation means the service doesn't crash if SMTP credentials are missing. This is critical for development/testing environments.

---

### `src/services/sms.service.ts`

**Purpose**: Send SMS using Twilio.

#### Key Functions:

##### `sendSmsNotification({ to, message })`
```typescript
export const sendSmsNotification = async ({ to, message }: SmsPayload) => { ... }
```
**Flow**:
1. Check if Twilio client is initialized.
2. If not: **Log the SMS**.
3. If yes: Call `twilioClient.messages.create()`.

**Required Environment Variables**:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

---

### `src/services/call.service.ts`

**Purpose**: Make voice calls using Twilio for critical alerts.

#### Key Functions:

##### `makeCallNotification({ to, message })`
```typescript
export const makeCallNotification = async ({ to, message }: CallPayload) => { ... }
```
**Flow**:
1. Check if Twilio client is initialized.
2. If not: **Log the call**.
3. If yes: Call `client.calls.create()` with TwiML (XML-based voice script).

**TwiML Example**:
```xml
<Response>
  <Say voice="alice">Critical anomaly detected. Please check immediately.</Say>
</Response>
```

---

### `src/services/webhook.service.ts`

**Purpose**: Send HTTP POST requests to user-configured webhook endpoints.

#### Key Functions:

##### `generateSignature(payload, secret)`
```typescript
const generateSignature = (payload: string, secret: string): string => { ... }
```
**Purpose**: Create HMAC SHA-256 signature for payload verification.

**Theory**: HMAC signing allows receivers to verify that the webhook came from our service and wasn't tampered with. The signature is sent in `X-Webhook-Signature` header.

##### `sendWebhookNotification({ url, data, secret, timeoutMs })`
```typescript
export const sendWebhookNotification = async ({ ... }: WebhookPayload) => { ... }
```
**Flow**:
1. Create JSON payload.
2. If secret provided: Generate HMAC signature.
3. Send POST request with headers.
4. Log result (success or failure).

---

### `src/services/deduplication.service.ts`

**Purpose**: Prevent duplicate notifications for the same anomaly.

#### Key Functions:

##### `shouldSendAlert(userId, txId)`
```typescript
export const shouldSendAlert = async (userId: string, txId: string): Promise<boolean> => { ... }
```
**Algorithm**:
1. Create unique key: `alert:{userId}:{txId}`.
2. Execute Redis `SETNX` with 15-minute TTL.
3. If `SETNX` returns `OK`: This is a new alert → **Allow**.
4. If `SETNX` returns `null`: Key exists → **Block (Duplicate)**.

**Theory**: `SETNX` (Set if Not Exists) is atomic. This prevents race conditions when multiple consumers process the same event.

**Fail-Open Strategy**:
```typescript
if (!redis || redis.status !== 'ready') {
    return true; // Allow alert if Redis is down
}
```
**Theory**: Notification delivery is more important than deduplication. If Redis fails, we prefer to send a duplicate rather than miss an alert.

---

### `src/services/subscription.service.ts`

**Purpose**: Fetch user details from the database and enforce subscription-based access to channels.

#### Key Functions:

##### `getUserContext(userId)`
```typescript
export const getUserContext = async (userId: string): Promise<UserContext | null> => { ... }
```
**Flow**:
1. Query Postgres for User with `subscription` and `notificationSettings` relations.
2. If user not found: Return `null`.
3. Otherwise: Return structured context object.

**Context Object**:
```typescript
{
  userId: string;
  email: string | null;
  phone: string | null;
  plan: 'FREE' | 'BASIC' | 'PRO';
  features: { sms?: boolean; ... };
  settings: { emailEnabled: boolean; phoneEnabled: boolean; minSeverityForCall: Severity; };
}
```

##### `canSendNotification(context, channel, severity)`
```typescript
export const canSendNotification = (context: UserContext, channel: 'EMAIL' | 'SMS' | 'VOICE', severity: Severity): boolean => { ... }
```
**Business Rules**:
| Channel | Requirement |
|---------|-------------|
| Email   | Always allowed (if `emailEnabled`) |
| SMS     | PRO plan OR `features.sms === true` |
| Voice   | PRO plan AND severity === CRITICAL |

---

## 6. API Layer

### `src/api/routes.ts`

**Purpose**: Expose REST endpoints for manual testing of notification channels.

#### Endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/notifications/test/email` | Send test email |
| POST | `/api/v1/notifications/test/sms` | Send test SMS |
| POST | `/api/v1/notifications/test/webhook` | Send test webhook |

**Note**: These are for development/debugging only. In production, notifications are triggered by Kafka events.

---

## 7. Testing & Scripts

### `tests/health.test.ts`
Basic Jest test verifying the `/health` endpoint returns 200 OK.

### `scripts/verify-smtp.ts`
Standalone script to test SMTP credentials by sending a real email.

### `scripts/verify-dedup.ts`
Tests Redis deduplication logic by simulating duplicate alerts.

### `scripts/verify-subscription.ts`
Creates temporary users in DB and verifies subscription tier enforcement.

### `scripts/produce-test-event.ts`
Produces a test anomaly event to Kafka for end-to-end testing.

---

## 8. Deployment Configuration

### `Dockerfile`

**Multi-Stage Build**:
1. **Builder Stage**: Compiles TypeScript, generates Prisma client.
2. **Runner Stage**: Copies only production files, runs as non-root user.

**Security Features**:
- Runs as `appuser` (non-root).
- Only production dependencies installed.
- Health check built-in.

### Required Environment Variables for Production

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Postgres connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | ✅ | Kafka broker addresses |
| `ENABLE_KAFKA` | ✅ | Set to `true` to start consumer |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` | Optional | Email credentials |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | Optional | SMS/Voice credentials |

---

## 9. Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ANOMALYZE SYSTEM                             │
└─────────────────────────────────────────────────────────────────────┘

1. ML Service detects anomaly
        ↓
2. Event published to Kafka `anomalies` topic
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   NOTIFICATION SERVICE                              │
├─────────────────────────────────────────────────────────────────────┤
│  3. consumer.ts receives event                                      │
│        ↓                                                            │
│  4. Deduplication Check (Redis SETNX)                               │
│     - If duplicate → SKIP                                           │
│     - If new → CONTINUE                                             │
│        ↓                                                            │
│  5. Fetch User Context (Postgres)                                   │
│     - Email, Phone, Subscription Plan, Settings                     │
│        ↓                                                            │
│  6. Authorization Check                                             │
│     - FREE: Email only                                              │
│     - PRO: Email + SMS + Voice (Critical)                           │
│        ↓                                                            │
│  7. Dispatch Notifications (with retry)                             │
│     - email.service.ts → Gmail/SendGrid                             │
│     - sms.service.ts → Twilio                                       │
│     - call.service.ts → Twilio                                      │
│     - webhook.service.ts → User's endpoint                          │
│        ↓                                                            │
│  8. Produce Audit Event                                             │
│     - producer.ts → Kafka `alerts` topic                            │
└─────────────────────────────────────────────────────────────────────┘
        ↓
9. Other services (Analytics, Dashboard) consume `alerts` for logging
```

---

**End of Documentation**  
*Generated: 2026-01-10*

# Identity & Entitlements Service (`auth-service`)

## Overview
The **Identity & Entitlements Service** is the foundational layer for user identity, access control, and billing integration. It manages the lifecycle of users, their API keys for programmatic access, and their subscription status via Stripe. It serves as the "Source of Truth" for what a user is allowed to do within the platform.

## Architecture
- **Authentication**: Clerk (JWT Handling)
- **Database**: Neon Postgres (`users`, `subscriptions`, `api_keys`)
- **Billing**: Stripe (Checkout & Webhooks)
- **Communication**: Publishes `user.created`, `user.updated` events to Kafka.

## API Reference

### 1. User Management

#### Get Current User Profile
Retrieves the authenticated user's profile, active plan, and feature flags.
- **Endpoint**: `GET /v1/users/me`
- **Auth**: Bearer Token (JWT)

```json
{
  "id": "user_123",
  "email": "alice@example.com",
  "role": "ADMIN",
  "subscription": {
    "plan": "ADVANCED",
    "status": "ACTIVE",
    "expiry": "2026-01-01T00:00:00Z"
  }
}
```

#### Update User Profile
Updates user preferences or metadata.
- **Endpoint**: `PATCH /v1/users/me`
- **Body**: `{ "name": "Alice Corp", "settings": { "theme": "dark" } }`

### 2. API Key Management
Manage long-lived API keys used for the Ingestion Service.

#### Create API Key
Generates a new API key for server-to-server integration.
- **Endpoint**: `POST /v1/api-keys`
- **Body**: `{ "name": "Production Ingestion Key", "scopes": ["ingest:write"] }`
- **Response**:
  ```json
  {
    "id": "key_xyz",
    "secret": "sk_live_...", // Shown only once
    "createdAt": "2025-01-01T12:00:00Z"
  }
  ```

#### List API Keys
- **Endpoint**: `GET /v1/api-keys`

#### Revoke API Key
- **Endpoint**: `DELETE /v1/api-keys/:id`

### 3. Subscription & Billing

#### List Available Plans
Returns public pricing tiers and features.
- **Endpoint**: `GET /v1/subscriptions/plans`

#### Create Checkout Session
Initiates a Stripe Checkout flow for upgrading/downgrading.
- **Endpoint**: `POST /v1/subscriptions/checkout`
- **Body**: `{ "planId": "price_pro_monthly" }`
- **Response**: `{ "checkoutUrl": "https://checkout.stripe.com/..." }`

#### Customer Portal
Generates a link to the Stripe Customer Portal for billing management.
- **Endpoint**: `POST /v1/subscriptions/portal`

#### Stripe Webhook
Handles asynchronous billing events.
- **Endpoint**: `POST /webhooks/stripe`
- **Events Handled**: `checkout.session.completed`, `customer.subscription.updated`, `invoice.payment_failed`.

### 4. Admin (Internal)

#### Get User Entitlements (Internal)
Used by other services (like Ingestion) to check limits.
- **Endpoint**: `GET /internal/entitlements/:userId`
- **Auth**: Service-to-Service Token

## Error Codes
| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid or expired JWT |
| `SUB_001` | Active subscription required |
| `KEY_001` | API Key limit reached |

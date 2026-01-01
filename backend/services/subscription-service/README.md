# Subscription & Billing Service (`subscription-service`)

## Overview
The **Subscription Service** encapsulates all billing logic, plan management, and entitlement enforcement. It synchronizes state with Stripe and provides a high-speed internal API for other services to check what features a user can access.

## Architecture
- **Payment Processor**: Stripe
- **Database**: Postgres (`subscriptions`, `invoices`, `usage_records`)
- **Cache**: Redis (Entitlements caching for <5ms lookups)

## API Reference

### 1. Public Plans

#### Get Pricing Tiers
Returns available subscription plans and their feature sets.
- **Endpoint**: `GET /v1/plans`
- **Response**:
  ```json
  [
    {
      "id": "price_free",
      "name": "Hobby",
      "price": 0,
      "features": { "retention": 7, "requests_per_min": 60 }
    },
    {
      "id": "price_pro",
      "name": "Pro",
      "price": 4900, // $49.00
      "features": { "retention": 90, "requests_per_min": 1000 }
    }
  ]
  ```

### 2. Subscription Management

#### Create Checkout Session
Generates a Stripe Checkout URL for upgrading/downgrading.
- **Endpoint**: `POST /v1/checkout`
- **Body**: `{ "price_id": "price_pro", "success_url": "...", "cancel_url": "..." }`

#### Get Current Subscription
- **Endpoint**: `GET /v1/subscription/me`

#### Cancel Subscription
- **Endpoint**: `POST /v1/subscription/cancel`
- **Body**: `{ "reason": "Too expensive" }`

#### Billing Portal
Get a link to the Stripe self-serve portal (update card, download invoices).
- **Endpoint**: `POST /v1/portal`

### 3. Entitlements (Internal High-Performance)

#### Check Entitlement
Used by Ingestion/ML services to verify limits.
- **Endpoint**: `GET /internal/entitlements/:userId`
- **Response**:
  ```json
  {
    "plan": "PRO",
    "status": "ACTIVE",
    "limits": {
      "daily_ingestion": 100000,
      "alert_channels": 5
    },
    "features": ["ml_inference", "export_pdf"]
  }
  ```

#### Report Usage
Report metered usage (e.g., number of transactions processed) to Stripe.
- **Endpoint**: `POST /internal/usage`
- **Body**: `{ "user_id": "user_123", "metric": "transactions_processed", "quantity": 50 }`

### 4. Webhooks

#### Stripe Webhook Handler
The single entry point for Stripe events.
- **Endpoint**: `POST /webhooks/stripe`
- **Security**: Verifies `Stripe-Signature` header.
- **Handled Events**:
  - `checkout.session.completed`: Provision new subscription.
  - `invoice.payment_succeeded`: Renew access.
  - `invoice.payment_failed`: Enter grace period / downgrade.
  - `customer.subscription.deleted`: Revoke access.

## Data Model
**Table**: `subscriptions`
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | VARCHAR | Foreign Key to Auth Service |
| `stripe_customer_id` | VARCHAR | Stripe Customer ID |
| `stripe_sub_id` | VARCHAR | Stripe Subscription ID |
| `status` | ENUM | active, trialing, past_due, canceled |
| `current_period_end` | TIMESTAMP | Expiry date |

## Dependencies
- `stripe-node`: Official Stripe SDK.
- `redis`: For caching entitlement responses.

# Subscription & Billing Service (`subscription-service`)

## 📖 Overview
The **Subscription Service** handles the entire billing lifecycle using **Razorpay Subscriptions**. It manages plans, recurring payments, and generates compliant PDF invoices asynchronously. It serves as the "Source of Truth" for user entitlements (Basic vs. Pro).

## 🏗 Architecture
- **Payment Gateway**: Razorpay (Subscription API).
- **Invoice Storage**: AWS S3 / Cloudflare R2.
- **Queue**: Kafka (`billing-events` topic) for async invoice generation.
- **Database**: Postgres (`subscriptions`, `invoices`, `plans`).

## 🔄 Subscription Lifecycle
1.  **Created**: User selects a plan -> Razorpay Subscription ID generated.
2.  **Authenticated**: User completes payment on Razorpay Checkout.
3.  **Active**: Webhook `subscription.charged` received -> DB updated to `ACTIVE`.
4.  **Halted**: Payment fails -> Retry logic -> Status `PAST_DUE` -> `HALTED`.
5.  **Cancelled**: User cancels -> Access remains until `current_period_end`.

## 🔌 API Reference

### 1. Plan Management
#### List Plans
**Endpoint**: `GET /v1/plans`
- **Response**:
  ```json
  [
    { "id": "plan_basic", "name": "Basic", "price": 999, "currency": "INR", "interval": "monthly" },
    { "id": "plan_pro", "name": "Pro", "price": 4999, "currency": "INR", "interval": "monthly" }
  ]
  ```

### 2. Subscription Flow
#### Create Subscription
**Endpoint**: `POST /v1/subscriptions`
- **Body**: `{ "plan_id": "plan_pro" }`
- **Response**:
  ```json
  {
    "subscription_id": "sub_123456",
    "short_url": "https://rzp.io/i/..." // Razorpay Checkout URL
  }
  ```

#### Cancel Subscription
**Endpoint**: `POST /v1/subscriptions/cancel`
- **Description**: Cancels auto-renewal. Access continues until cycle end.

#### Get Current Status
**Endpoint**: `GET /v1/subscriptions/me`
- **Response**: `{ "status": "ACTIVE", "plan": "PRO", "renews_at": "2026-02-01" }`

### 3. Invoicing (Async Pipeline)
#### List Invoices
**Endpoint**: `GET /v1/invoices`

#### Download Invoice
**Endpoint**: `GET /v1/invoices/:id/download`
- **Response**: Redirects to S3/R2 signed URL for the PDF.

### 4. Webhooks (Razorpay)
**Endpoint**: `POST /webhooks/razorpay`
- **Security**: Validates `X-Razorpay-Signature`.
- **Events**:
    - `subscription.charged`: Extend validity, trigger `invoice-generation` Kafka event.
    - `subscription.halted`: Downgrade user to Free tier.
    - `payment.failed`: Notify user via Notification Service.

### 5. Internal Entitlements
**Endpoint**: `GET /internal/entitlements/:user_id`
- **Used By**: Ingestion Service, ML Service.
- **Response**:
  ```json
  {
    "plan": "PRO",
    "features": {
      "live_ingestion": true,
      "phone_alerts": true,
      "retention_days": 90
    }
  }
  ```

## 📄 Invoice Generation Workflow
1.  **Trigger**: `subscription.charged` webhook received.
2.  **Publish**: Event `{ "user_id": "...", "amount": 4999, "date": "..." }` pushed to Kafka `invoices` topic.
3.  **Worker**:
    - Consumes event.
    - Generates HTML from template.
    - Converts HTML -> PDF (Puppeteer/Playwright).
    - Uploads to S3/R2.
    - Inserts record into `invoices` table.

# Notification Service (`notification-service`)

## Overview
The **Notification Service** is a centralized delivery engine responsible for dispatching critical alerts and system messages to users across multiple channels (Email, Slack, Webhooks, SMS). It abstracts provider complexity and handles retries, rate limiting, and template rendering.

## Architecture
- **Input**: Kafka Topic `alerts` (Async) & REST API (Sync)
- **Providers**: 
  - **Email**: SendGrid / AWS SES
  - **SMS**: Twilio
  - **Chat**: Slack Webhooks / Discord
- **Storage**: Postgres (`notification_logs`, `channels`)

## API Reference

### 1. Channel Management

#### Register Notification Channel
Users can configure where they want to receive alerts.
- **Endpoint**: `POST /v1/channels`
- **Auth**: Bearer Token
- **Body**:
  ```json
  {
    "type": "SLACK",
    "name": "DevOps Channel",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/..."
    },
    "events": ["ANOMALY_CRITICAL", "BILLING_FAILED"]
  }
  ```

#### List Channels
- **Endpoint**: `GET /v1/channels`

#### Delete Channel
- **Endpoint**: `DELETE /v1/channels/:id`

### 2. Dispatch API (Internal)

#### Send Notification
Used by other services (e.g., Auth Service for "Welcome Email") to trigger notifications programmatically.
- **Endpoint**: `POST /v1/dispatch`
- **Auth**: Service Token
- **Body**:
  ```json
  {
    "user_id": "user_123",
    "template_id": "welcome_email_v1",
    "data": { "name": "Alice" },
    "channels": ["EMAIL"]
  }
  ```

### 3. History & Audit

#### Get Notification Logs
View the delivery status of past notifications.
- **Endpoint**: `GET /v1/history`
- **Query**: `?status=FAILED&limit=20`

**Response**:
```json
[
  {
    "id": "notif_999",
    "event": "ANOMALY_DETECTED",
    "channel": "EMAIL",
    "status": "DELIVERED",
    "sent_at": "2025-12-20T12:05:00Z"
  }
]
```

### 4. Template Management (Admin)

#### Create/Update Template
Manage HTML/Text templates for emails.
- **Endpoint**: `PUT /v1/templates/:id`
- **Body**:
  ```json
  {
    "subject": "Alert: {{severity}} Anomaly Detected",
    "body_html": "<h1>Anomaly Detected</h1><p>Transaction ID: {{tx_id}}</p>"
  }
  ```

## Event Consumption
The service listens to the `alerts` Kafka topic.
1. **Consume**: Read message `{ "anomaly_id": "...", "user_id": "..." }`.
2. **Resolve**: Fetch user's configured channels from DB.
3. **Render**: Hydrate template with anomaly details.
4. **Send**: Dispatch to SendGrid/Slack.
5. **Log**: Record outcome in `notification_logs`.

## Error Handling
- **Retries**: Exponential backoff for 5xx provider errors (up to 3 times).
- **Dead Letter Queue**: Failed messages are pushed to `alerts-dlq` for manual inspection.

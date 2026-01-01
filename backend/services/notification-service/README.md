# Notification Service (`notification-service`)

## 📖 Overview
The **Notification Service** is a multi-channel alert dispatcher. It handles critical anomaly alerts with a tiered escalation policy.
- **Basic Users**: Email only (Nodemailer).
- **Pro Users**: Email + **Voice Call** (Twilio) with Text-to-Speech (TTS).

## 🏗 Architecture
- **Email**: Nodemailer (SMTP / SES / SendGrid).
- **Voice**: Twilio Programmable Voice API.
- **Input**: Kafka Topic `alerts`.
- **Logic**: Severity-based routing & User Plan checks.

## 🔌 API Reference

### 1. Configuration
#### Update Notification Settings
**Endpoint**: `PATCH /v1/settings`
- **Body**:
  ```json
  {
    "email_enabled": true,
    "phone_enabled": true, // Only allowed if Plan = PRO
    "phone_number": "+919876543210",
    "min_severity_for_call": "CRITICAL" // HIGH or CRITICAL
  }
  ```

### 2. Testing
#### Test Channel
**Endpoint**: `POST /v1/test`
- **Body**: `{ "channel": "VOICE" }`
- **Description**: Triggers a dummy call to verify Twilio integration.

## 📞 Voice Call Logic (Twilio)
**Workflow for Pro Users:**
1.  **Anomaly Detected**: Kafka message received `{ "severity": "CRITICAL", "amount": 50000 }`.
2.  **Check Preferences**: Is `phone_enabled`? Is severity >= `min_severity`?
3.  **Initiate Call**: Call user via Twilio.
4.  **TwiML Execution (TTS)**:
    ```xml
    <Response>
      <Say voice="alice">
        This is an alert from Anomalyze. 
        We detected a critical anomaly of 50,000 Rupees. 
        Please check your dashboard immediately.
      </Say>
    </Response>
    ```
5.  **Fallback**: If call status is `busy` or `no-answer`, log it and send an SMS/Email backup.

## 📧 Email Logic (Nodemailer)
- **Templates**: Handlebars (`.hbs`) templates for consistent branding.
- **Transport**: Configurable SMTP (Gmail for dev, SES/SendGrid for prod).
- **Rate Limiting**: Max 10 emails/hour per user to prevent spamming during anomaly storms.

## 📨 Event Consumer
**Topic**: `alerts`
**Payload**:
```json
{
  "user_id": "user_123",
  "anomaly_id": "anom_999",
  "severity": "CRITICAL",
  "details": {
    "amount": 50000,
    "merchant": "Unknown"
  }
}
```
**Processing**:
1.  Fetch user profile & plan (Cached).
2.  If `Plan == PRO` && `Severity == CRITICAL` -> **Trigger Call**.
3.  Always **Trigger Email**.

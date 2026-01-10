// src/services/webhook.service.ts
import axios from 'axios';
import crypto from 'crypto';

interface WebhookPayload {
  url: string;
  data: Record<string, any>;
  secret?: string; // signing secret (shared with receiver)
  timeoutMs?: number;
}

/* ======================================================
   Helpers
====================================================== */

/**
 * Generates HMAC SHA256 signature
 */
const generateSignature = (
  payload: string,
  secret: string
): string => {
  return crypto
    .createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');
};

/* ======================================================
   Webhook Sender
====================================================== */

export const sendWebhookNotification = async ({
  url,
  data,
  secret,
  timeoutMs = 5000,
}: WebhookPayload): Promise<void> => {
  const timestamp = Date.now().toString();
  const payloadString = JSON.stringify(data);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Webhook-Timestamp': timestamp,
  };

  /* ---------------- HMAC Signing ---------------- */
  if (secret) {
    const signaturePayload = `${timestamp}.${payloadString}`;
    const signature = generateSignature(signaturePayload, secret);

    headers['X-Webhook-Signature'] = signature;
    headers['X-Webhook-Signature-Version'] = 'v1';
  }

  try {
    const response = await axios.post(url, data, {
      headers,
      timeout: timeoutMs,
      validateStatus: () => true, // webhook endpoints may return non-2xx
    });

    if (response.status >= 200 && response.status < 300) {
      console.log(`🔗 Webhook delivered → ${url} (${response.status})`);
    } else {
      console.warn(
        `⚠️ Webhook responded with ${response.status} → ${url}`
      );
    }
  } catch (err: any) {
    console.error(
      `❌ Webhook delivery failed → ${url}`,
      err?.message || err
    );
  }
};

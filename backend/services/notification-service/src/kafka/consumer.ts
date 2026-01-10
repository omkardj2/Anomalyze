// src/kafka/consumer.ts
import { Kafka, EachMessagePayload } from 'kafkajs';

import { sendEmailNotification } from '../services/email.service';
import { sendSmsNotification } from '../services/sms.service';
import { sendWebhookNotification } from '../services/webhook.service';
import { makeCallNotification } from '../services/call.service';
import { shouldSendAlert } from '../services/deduplication.service';
import { getUserContext, canSendNotification } from '../services/subscription.service';

import {
  startKafkaProducer,
  produceAlertEvent,
} from './producer';

const KAFKA_BROKERS =
  process.env.KAFKA_BOOTSTRAP_SERVERS?.split(',') || ['localhost:9092'];

const KAFKA_TOPIC =
  process.env.KAFKA_ANOMALIES_TOPIC || 'anomalies';

const KAFKA_GROUP_ID =
  process.env.KAFKA_GROUP_ID || 'notification-service-group';

const MAX_RETRIES = 3;
const BACKOFF_BASE_MS = 2000;

/**
 * Retry helper with exponential backoff
 */
async function retry<T>(
  fn: () => Promise<T>,
  retries = MAX_RETRIES,
  backoffMs = BACKOFF_BASE_MS
): Promise<T> {
  let attempt = 0;

  while (true) {
    try {
      return await fn();
    } catch (err) {
      attempt++;
      if (attempt > retries) throw err;

      console.warn(
        `⚠️ Retry ${attempt}/${retries} failed. Retrying in ${backoffMs}ms...`
      );
      await new Promise(res => setTimeout(res, backoffMs));
      backoffMs *= 2;
    }
  }
}

export const startKafkaConsumer = async () => {
  const kafka = new Kafka({
    clientId: 'notification-service',
    brokers: KAFKA_BROKERS,
  });

  const consumer = kafka.consumer({ groupId: KAFKA_GROUP_ID });

  // 🔥 Start producer ONCE
  await startKafkaProducer();

  await consumer.connect();
  console.log(`✅ Kafka consumer connected: ${KAFKA_BROKERS.join(', ')}`);

  await consumer.subscribe({
    topic: KAFKA_TOPIC,
    fromBeginning: false,
  });

  console.log(`📩 Subscribed to topic: ${KAFKA_TOPIC}`);

  await consumer.run({
    eachMessage: async ({ message }: EachMessagePayload) => {
      if (!message.value) return;

      const event = JSON.parse(message.value.toString());
      const userId = event.userId || event.meta?.user_id || 'unknown_user';
      // Find identifying ID (tx_id preferred)
      const txId = event.data?.tx_id || event.tx_id || event.id || 'unknown_tx';

      console.log('📢 Received anomaly event:', event);

      // 🛑 DEDUPLICATION CHECK
      const shouldSend = await shouldSendAlert(userId, txId);
      if (!shouldSend) {
        return;
      }

      try {
        // 🔍 FETCH USER CONTEXT (DB)
        const userContext = await getUserContext(userId);

        if (!userContext) {
          console.warn(`⚠️ User not found in DB: ${userId}. Skipping notification.`);
          return;
        }

        const severity = event.severity || 'MEDIUM';

        // -------- EMAIL --------
        // Check DB settings & Tier
        if (canSendNotification(userContext, 'EMAIL', severity)) {
          // Use DB email if available, fallback to event (for reliability)
          const emailTo = userContext.email || event.email;
          if (emailTo) {
            await retry(() =>
              sendEmailNotification({
                to: emailTo,
                subject: `Anomaly Alert for ${userId}`,
                body: JSON.stringify(event, null, 2),
              })
            );
          }
        } else {
          console.log(`🚫 Email suppressed for ${userId} (Disabled/Settings)`);
        }

        // -------- SMS --------
        if (canSendNotification(userContext, 'SMS', severity)) {
          const phoneTo = userContext.phone || event.phone;
          if (phoneTo) {
            await retry(() =>
              sendSmsNotification({
                to: phoneTo,
                message: `Anomaly detected for ${userId}. Severity: ${event.severity}`,
              })
            );
          }
        } else {
          // Only log if they HAVE a phone but were denied by tier
          if (userContext.phone || event.phone) {
            console.log(`🚫 SMS suppressed for ${userId} (Tier: ${userContext.plan} - Needs PRO)`);
          }
        }

        // -------- WEBHOOK --------
        // Webhooks are usually explicitly configured in DB settings
        // Assuming current implementation uses event.webhookUrl, let's keep it but ideally fetch from userContext.settings
        if (event.webhookUrl) {
          await retry(() =>
            sendWebhookNotification({
              url: event.webhookUrl,
              data: { userId, event },
              secret: process.env.WEBHOOK_SIGNING_SECRET,
            })
          );
        }

        // -------- CALL --------
        if (canSendNotification(userContext, 'VOICE', severity)) {
          const phoneTo = userContext.phone || event.phone;
          if (phoneTo) {
            await retry(() =>
              makeCallNotification({
                to: phoneTo,
                message: `Critical anomaly detected for user ${userId}. Please check immediately.`,
              })
            );
          }
        }

        // -------- PRODUCE ALERT EVENT --------
        await produceAlertEvent({
          alertId: `alert_${Date.now()}`,
          userId,
          severity: event.severity,
          channels: {
            // Log what was ACTUALLY allowed
            email: canSendNotification(userContext, 'EMAIL', severity),
            sms: canSendNotification(userContext, 'SMS', severity),
            webhook: !!event.webhookUrl,
            call: canSendNotification(userContext, 'VOICE', severity),
          },
          sourceEvent: event,
          timestamp: new Date().toISOString(),
        });

        console.log(`✅ Notifications processed for user: ${userId} (Plan: ${userContext.plan})`);
      } catch (err) {
        console.error(
          `❌ Failed processing notifications for user: ${userId}`,
          err
        );
      }
    },
  });
};

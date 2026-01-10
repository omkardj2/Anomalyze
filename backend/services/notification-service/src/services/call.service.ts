// src/services/call.service.ts
import twilio from 'twilio';

const {
  TWILIO_ACCOUNT_SID,
  TWILIO_AUTH_TOKEN,
  TWILIO_CALL_FROM,
} = process.env;

let client: ReturnType<typeof twilio> | null = null;

if (TWILIO_ACCOUNT_SID && TWILIO_AUTH_TOKEN) {
  client = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);
}

interface CallPayload {
  to: string;
  message: string;
}

export const makeCallNotification = async ({
  to,
  message,
}: CallPayload) => {
  if (!client) {
    console.warn('📞 Twilio not configured. Call logged only.');
    console.log(`[CALL] → ${to}: ${message}`);
    return;
  }

  try {
    await client.calls.create({
      to,
      from: TWILIO_CALL_FROM!,
      twiml: `
        <Response>
          <Say voice="alice">
            ${message}
          </Say>
        </Response>
      `,
    });

    console.log(`📞 Call placed to ${to}`);
  } catch (err: any) {
    console.error('❌ Failed to place call:', err.message || err);
  }
};

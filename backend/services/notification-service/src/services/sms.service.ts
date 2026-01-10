// src/services/sms.service.ts
import twilio, { Twilio as TwilioClient } from 'twilio';

interface SmsPayload {
  to: string;
  message: string;
}

let twilioClient: TwilioClient | null = null;
if (process.env.TWILIO_ACCOUNT_SID && process.env.TWILIO_AUTH_TOKEN) {
  twilioClient = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
} else {
  console.warn('⚠️ Twilio credentials not found. SMS notifications will be logged only.');
}

export const sendSmsNotification = async ({ to, message }: SmsPayload) => {
  if (!twilioClient) {
    console.log(`📱 [SMS LOG] To: ${to}, Message: ${message}`);
    return;
  }

  try {
    const fromNumber = process.env.TWILIO_PHONE_NUMBER;
    if (!fromNumber) {
      console.warn('⚠️ TWILIO_PHONE_NUMBER is not set. SMS will be logged instead of sent.');
      console.log(`📱 [SMS LOG] To: ${to}, Message: ${message}`);
      return;
    }

    const result = await twilioClient.messages.create({
      body: message,
      from: fromNumber,
      to,
    });

    console.log(`📱 SMS sent: SID=${result.sid}, To=${to}`);
  } catch (err) {
    console.error('❌ Failed to send SMS:', err);
  }
};

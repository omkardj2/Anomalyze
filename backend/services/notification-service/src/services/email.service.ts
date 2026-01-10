// src/services/email.service.ts
import nodemailer, { Transporter } from 'nodemailer';

interface EmailPayload {
  to: string;
  subject: string;
  body: string;
}

let transporter: Transporter | null = null;

// Initialize transporter if SMTP credentials are available
if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT) || 587,
    secure: process.env.SMTP_SECURE === 'true', // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });
} else {
  console.warn('⚠️ SMTP credentials not found. Emails will be logged only.');
}

export const sendEmailNotification = async ({ to, subject, body }: EmailPayload) => {
  if (!transporter) {
    console.log(`📧 [EMAIL LOG] To: ${to}, Subject: ${subject}, Body: ${body}`);
    return;
  }

  try {
    const fromAddress = process.env.EMAIL_FROM || 'no-reply@example.com';

    const info = await transporter.sendMail({
      from: fromAddress,
      to,
      subject,
      text: body,
    });

    console.log(`📧 Email sent: MessageId=${info.messageId}, To=${to}`);
  } catch (err) {
    console.error('❌ Failed to send email:', err);
  }
};
    
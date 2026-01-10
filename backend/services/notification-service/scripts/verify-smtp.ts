
import dotenv from 'dotenv';
import { sendEmailNotification } from '../src/services/email.service';

// Load env vars
dotenv.config();

async function main() {
  const testEmail = process.argv[2] || 'test@example.com';
  console.log(`📧 Attempting to send test email to: ${testEmail}`);
  console.log(`Using SMTP Host: ${process.env.SMTP_HOST}`);

  try {
    await sendEmailNotification({
      to: testEmail,
      subject: 'Anomalyze SMTP Test',
      body: 'If you are receiving this, your SMTP credentials are correctly configured!'
    });
    console.log('✅ Test email sent successfully!');
  } catch (error: any) {
    console.error('❌ Failed to send test email:', error.message || error);
    process.exit(1);
  }
}

main();

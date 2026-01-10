import { Router } from 'express';
import { sendEmailNotification } from '../services/email.service';
import { sendSmsNotification } from '../services/sms.service';
import { sendWebhookNotification } from '../services/webhook.service';

const router = Router();

// Test Email
router.post('/v1/notifications/test/email', async (req, res) => {
    const { to, subject, body } = req.body;
    await sendEmailNotification({ to, subject, body });
    res.json({ success: true, message: 'Test email sent (logged)' });
});

// Test SMS
router.post('/v1/notifications/test/sms', async (req, res) => {
    const { to, message } = req.body;
    await sendSmsNotification({ to, message });
    res.json({ success: true, message: 'Test SMS sent (logged)' });
});

router.post('/v1/notifications/test/webhook', async (req, res) => {
  const { url, data } = req.body;

  if (!url || !data) {
    return res.status(400).json({
      success: false,
      message: 'url and data are required',
    });
  }

  await sendWebhookNotification({
    url,
    data,
    secret: process.env.WEBHOOK_SIGNING_SECRET,
  });

  res.json({
    success: true,
    message: 'Test webhook sent',
  });
});

export default router;

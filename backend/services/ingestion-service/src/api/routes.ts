import { Router } from 'express';
import multer from 'multer';

// Configure upload
const upload = multer({ dest: process.env.UPLOAD_DIR || 'uploads/' });

const router = Router();

// 1. Real-time Transaction Endpoint
router.post('/transactions', async (req, res) => {
    // TODO: Validate input with Zod
    // TODO: Send to Kafka 'transactions' topic
    res.status(202).json({ status: 'accepted', message: 'Transaction received' });
});

// 2. Batch CSV Upload Endpoint
router.post('/transactions/batch', upload.single('file'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No CSV file provided' });
    }

    // TODO: Validate file type (text/csv)
    // TODO: Add job to BullMQ 'csv-processing' queue
    // TODO: Return Job ID

    res.status(202).json({
        status: 'processing',
        jobId: 'job_' + Date.now(),
        message: 'File uploaded, processing started'
    });
});

export default router;

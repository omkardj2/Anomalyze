import { Request, Response } from 'express';
import { Webhook } from 'svix';
import { query } from '../config/db';
import { WebhookEvent } from '@clerk/clerk-sdk-node';

export const handleClerkWebhook = async (req: Request, res: Response) => {
    const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

    if (!WEBHOOK_SECRET) {
        throw new Error('Please add CLERK_WEBHOOK_SECRET from Clerk Dashboard to .env');
    }

    // Get the headers
    const svix_id = req.headers["svix-id"] as string;
    const svix_timestamp = req.headers["svix-timestamp"] as string;
    const svix_signature = req.headers["svix-signature"] as string;

    // If there are no headers, error out
    if (!svix_id || !svix_timestamp || !svix_signature) {
        return res.status(400).send('Error occured -- no svix headers');
    }

    // Get the body
    const body = JSON.stringify(req.body);

    // Create a new Svix instance with your secret.
    const wh = new Webhook(WEBHOOK_SECRET);

    let evt: WebhookEvent;

    // Verify the payload with the headers
    try {
        evt = wh.verify(body, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        }) as WebhookEvent;
    } catch (err) {
        console.error('Error verifying webhook:', err);
        return res.status(400).send('Error occured');
    }

    const { id } = evt.data;
    const eventType = evt.type;

    console.log(`Webhook with and ID of ${id} and type of ${eventType}`);
    console.log('Webhook body:', body);

    try {
        if (eventType === 'user.created' || eventType === 'user.updated') {
            const { id, email_addresses, first_name, last_name } = evt.data;
            const email = email_addresses[0]?.email_address;
            const name = `${first_name || ''} ${last_name || ''}`.trim();

            const upsertQuery = `
        INSERT INTO users (id, email, name, "updatedAt")
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = EXCLUDED.name,
        "updatedAt" = NOW();
      `;

            await query(upsertQuery, [id, email, name]);
            console.log(`User ${id} upserted successfully`);
        }

        if (eventType === 'user.deleted') {
            const { id } = evt.data;
            const deleteQuery = 'DELETE FROM users WHERE id = $1';
            await query(deleteQuery, [id]);
            console.log(`User ${id} deleted successfully`);
        }

        return res.status(200).json({ success: true, message: 'Webhook received' });
    } catch (err) {
        console.error('Error processing webhook:', err);
        return res.status(500).json({ success: false, message: 'Error processing webhook' });
    }
};

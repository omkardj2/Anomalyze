"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleClerkWebhook = void 0;
const svix_1 = require("svix");
const db_1 = require("../config/db");
const handleClerkWebhook = async (req, res) => {
    const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;
    if (!WEBHOOK_SECRET) {
        throw new Error('Please add CLERK_WEBHOOK_SECRET from Clerk Dashboard to .env');
    }
    // Get the headers
    const svix_id = req.headers["svix-id"];
    const svix_timestamp = req.headers["svix-timestamp"];
    const svix_signature = req.headers["svix-signature"];
    // If there are no headers, error out
    if (!svix_id || !svix_timestamp || !svix_signature) {
        return res.status(400).send('Error occured -- no svix headers');
    }
    // Get the body
    const body = JSON.stringify(req.body);
    // Create a new Svix instance with your secret.
    const wh = new svix_1.Webhook(WEBHOOK_SECRET);
    let evt;
    // Verify the payload with the headers
    try {
        evt = wh.verify(body, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        });
    }
    catch (err) {
        console.error('Error verifying webhook:', err);
        return res.status(400).send('Error occured');
    }
    const { id } = evt.data;
    const eventType = evt.type;
    console.log(`Webhook with and ID of ${id} and type of ${eventType}`);
    console.log('Webhook body:', body);
    try {
        if (eventType === 'user.created' || eventType === 'user.updated') {
            const { id, email_addresses, first_name, last_name, image_url } = evt.data;
            const email = email_addresses[0]?.email_address;
            const upsertQuery = `
        INSERT INTO users (clerk_id, email, first_name, last_name, image_url)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (clerk_id) DO UPDATE SET
        email = EXCLUDED.email,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        image_url = EXCLUDED.image_url;
      `;
            await (0, db_1.query)(upsertQuery, [id, email, first_name, last_name, image_url]);
            console.log(`User ${id} upserted successfully`);
        }
        if (eventType === 'user.deleted') {
            const { id } = evt.data;
            const deleteQuery = 'DELETE FROM users WHERE clerk_id = $1';
            await (0, db_1.query)(deleteQuery, [id]);
            console.log(`User ${id} deleted successfully`);
        }
        return res.status(200).json({ success: true, message: 'Webhook received' });
    }
    catch (err) {
        console.error('Error processing webhook:', err);
        return res.status(500).json({ success: false, message: 'Error processing webhook' });
    }
};
exports.handleClerkWebhook = handleClerkWebhook;

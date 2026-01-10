import { Request, Response } from 'express';
import { query } from '../config/db';

export const getMe = async (req: Request, res: Response) => {
    try {
        const userId = req.auth.userId;

        if (!userId) {
            return res.status(401).json({ error: 'Unauthorized' });
        }

        const start = Date.now();
        const result = await query('SELECT * FROM users WHERE id = $1', [userId]);

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User not found in local database (sync pending?)' });
        }

        res.json(result.rows[0]);
    } catch (error) {
        console.error('Error fetching user profile:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
};

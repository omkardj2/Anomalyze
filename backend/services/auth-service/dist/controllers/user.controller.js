"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getMe = void 0;
const db_1 = require("../config/db");
const getMe = async (req, res) => {
    try {
        const userId = req.auth.userId;
        if (!userId) {
            return res.status(401).json({ error: 'Unauthorized' });
        }
        const start = Date.now();
        const result = await (0, db_1.query)('SELECT * FROM users WHERE clerk_id = $1', [userId]);
        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User not found in local database (sync pending?)' });
        }
        res.json(result.rows[0]);
    }
    catch (error) {
        console.error('Error fetching user profile:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
};
exports.getMe = getMe;

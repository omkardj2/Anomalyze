import { Pool, QueryResult } from 'pg';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config();

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
});

pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
    process.exit(-1);
});

export const query = async (text: string, params?: any[]): Promise<QueryResult> => {
    const start = Date.now();
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('executed query', { text, duration, rows: res.rowCount });
    return res;
};

export const connectDB = async () => {
    try {
        const client = await pool.connect();
        console.log('✅ Connected to PostgreSQL');
        client.release();
    } catch (err) {
        console.error('❌ Database connection failed:', err);
        process.exit(1);
    }
};

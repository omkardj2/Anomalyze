"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.connectDB = exports.query = void 0;
const pg_1 = require("pg");
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = __importDefault(require("path"));
dotenv_1.default.config({ path: path_1.default.resolve(__dirname, '../../.env') });
const pool = new pg_1.Pool({
    connectionString: process.env.DATABASE_URL,
});
pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
    process.exit(-1);
});
const query = async (text, params) => {
    const start = Date.now();
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('executed query', { text, duration, rows: res.rowCount });
    return res;
};
exports.query = query;
const connectDB = async () => {
    try {
        const client = await pool.connect();
        console.log('✅ Connected to PostgreSQL');
        client.release();
    }
    catch (err) {
        console.error('❌ Database connection failed:', err);
        process.exit(1);
    }
};
exports.connectDB = connectDB;

import request from 'supertest';
import app from '../src/app';

describe('Ingestion Service Health Check', () => {
    it('should return 200 OK', async () => {
        const res = await request(app).get('/health');
        expect(res.status).toBe(200);
        expect(res.body).toHaveProperty('status', 'ok');
        expect(res.body).toHaveProperty('service', 'ingestion-service');
    });
});

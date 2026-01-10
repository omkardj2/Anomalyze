import { Request, Response, NextFunction } from 'express';
import { ClerkExpressWithAuth } from '@clerk/clerk-sdk-node';

// This extends the Express Request interface to include Clerk's auth property
declare global {
    namespace Express {
        interface Request {
            auth: {
                userId: string | null;
                sessionId: string | null;
                getToken: () => Promise<string | null>;
            };
        }
    }
}

// Wrapper to use clerk middleware
export const requireAuth = (req: Request, res: Response, next: NextFunction) => {
    ClerkExpressWithAuth()(req, res, (err: any) => {
        if (err) {
            console.error('Clerk Middleware Error:', err);
            return res.status(401).json({ error: 'Unauthenticated' });
        }

        if (!req.auth.userId) {
            return res.status(401).json({ error: 'Unauthenticated' });
        }
        next();
    });
};

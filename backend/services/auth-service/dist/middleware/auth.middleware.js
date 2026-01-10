"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.requireAuth = void 0;
const clerk_sdk_node_1 = require("@clerk/clerk-sdk-node");
// Wrapper to use clerk middleware
const requireAuth = (req, res, next) => {
    (0, clerk_sdk_node_1.ClerkExpressWithAuth)()(req, res, (err) => {
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
exports.requireAuth = requireAuth;

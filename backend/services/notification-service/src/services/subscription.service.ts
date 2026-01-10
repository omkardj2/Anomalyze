
import { PrismaClient, SubscriptionPlan, Severity } from '@prisma/client';

const prisma = new PrismaClient();

// Defined in schema.prisma:
// enum SubscriptionPlan {
//   FREE
//   BASIC
//   PRO
// }

interface UserContext {
    userId: string;
    email: string | null;
    phone: string | null;
    plan: SubscriptionPlan;
    features: any; // JSON
    settings: {
        emailEnabled: boolean;
        phoneEnabled: boolean;
        minSeverityForCall: Severity;
    };
}

/**
 * Fetches the user's current subscription context and notification settings.
 */
export const getUserContext = async (userId: string): Promise<UserContext | null> => {
    try {
        const user = await prisma.user.findUnique({
            where: { id: userId },
            include: {
                subscription: true,
                notificationSettings: true,
            },
        });

        if (!user) return null;

        return {
            userId: user.id,
            email: user.email,
            phone: user.notificationSettings?.phoneNumber || null,
            plan: user.subscription?.plan || 'FREE',
            features: user.subscription?.features || {},
            settings: {
                emailEnabled: user.notificationSettings?.emailEnabled ?? true,
                phoneEnabled: user.notificationSettings?.phoneEnabled ?? false,
                minSeverityForCall: user.notificationSettings?.minSeverityForCall || 'CRITICAL',
            },
        };
    } catch (err) {
        console.error(`❌ DB Error fetching user context for ${userId}:`, err);
        return null;
    }
};

/**
 * Determines if a notification should be sent based on subscription tier and user preferences.
 */
export const canSendNotification = (
    context: UserContext,
    channel: 'EMAIL' | 'SMS' | 'VOICE',
    severity: Severity
): boolean => {
    const { plan, settings, features } = context;

    if (channel === 'EMAIL') {
        // Email is available for all plans, if enabled by user
        return settings.emailEnabled;
    }

    if (channel === 'SMS') {
        // SMS Requires PRO plan OR specific feature flag
        // Also requires user to enable it
        if (!settings.phoneEnabled) return false;

        // Check Plan or Features
        if (plan === 'PRO') return true;
        if (features && features.sms === true) return true;

        return false; // FREE/BASIC don't get SMS by default
    }

    if (channel === 'VOICE') {
        // Voice Requires PRO plan AND Critical Severity
        if (plan !== 'PRO') return false;

        // Check severity threshold (defaults to CRITICAL)
        // Simple check: Only CRITICAL triggers call
        if (severity !== 'CRITICAL') return false;

        return true;
    }

    return false;
};

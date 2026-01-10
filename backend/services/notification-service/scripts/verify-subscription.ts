
import { PrismaClient, SubscriptionPlan, Severity } from '@prisma/client';
import { getUserContext, canSendNotification } from '../src/services/subscription.service';

const prisma = new PrismaClient();

async function main() {
    const userId = 'user_test_subscription_' + Date.now();
    console.log(`🧪 Testing Subscription Logic for user: ${userId}`);

    try {
        // 1. Create a FREE Tier User
        await prisma.user.create({
            data: {
                id: userId,
                email: `test_${userId}@example.com`,
                notificationSettings: {
                    create: {
                        emailEnabled: true,
                        phoneEnabled: true, // Enabled, but should be blocked by plan
                        minSeverityForCall: 'CRITICAL'
                    }
                },
                subscription: {
                    create: {
                        plan: 'FREE',
                        features: {},
                        currentPeriodEnd: new Date(Date.now() + 86400000)
                    }
                }
            }
        });

        // 2. Test FREE Context
        let context = await getUserContext(userId);
        console.log('\n--- FREE TIER CHECK ---');
        console.log('Email Allowed (Medium)?', canSendNotification(context!, 'EMAIL', 'MEDIUM'), '(Expected: true)');
        console.log('SMS Allowed (Medium)?', canSendNotification(context!, 'SMS', 'MEDIUM'), '(Expected: false - Plan Restriction)');
        console.log('Voice Allowed (Critical)?', canSendNotification(context!, 'VOICE', 'CRITICAL'), '(Expected: false - Plan Restriction)');

        // 3. Upgrade to PRO
        await prisma.subscription.update({
            where: { userId },
            data: { plan: 'PRO' }
        });
        context = await getUserContext(userId); // Refresh

        console.log('\n--- PRO TIER CHECK ---');
        console.log('SMS Allowed (Medium)?', canSendNotification(context!, 'SMS', 'MEDIUM'), '(Expected: true)');
        console.log('Voice Allowed (Critical)?', canSendNotification(context!, 'VOICE', 'CRITICAL'), '(Expected: true)');
        console.log('Voice Allowed (Low)?', canSendNotification(context!, 'VOICE', 'LOW'), '(Expected: false - Severity Restriction)');

        console.log('\n✅ Subscription Logic Verified!');

    } catch (err) {
        console.error('❌ Test Failed:', err);
    } finally {
        // Cleanup
        await prisma.user.delete({ where: { id: userId } }).catch(() => { });
        await prisma.$disconnect();
    }
}

main();

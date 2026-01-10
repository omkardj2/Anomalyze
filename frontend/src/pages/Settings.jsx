import { Header } from '../components/layout/Header';
import { motion } from 'framer-motion';
import { Check, X, CreditCard, Shield } from 'lucide-react';
import { cn } from '../lib/utils';
import { useState } from 'react';

// TODO: Fetch available plans from backend (GET /subscriptions/plans)
const plans = [
  {
    name: 'Starter',
    price: 'Free',
    features: [
      { name: 'Batch Ingestion', included: true },
      { name: 'Basic Anomaly Detection', included: true },
      { name: 'Real-time Processing', included: false },
      { name: 'Advanced ML Models', included: false },
      { name: 'Email Alerts', included: false },
    ]
  },
  {
    name: 'Advanced',
    price: '$49/mo',
    current: true,
    features: [
      { name: 'Batch Ingestion', included: true },
      { name: 'Basic Anomaly Detection', included: true },
      { name: 'Real-time Processing', included: true },
      { name: 'Advanced ML Models', included: true },
      { name: 'Email Alerts', included: true },
    ]
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    features: [
      { name: 'Batch Ingestion', included: true },
      { name: 'Basic Anomaly Detection', included: true },
      { name: 'Real-time Processing', included: true },
      { name: 'Advanced ML Models', included: true },
      { name: 'Email Alerts', included: true },
    ]
  }
];

export default function Settings() {
  const [billingCycle, setBillingCycle] = useState('monthly');

  return (
    <div>
      <Header title="Settings & Entitlements" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* User Profile Card */}
        <div className="glass-panel p-6 rounded-2xl flex items-center gap-6">
          <div className="h-20 w-20 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 border-2 border-white/20" />
          <div>
            <h3 className="text-xl font-bold text-white">Deepak</h3>
            <p className="text-gray-400">deepak@anomalyze.com</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">Active</span>
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Advanced Plan</span>
            </div>
          </div>
        </div>

        {/* Usage Stats (Quick View) */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-center">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Monthly Transaction Limit</span>
            <span className="text-sm font-medium text-white">12,450 / 50,000</span>
          </div>
          <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden mb-4">
            <div className="h-full bg-indigo-500 w-[25%]" />
          </div>
          <button className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors self-start">
            View Usage Details
          </button>
        </div>
      </div>

      <h3 className="text-xl font-bold text-white mb-6">Subscription Plans</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
              "glass-panel p-8 rounded-2xl border-2 relative overflow-hidden transition-all duration-300",
              plan.current
                ? "border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.2)]"
                : "border-transparent hover:border-white/10"
            )}
          >
            {plan.current && (
              <div className="absolute top-0 right-0 px-3 py-1 bg-indigo-500 text-white text-xs font-bold rounded-bl-xl">
                CURRENT
              </div>
            )}

            <h4 className="text-lg font-medium text-gray-300 mb-2">{plan.name}</h4>
            <div className="flex items-end gap-1 mb-6">
              <span className="text-3xl font-bold text-white">{plan.price}</span>
              {plan.price !== 'Free' && plan.price !== 'Custom' && <span className="text-sm text-gray-500 mb-1">/mo</span>}
            </div>

            <div className="space-y-4 mb-8">
              {plan.features.map((feature) => (
                <div key={feature.name} className="flex items-center gap-3">
                  <div className={cn(
                    "flex-shrink-0 h-5 w-5 rounded-full flex items-center justify-center",
                    feature.included ? "bg-green-500/10 text-green-400" : "bg-white/5 text-gray-600"
                  )}>
                    {feature.included ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                  </div>
                  <span className={cn(
                    "text-sm",
                    feature.included ? "text-gray-300" : "text-gray-500 line-through"
                  )}>
                    {feature.name}
                  </span>
                </div>
              ))}
            </div>

            <button
              disabled={plan.current}
              className={cn(
                "w-full py-3 rounded-xl text-sm font-medium transition-all duration-300",
                plan.current
                  ? "bg-white/5 text-gray-400 cursor-default"
                  : "bg-indigo-500 text-white hover:bg-indigo-600 shadow-lg shadow-indigo-500/20"
              )}
            >
              {plan.current ? 'Current Plan' : 'Upgrade'}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

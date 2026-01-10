import { Header } from '../components/layout/Header';
import { StatsCard } from '../components/dashboard/StatsCard';
import { Activity, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { motion } from 'framer-motion';

// TODO: Replace with real chart data from API (GET /stats/anomalies?range=24h)
const data = [
  { name: '00:00', value: 400, anomalies: 2 },
  { name: '04:00', value: 300, anomalies: 1 },
  { name: '08:00', value: 600, anomalies: 5 },
  { name: '12:00', value: 900, anomalies: 8 },
  { name: '16:00', value: 1200, anomalies: 12 },
  { name: '20:00', value: 800, anomalies: 4 },
  { name: '23:59', value: 500, anomalies: 2 },
];

export default function Dashboard() {
  return (
    <div>
      <Header title="Dashboard" />

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* TODO: Fetch real-time stats from backend (GET /stats/overview) */}
        <StatsCard
          title="Total Transactions"
          value="12,450"
          change="+12.5%"
          trend="up"
          icon={Activity}
        />
        <StatsCard
          title="Anomalies Detected"
          value="42"
          change="+5.2%"
          trend="down"
          icon={AlertTriangle}
        />
        <StatsCard
          title="System Status"
          value="99.9%"
          change="Operational"
          trend="up"
          icon={CheckCircle}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Chart Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 glass-panel p-6 rounded-2xl"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Anomaly Trends</h3>
            <div className="flex gap-2">
              <button className="px-3 py-1 rounded-lg bg-white/5 text-xs text-gray-400 hover:text-white transition-colors">24h</button>
              <button className="px-3 py-1 rounded-lg bg-white/5 text-xs text-gray-400 hover:text-white transition-colors">7d</button>
            </div>
          </div>

          <div className="h-[300px] w-full min-h-[300px]">
            <ResponsiveContainer width="99%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorAnomalies" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#64748b' }} axisLine={false} />
                <YAxis stroke="#64748b" tick={{ fill: '#64748b' }} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#141522', borderColor: '#1e293b', borderRadius: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="value" stroke="#6366f1" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
                <Area type="monotone" dataKey="anomalies" stroke="#22d3ee" fillOpacity={1} fill="url(#colorAnomalies)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Recent Activity Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-panel p-6 rounded-2xl"
        >
          <h3 className="text-lg font-semibold text-white mb-6">Recent Activity</h3>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors group cursor-pointer">
                <div className="h-10 w-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 group-hover:bg-red-500/20 transition-colors">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-200">High Velocity Alert</h4>
                  <p className="text-xs text-gray-400">Transaction ID #49283 detected</p>
                </div>
                <span className="text-xs text-gray-500">2m ago</span>
              </div>
            ))}
          </div>

          <button className="w-full mt-6 py-3 rounded-xl border border-white/10 text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all">
            {/* TODO: Link to full activity log page */}
            View All Activity
          </button>
        </motion.div>
      </div>
    </div>
  );
}

import { Header } from '../components/layout/Header';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, Search, Filter, MoreHorizontal } from 'lucide-react';
import { cn } from '../lib/utils';
import { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

// TODO: Replace static data with API call (GET /anomalies) or WebSocket subscription
// const { data: anomaliesData } = useQuery({ queryKey: ['anomalies'], queryFn: fetchAnomalies });
const anomaliesData = [
  { id: 'TXN-7829', user: 'user_42', score: 0.98, type: 'Velocity', severity: 'critical', timestamp: '2025-01-10T14:20:00', status: 'Pending' },
  { id: 'TXN-7830', user: 'user_19', score: 0.85, type: 'Amount Spike', severity: 'warning', timestamp: '2025-01-10T14:15:00', status: 'Investigating' },
  { id: 'TXN-7831', user: 'user_88', score: 0.92, type: 'Geo-Fencing', severity: 'critical', timestamp: '2025-01-10T14:10:00', status: 'Pending' },
  { id: 'TXN-7832', user: 'user_05', score: 0.72, type: 'Pattern', severity: 'low', timestamp: '2025-01-10T14:05:00', status: 'Resolved' },
  { id: 'TXN-7833', user: 'user_42', score: 0.99, type: 'Velocity', severity: 'critical', timestamp: '2025-01-10T14:00:00', status: 'Resolved' },
  { id: 'TXN-7834', user: 'user_99', score: 0.88, type: 'Amount Spike', severity: 'warning', timestamp: '2025-01-10T13:55:00', status: 'Pending' },
];

export default function Anomalies() {
  const [filter, setFilter] = useState('All');
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('q')?.toLowerCase() || '';

  const filteredData = useMemo(() => {
    return anomaliesData.filter(item => {
      const matchesFilter = filter === 'All' || item.severity.toLowerCase() === filter.toLowerCase() || item.status === filter;
      const matchesSearch = item.id.toLowerCase().includes(searchQuery) ||
        item.user.toLowerCase().includes(searchQuery) ||
        item.type.toLowerCase().includes(searchQuery);
      return matchesFilter && matchesSearch;
    });
  }, [filter, searchQuery]);

  return (
    <div>
      <Header title="Anomalies Explorer" />

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-2 bg-[#1A1D2D]/50 p-1 rounded-xl border border-white/10">
          {['All', 'Critical', 'Warning', 'Resolved'].map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={cn(
                "px-4 py-1.5 rounded-lg text-sm font-medium transition-all",
                filter === tab
                  ? "bg-indigo-500 text-white shadow-lg"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm text-gray-300 hover:bg-white/10 transition-colors">
            <Filter className="h-4 w-4" />
            Filter
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/20">
            {/* TODO: Implement CSV export functionality (GET /anomalies/export) */}
            Export CSV
          </button>
        </div>
      </div>

      {/* Data Grid */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        <div className="grid grid-cols-7 gap-4 p-4 border-b border-white/10 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          <div className="col-span-1">Transaction ID</div>
          <div className="col-span-1">User</div>
          <div className="col-span-1">Type</div>
          <div className="col-span-1">Score</div>
          <div className="col-span-1">Severity</div>
          <div className="col-span-1">Status</div>
          <div className="col-span-1 text-right">Actions</div>
        </div>

        <div>
          {filteredData.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No anomalies found matching your criteria.
            </div>
          ) : (
            filteredData.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="grid grid-cols-7 gap-4 p-4 border-b border-white/5 hover:bg-white/5 transition-colors items-center group cursor-pointer"
              >
                <div className="col-span-1 font-medium text-white">{item.id}</div>
                <div className="col-span-1 text-gray-400 text-sm">{item.user}</div>
                <div className="col-span-1">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#1A1D2D] border border-white/5 text-xs text-gray-300">
                    {item.type}
                  </span>
                </div>
                <div className="col-span-1">
                  <div className="w-full max-w-[100px] h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full",
                        item.score > 0.9 ? "bg-red-500" : item.score > 0.7 ? "bg-yellow-500" : "bg-green-500"
                      )}
                      style={{ width: `${item.score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 mt-1 block">{Math.round(item.score * 100)}%</span>
                </div>
                <div className="col-span-1">
                  <span className={cn(
                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                    item.severity === 'critical' ? "bg-red-500/10 text-red-500 border-red-500/20" :
                      item.severity === 'warning' ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" :
                        "bg-green-500/10 text-green-500 border-green-500/20"
                  )}>
                    {item.severity === 'critical' && <AlertTriangle className="h-3 w-3" />}
                    {item.severity.charAt(0).toUpperCase() + item.severity.slice(1)}
                  </span>
                </div>
                <div className="col-span-1">
                  <span className={cn(
                    "text-xs px-2 py-1 rounded-lg",
                    item.status === 'Resolved' ? "text-green-400 bg-green-400/10" : "text-gray-400 bg-white/5"
                  )}>
                    {item.status}
                  </span>
                </div>
                <div className="col-span-1 flex justify-end">
                  <button className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

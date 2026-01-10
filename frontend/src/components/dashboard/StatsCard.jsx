import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export function StatsCard({ title, value, change, icon: Icon, trend }) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
    >
      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <Icon className="h-24 w-24" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-cyan-400">
            <Icon className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        </div>

        <div className="flex items-end gap-3">
          <h4 className="text-3xl font-bold text-white tracking-tight">{value}</h4>
          {change && (
            <span className={cn(
              "text-xs font-bold px-2 py-1 rounded-full mb-1 border",
              trend === 'up'
                ? "bg-green-500/10 text-green-400 border-green-500/20"
                : "bg-red-500/10 text-red-400 border-red-500/20"
            )}>
              {change}
            </span>
          )}
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.div>
  );
}

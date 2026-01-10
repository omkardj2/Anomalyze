import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, AlertOctagon, Upload, Settings, User } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: AlertOctagon, label: 'Anomalies', path: '/anomalies' },
  { icon: Upload, label: 'Ingestion', path: '/upload' },
  { icon: Settings, label: 'Settings', path: '/settings' },
  { icon: User, label: 'Profile', path: '/profile' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 glass-card m-4 !rounded-2xl border-r-0 z-50 flex flex-col items-center py-8">
      <div className="mb-10 w-full px-6 flex items-center gap-3">
        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-cyan-400 blur-[2px]" />
        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 tracking-tight">
          Anomalyze
        </h1>
      </div>

      <nav className="w-full px-4 space-y-2 flex-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 hover:bg-white/5"
            >
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-cyan-500/10 rounded-xl border border-indigo-500/30"
                  initial={false}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}

              <Icon
                className={cn(
                  "h-5 w-5 z-10 transition-colors duration-300",
                  isActive ? "text-cyan-400" : "text-gray-400 group-hover:text-gray-200"
                )}
              />
              <span
                className={cn(
                  "font-medium z-10 transition-colors duration-300",
                  isActive ? "text-white" : "text-gray-400 group-hover:text-gray-200"
                )}
              >
                {item.label}
              </span>

              {isActive && (
                <div className="absolute right-2 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="w-full px-4">
        <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border border-indigo-500/20">
          <h4 className="text-sm font-semibold text-white mb-1">Status</h4>
          <div className="flex items-center gap-2 text-xs text-green-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            System Operational
          </div>
        </div>
      </div>
    </aside>
  );
}

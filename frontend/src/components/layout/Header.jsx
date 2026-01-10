import { Bell, Search, X } from 'lucide-react';
import { useNotifications } from '../../contexts/NotificationContext';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';
import { useSearchParams } from 'react-router-dom';

export function Header({ title }) {
  const { notifications, unreadCount, markAllAsRead } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState(searchParams.get('q') || '');

  const handleSearch = (e) => {
    const term = e.target.value;
    setSearchTerm(term);

    // Update URL params
    const newParams = new URLSearchParams(searchParams);
    if (term) {
      newParams.set('q', term);
      // TODO: Debounce and fetch search results from backend (GET /search?q=...)
    } else {
      newParams.delete('q');
    }
    setSearchParams(newParams);
  };

  return (
    <header className="flex items-center justify-between mb-8 relative">
      <h2 className="text-3xl font-bold tracking-tight text-white">{title}</h2>

      <div className="flex items-center gap-4">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400 group-focus-within:text-cyan-400 transition-colors" />
          </div>
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={handleSearch}
            className="pl-10 pr-4 py-2 bg-[#1A1D2D]/50 border border-white/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 w-64 transition-all"
          />
        </div>

        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              if (!showNotifications && unreadCount > 0) markAllAsRead();
            }}
            className="relative p-2 rounded-xl hover:bg-white/5 transition-colors group"
          >
            <Bell className="h-5 w-5 text-gray-400 group-hover:text-cyan-400 transition-colors" />
            {unreadCount > 0 && (
              <span className="absolute top-2 right-2 h-2.5 w-2.5 rounded-full bg-red-500 border-2 border-[#0B0C15] animate-pulse" />
            )}
          </button>

          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 top-full mt-2 w-96 glass-card border border-white/10 overflow-hidden z-50 origin-top-right"
              >
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
                  <h4 className="font-semibold text-sm">Notifications</h4>
                  <button onClick={() => setShowNotifications(false)} className="text-gray-400 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="max-h-[70vh] overflow-y-auto custom-scrollbar">
                  {notifications.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 text-sm">
                      No new notifications
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div key={n.id} className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors">
                        <div className="flex items-start justify-between mb-1">
                          <span className={cn(
                            "text-xs font-bold px-2 py-0.5 rounded-full border",
                            n.severity === 'critical'
                              ? "bg-red-500/10 text-red-500 border-red-500/20"
                              : "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                          )}>
                            {n.severity.toUpperCase()}
                          </span>
                          <span className="text-[10px] text-gray-500">
                            {n.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <h5 className="text-sm font-medium text-gray-200 mb-0.5">{n.title}</h5>
                        <p className="text-xs text-gray-400 leading-relaxed">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 border border-white/10 ring-2 ring-white/5 cursor-pointer hover:ring-indigo-500/50 transition-all" />
      </div>
    </header>
  );
}

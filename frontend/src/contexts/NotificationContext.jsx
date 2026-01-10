import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

const NotificationContext = createContext(undefined);

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const addNotification = useCallback((notification) => {
    setNotifications((prev) => [notification, ...prev]);
    setUnreadCount((prev) => prev + 1);
  }, []);

  // Simulate receiving real-time notifications
  useEffect(() => {
    // TODO: Replace interval with WebSocket connection (e.g., using socket.io-client or native WebSocket)
    // const socket = new WebSocket('ws://api.anomalyze.com/notifications');
    const interval = setInterval(() => {
      // 10% chance to get a new notification every 10s
      if (Math.random() > 0.9) {
        const newNotification = {
          id: Date.now().toString(),
          title: 'High Velocity Detected',
          message: `User user_${Math.floor(Math.random() * 1000)} exceeded velocity limits.`,
          timestamp: new Date(),
          read: false,
          severity: Math.random() > 0.5 ? 'critical' : 'warning',
        };

        addNotification(newNotification);
        toast.error(newNotification.title, {
          description: newNotification.message,
        });
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [addNotification]);



  const markAllAsRead = () => {
    setNotifications((prev) => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, addNotification, markAllAsRead }}>
      {children}
    </NotificationContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

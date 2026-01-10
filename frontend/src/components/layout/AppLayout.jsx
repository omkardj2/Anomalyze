import { Sidebar } from './Sidebar';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-[#0B0C15] text-white">
      <Sidebar />
      <main className="pl-[280px] pr-8 py-8 min-h-screen">
        <Outlet />
      </main>
      <Toaster theme="dark" position="top-right" />
    </div>
  );
}

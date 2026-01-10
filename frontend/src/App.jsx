import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { NotificationProvider } from './contexts/NotificationContext';
import Dashboard from './pages/Dashboard';
import Anomalies from './pages/Anomalies';
import Upload from './pages/Upload';
import Settings from './pages/Settings';
import Profile from './pages/Profile';

function App() {
  return (
    <BrowserRouter>
      <NotificationProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/anomalies" element={<Anomalies />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </NotificationProvider>
    </BrowserRouter>
  );
}

export default App;

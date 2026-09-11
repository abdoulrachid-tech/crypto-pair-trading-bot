import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import TradesHistory from './pages/TradesHistory';
import Logs from './pages/Logs';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="trades" element={<TradesHistory />} />
            <Route path="logs" element={<Logs />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

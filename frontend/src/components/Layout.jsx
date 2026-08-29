import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>📈 Pair Trading Bot</h1>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/trades">Historique des trades</NavLink>
          <NavLink to="/logs">Logs</NavLink>
        </nav>
        <div style={{ marginTop: 40, fontSize: 12, color: 'var(--text-dim)' }}>
          Connecté : {user?.email}
          <br />
          <button
            onClick={logout}
            style={{
              marginTop: 8, background: 'none', border: '1px solid var(--border)',
              color: 'var(--text-dim)', borderRadius: 6, padding: '6px 10px', cursor: 'pointer', fontSize: 12,
            }}
          >
            Se déconnecter
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

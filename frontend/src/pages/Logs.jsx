import { useEffect, useState } from 'react';
import { botApi } from '../api/client';

const LEVEL_COLORS = {
  info: 'var(--text-dim)',
  warning: 'var(--yellow)',
  error: 'var(--red)',
};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    botApi.getLogs(200).then((res) => {
      setLogs(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Chargement des logs...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Logs du bot</h1>
      <div className="panel">
        {logs.length === 0 ? (
          <div className="empty-state">Aucun log disponible.</div>
        ) : (
          <div style={{ fontFamily: 'monospace', fontSize: 12, lineHeight: 1.7 }}>
            {logs.map((log) => (
              <div key={log._id}>
                <span style={{ color: 'var(--text-dim)' }}>
                  [{new Date(log.createdAt).toLocaleString('fr-FR')}]
                </span>{' '}
                <span style={{ color: LEVEL_COLORS[log.level], fontWeight: 600 }}>
                  {log.level.toUpperCase()}
                </span>{' '}
                {log.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

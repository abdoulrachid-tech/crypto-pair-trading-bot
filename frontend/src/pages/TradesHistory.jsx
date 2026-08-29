import { useEffect, useState } from 'react';
import { botApi } from '../api/client';
import TradeTable from '../components/TradeTable';

const FILTERS = [
  { key: 'all', label: 'Tous' },
  { key: 'winning', label: 'Gagnants' },
  { key: 'losing', label: 'Perdants' },
];

export default function TradesHistory() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    botApi.getTrades(500).then((res) => {
      setTrades(res.data);
      setLoading(false);
    });
  }, []);

  const filtered = trades.filter((t) => {
    if (filter === 'winning') return (t.pnl ?? 0) > 0;
    if (filter === 'losing') return (t.pnl ?? 0) < 0;
    return true;
  });

  if (loading) return <div className="loading">Chargement de l'historique...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>Historique des trades</h1>

      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            style={{
              padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
              border: '1px solid var(--border)',
              background: filter === f.key ? 'var(--accent)' : 'transparent',
              color: filter === f.key ? '#0f172a' : 'var(--text-dim)',
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="panel">
        <TradeTable trades={filtered} />
      </div>
    </div>
  );
}

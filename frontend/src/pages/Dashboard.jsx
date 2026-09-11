import { useEffect, useState, useCallback } from 'react';
import { botApi } from '../api/client';
import StatCards from '../components/StatCards';
import PnlChart from '../components/PnlChart';
import PriceChart from '../components/PriceChart';
import ZScoreChart from '../components/ZScoreChart';
import TradeTable from '../components/TradeTable';

const REFRESH_INTERVAL_MS = 15_000;

export default function Dashboard() {
  const [performance, setPerformance] = useState(null);
  const [status, setStatus] = useState(null);
  const [trades, setTrades] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [perfRes, statusRes, tradesRes, snapshotsRes] = await Promise.all([
        botApi.getPerformance(),
        botApi.getStatus(),
        botApi.getTrades(50),
        botApi.getSnapshots(300),
      ]);
      setPerformance(perfRes.data);
      setStatus(statusRes.data);
      setTrades(tradesRes.data);
      setSnapshots(snapshotsRes.data);
      setError('');
    } catch (err) {
      setError('Impossible de récupérer les données du bot depuis l\'API.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) return <div className="loading">Chargement du dashboard...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>

      {error && <div className="panel" style={{ color: 'var(--red)' }}>{error}</div>}

      {status?.isRunning && status?.meta?.tradingEnabled === false && (
        <div className="panel" style={{ borderColor: '#facc15', color: '#facc15' }}>
          ⏸️ Trading en pause — {status.meta.reason || 'cointégration invalide'}. Les prix continuent d'être suivis ci-dessous.
        </div>
      )}

      <StatCards performance={performance} status={status} />

      <div className="panel">
        <h2>Prix BTC / ETH (mis à jour à chaque cycle du bot)</h2>
        <PriceChart snapshots={snapshots} />
      </div>

      <div className="panel">
        <h2>PnL cumulé</h2>
        <PnlChart equityCurve={performance?.equityCurve} />
      </div>

      <div className="panel">
        <h2>Z-score de la paire (avec seuils de la stratégie)</h2>
        <ZScoreChart trades={trades} snapshots={snapshots} />
      </div>

      <div className="panel">
        <h2>Derniers trades</h2>
        <TradeTable trades={trades.slice(0, 10)} />
      </div>
    </div>
  );
}

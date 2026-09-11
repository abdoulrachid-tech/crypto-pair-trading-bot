import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

/**
 * Évolution des prix des deux actifs de la paire, alimentée par les snapshots
 * remontés par le bot à chaque cycle (voir POST /api/bot/snapshots) —
 * contrairement au Z-score/PnL, ceci bouge en continu, pas seulement aux
 * moments de trade.
 */
export default function PriceChart({ snapshots, symbolA = 'BTC', symbolB = 'ETH' }) {
  if (!snapshots || snapshots.length === 0) {
    return <div className="empty-state">Aucune donnée de prix disponible pour le moment.</div>;
  }

  const data = snapshots.map((s) => ({
    time: new Date(s.recordedAt).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }),
    priceA: Number(s.priceA?.toFixed(2)),
    priceB: Number(s.priceB?.toFixed(2)),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} minTickGap={40} />
        <YAxis yAxisId="a" stroke="#38bdf8" fontSize={11} domain={['auto', 'auto']} />
        <YAxis yAxisId="b" orientation="right" stroke="#facc15" fontSize={11} domain={['auto', 'auto']} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line yAxisId="a" type="monotone" dataKey="priceA" stroke="#38bdf8" strokeWidth={2} dot={false} name={symbolA} />
        <Line yAxisId="b" type="monotone" dataKey="priceB" stroke="#facc15" strokeWidth={2} dot={false} name={symbolB} />
      </LineChart>
    </ResponsiveContainer>
  );
}

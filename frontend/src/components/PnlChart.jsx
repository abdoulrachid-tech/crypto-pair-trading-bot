import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';

/**
 * Mission 14 — "Un graphique représentant le PnL cumulé de votre stratégie au fil du temps."
 */
export default function PnlChart({ equityCurve }) {
  if (!equityCurve || equityCurve.length === 0) {
    return <div className="empty-state">Aucune donnée de PnL disponible pour le moment.</div>;
  }

  const data = equityCurve.map((point) => ({
    time: new Date(point.time).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }),
    equity: Number(point.equity.toFixed(2)),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} minTickGap={40} />
        <YAxis stroke="#94a3b8" fontSize={11} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <Line type="monotone" dataKey="equity" stroke="#38bdf8" strokeWidth={2} dot={false} name="PnL cumulé" />
      </LineChart>
    </ResponsiveContainer>
  );
}

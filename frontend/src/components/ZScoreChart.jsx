import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts';

/**
 * Mission 14 — "Un graphique en ligne du Z-score de votre paire" avec les
 * seuils d'entrée/sortie de la stratégie tracés en surimpression.
 */
export default function ZScoreChart({ trades, snapshots, entryThreshold = 2.0, exitThreshold = 0.5 }) {
  const hasSnapshots = snapshots && snapshots.length > 0;
  const hasTrades = trades && trades.length > 0;

  if (!hasSnapshots && !hasTrades) {
    return <div className="empty-state">Aucun signal enregistré pour le moment.</div>;
  }

  const data = (hasSnapshots
    ? snapshots.map((s) => ({ time: s.recordedAt, zscore: s.zscore }))
    : [...trades].reverse().map((t) => ({ time: t.executedAt, zscore: t.zscore }))
  ).map((p) => ({
    time: new Date(p.time).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }),
    zscore: Number(p.zscore?.toFixed(3)),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} minTickGap={40} />
        <YAxis stroke="#94a3b8" fontSize={11} domain={['auto', 'auto']} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <ReferenceLine y={entryThreshold} stroke="#f87171" strokeDasharray="4 4" label={{ value: 'Entrée +', fill: '#f87171', fontSize: 11 }} />
        <ReferenceLine y={-entryThreshold} stroke="#f87171" strokeDasharray="4 4" label={{ value: 'Entrée -', fill: '#f87171', fontSize: 11 }} />
        <ReferenceLine y={exitThreshold} stroke="#facc15" strokeDasharray="2 2" />
        <ReferenceLine y={-exitThreshold} stroke="#facc15" strokeDasharray="2 2" />
        <ReferenceLine y={0} stroke="#475569" />
        <Line type="monotone" dataKey="zscore" stroke="#38bdf8" strokeWidth={2} dot={false} name="Z-score" />
      </LineChart>
    </ResponsiveContainer>
  );
}

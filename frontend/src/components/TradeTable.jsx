function formatNumber(n, decimals = 2) {
  return n != null ? Number(n).toFixed(decimals) : '—';
}

/**
 * Mission 14 — "Un tableau détaillé affichant : la paire, la date et l'heure
 * d'entrée, le type de trade, les prix d'entrée et de sortie, et le PnL réalisé."
 */
export default function TradeTable({ trades }) {
  if (!trades || trades.length === 0) {
    return <div className="empty-state">Aucun trade enregistré pour le moment.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Paire</th>
          <th>Signal</th>
          <th>Prix A</th>
          <th>Prix B</th>
          <th>Z-score</th>
          <th>PnL</th>
          <th>Mode</th>
        </tr>
      </thead>
      <tbody>
        {trades.map((t) => (
          <tr key={t._id}>
            <td>{new Date(t.executedAt).toLocaleString('fr-FR')}</td>
            <td>{t.symbolA} / {t.symbolB}</td>
            <td><span className={`badge ${t.signal}`}>{t.signal}</span></td>
            <td>{formatNumber(t.priceA)}</td>
            <td>{formatNumber(t.priceB)}</td>
            <td>{formatNumber(t.zscore, 3)}</td>
            <td style={{ color: t.pnl > 0 ? 'var(--green)' : t.pnl < 0 ? 'var(--red)' : undefined }}>
              {t.pnl != null ? formatNumber(t.pnl) : '—'}
            </td>
            <td>{t.mode}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

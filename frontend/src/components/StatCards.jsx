function formatPnl(value) {
  if (value == null) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
}

function formatPct(value) {
  if (value == null) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Mission 14 — "État du bot en temps réel" + "Tableau de bord synthétique".
 * `performance` vient de GET /api/bot/performance, `status` de GET /api/bot/status.
 */
export default function StatCards({ performance, status }) {
  const pnl = performance?.cumulativePnl;
  const pnlClass = pnl == null ? '' : pnl >= 0 ? 'positive' : 'negative';

  return (
    <div className="card-grid">
      <div className="card">
        <div className="label">PnL cumulé</div>
        <div className={`value ${pnlClass}`}>{formatPnl(pnl)}</div>
      </div>
      <div className="card">
        <div className="label">Nombre de trades</div>
        <div className="value">{performance?.nTrades ?? '—'}</div>
      </div>
      <div className="card">
        <div className="label">Taux de réussite</div>
        <div className="value">{formatPct(performance?.winRate)}</div>
      </div>
      <div className="card">
        <div className="label">Max drawdown</div>
        <div className="value negative">{formatPct(performance?.maxDrawdown)}</div>
      </div>
      <div className="card">
        <div className="label">Dernier Z-score</div>
        <div className="value">{status?.lastZscore != null ? status.lastZscore.toFixed(2) : '—'}</div>
      </div>
      <div className="card">
        <div className="label">Statut du bot</div>
        <div className={`value ${status?.isRunning ? 'positive' : 'negative'}`}>
          {status?.isRunning ? 'Actif' : 'Arrêté'}
        </div>
      </div>
    </div>
  );
}

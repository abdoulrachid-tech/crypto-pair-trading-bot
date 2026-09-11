import { useEffect, useState, useCallback } from 'react';
import { botApi } from '../api/client';

function ConfigRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ color: 'var(--text-dim)' }}>{label}</span>
      <span style={{ fontWeight: 600 }}>{value ?? '—'}</span>
    </div>
  );
}

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [processStatus, setProcessStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processError, setProcessError] = useState('');
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [processActionLoading, setProcessActionLoading] = useState(false);

  const loadConfig = useCallback(async () => {
    try {
      const res = await botApi.getConfig();
      setConfig(res.data);
      setError('');
    } catch (err) {
      setError("Impossible de récupérer la configuration depuis l'API.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadProcessStatus = useCallback(async () => {
    try {
      const res = await botApi.getProcessStatus();
      setProcessStatus(res.data);
    } catch (err) {
      // Silencieux : peut arriver si TRADING_BOT_DIR/PYTHON ne sont pas configurés.
    }
  }, []);

  useEffect(() => {
    loadConfig();
    loadProcessStatus();
    const interval = setInterval(() => {
      loadConfig();
      loadProcessStatus();
    }, 15_000);
    return () => clearInterval(interval);
  }, [loadConfig, loadProcessStatus]);

  async function handleStart() {
    setProcessActionLoading(true);
    setProcessError('');
    try {
      const res = await botApi.startProcess();
      setProcessStatus(res.data);
    } catch (err) {
      setProcessError(err.response?.data?.error || 'Impossible de démarrer le bot.');
    } finally {
      setProcessActionLoading(false);
    }
  }

  async function handleStop() {
    setProcessActionLoading(true);
    setProcessError('');
    try {
      const res = await botApi.stopProcess();
      setProcessStatus(res.data);
    } catch (err) {
      setProcessError(err.response?.data?.error || 'Impossible d\'arrêter le bot.');
    } finally {
      setProcessActionLoading(false);
    }
  }

  async function toggleOverride() {
    const currentlyPaused = !!config?.manualOverride?.paused;
    setSaving(true);
    try {
      const res = await botApi.setManualOverride(!currentlyPaused, currentlyPaused ? '' : reason);
      setConfig(res.data);
      setReason('');
    } catch (err) {
      setError("Impossible de mettre à jour le coupe-circuit.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="loading">Chargement de la configuration...</div>;

  const isPaused = !!config?.manualOverride?.paused;
  const hasReportedConfig = !!config?.symbolA;

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Réglages</h1>

      {error && <div className="panel" style={{ color: 'var(--red)' }}>{error}</div>}

      <div className="panel">
        <h2>Contrôle du process (démarrer / arrêter le bot)</h2>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 16 }}>
          Lance ou arrête directement le process Python du bot depuis cette machine.
          Nécessite que <code>TRADING_BOT_DIR</code> et <code>TRADING_BOT_PYTHON</code>
          soient configurés dans <code>backend/.env</code>, et que backend et bot
          tournent sur le même ordinateur (ce qui est le cas en local avec des
          bases de données natives).
        </p>

        {processError && <div style={{ color: 'var(--red)', fontSize: 13, marginBottom: 12 }}>{processError}</div>}

        <div style={{
          padding: 12, borderRadius: 8, marginBottom: 16,
          background: processStatus?.running ? 'rgba(74, 222, 128, 0.1)' : 'rgba(148, 163, 184, 0.1)',
          border: `1px solid ${processStatus?.running ? '#4ade80' : 'var(--border)'}`,
        }}>
          <strong style={{ color: processStatus?.running ? '#4ade80' : 'var(--text-dim)' }}>
            {processStatus?.running ? `● Process actif (PID ${processStatus.pid})` : '○ Process arrêté'}
          </strong>
          {processStatus?.running && processStatus?.startedAt && (
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>
              Démarré à {new Date(processStatus.startedAt).toLocaleString('fr-FR')}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={handleStart}
            disabled={processActionLoading || processStatus?.running}
            style={{
              padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: '#4ade80', color: '#0f172a', fontWeight: 600,
              opacity: processStatus?.running ? 0.5 : 1,
            }}
          >
            {processActionLoading ? '...' : '▶️ Démarrer le bot'}
          </button>
          <button
            onClick={handleStop}
            disabled={processActionLoading || !processStatus?.running}
            style={{
              padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: '#f87171', color: '#0f172a', fontWeight: 600,
              opacity: !processStatus?.running ? 0.5 : 1,
            }}
          >
            {processActionLoading ? '...' : '⏹️ Arrêter le bot'}
          </button>
        </div>
      </div>

      <div className="panel">
        <h2>Coupe-circuit manuel</h2>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 16 }}>
          Indépendant du garde-fou automatique de cointégration : permet de mettre le
          trading en pause depuis l'interface (les prix continuent d'être suivis),
          sans avoir à toucher au serveur. Vérifié par le bot à chaque cycle.
        </p>

        <div style={{
          padding: 12, borderRadius: 8, marginBottom: 16,
          background: isPaused ? 'rgba(250, 204, 21, 0.1)' : 'rgba(74, 222, 128, 0.1)',
          border: `1px solid ${isPaused ? '#facc15' : '#4ade80'}`,
        }}>
          <strong style={{ color: isPaused ? '#facc15' : '#4ade80' }}>
            {isPaused ? '⏸️ Trading en pause (manuel)' : '▶️ Trading autorisé (manuel)'}
          </strong>
          {isPaused && config?.manualOverride?.reason && (
            <div style={{ fontSize: 13, marginTop: 4 }}>Raison : {config.manualOverride.reason}</div>
          )}
          {isPaused && config?.manualOverride?.updatedBy && (
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>
              Mis en pause par : {config.manualOverride.updatedBy}
            </div>
          )}
        </div>

        {!isPaused && (
          <input
            type="text"
            placeholder="Raison de la pause (optionnel)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{
              width: '100%', padding: 10, marginBottom: 12, borderRadius: 8,
              border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)',
            }}
          />
        )}

        <button
          onClick={toggleOverride}
          disabled={saving}
          style={{
            padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: isPaused ? '#4ade80' : '#facc15', color: '#0f172a', fontWeight: 600,
          }}
        >
          {saving ? '...' : isPaused ? 'Réactiver le trading' : 'Mettre le trading en pause'}
        </button>
      </div>

      <div className="panel">
        <h2>Configuration active du bot</h2>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 8 }}>
          Rapportée par le bot Python au démarrage — lecture seule ici. Pour changer
          une de ces valeurs, modifiez <code>trading-bot/.env</code> puis redémarrez le bot.
        </p>

        {!hasReportedConfig ? (
          <div className="empty-state">Le bot n'a pas encore rapporté sa configuration (démarrez-le pour la voir ici).</div>
        ) : (
          <>
            <ConfigRow label="Paire" value={`${config.symbolA} / ${config.symbolB}`} />
            <ConfigRow label="Exchange" value={config.exchangeId} />
            <ConfigRow label="Timeframe" value={config.timeframe} />
            <ConfigRow label="Mode d'exécution" value={config.tradingMode === 'live' ? 'RÉEL' : 'Simulation'} />
            {config.tradingMode === 'live' && (
              <ConfigRow label="Live confirmé (LIVE_TRADING_CONFIRMED)" value={config.liveTradingConfirmed ? 'oui' : 'non — reste en simulation'} />
            )}
            <ConfigRow label="Seuil d'entrée (Z-score)" value={config.zscoreEntry} />
            <ConfigRow label="Seuil de sortie (Z-score)" value={config.zscoreExit} />
            <ConfigRow label="Seuil de stop-loss (Z-score)" value={config.zscoreStoploss} />
            <ConfigRow label="Taille par trade (quote)" value={config.tradeSizeQuote} />
            <ConfigRow label="Intervalle entre cycles" value={config.cycleIntervalSeconds ? `${config.cycleIntervalSeconds}s` : null} />
            <ConfigRow label="Fenêtre d'historique au démarrage" value={config.bootstrapHistoryDays ? `${config.bootstrapHistoryDays} jours` : null} />
            <ConfigRow label="Intervalle de recalibrage" value={config.recalibrationIntervalHours ? `${config.recalibrationIntervalHours}h` : null} />
          </>
        )}
      </div>
    </div>
  );
}

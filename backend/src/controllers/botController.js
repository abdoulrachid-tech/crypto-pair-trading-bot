const BotLog = require('../models/BotLog');
const Trade = require('../models/Trade');
const BotStatus = require('../models/BotStatus');
const MarketSnapshot = require('../models/MarketSnapshot');
const BotConfig = require('../models/BotConfig');
const botProcess = require('../services/botProcess');

// --- Logs -------------------------------------------------------------

async function createLog(req, res) {
  try {
    const { level, message, meta } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Le champ "message" est requis.' });
    }
    const log = await BotLog.create({ level: level || 'info', message, meta: meta || {} });
    return res.status(201).json(log);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la création du log.', details: err.message });
  }
}

async function listLogs(req, res) {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 100, 1000);
    const level = req.query.level;
    const filter = level ? { level } : {};
    const logs = await BotLog.find(filter).sort({ createdAt: -1 }).limit(limit);
    return res.json(logs);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la récupération des logs.', details: err.message });
  }
}

// --- Trades -------------------------------------------------------------

async function createTrade(req, res) {
  try {
    const {
      symbolA, symbolB, signal, priceA, priceB, zscore,
      qtyA, qtyB, pnl, mode, timestamp,
    } = req.body;

    if (!symbolA || !symbolB || !signal || priceA == null || priceB == null) {
      return res.status(400).json({ error: 'Champs requis manquants (symbolA, symbolB, signal, priceA, priceB).' });
    }

    const trade = await Trade.create({
      symbolA, symbolB, signal, priceA, priceB, zscore,
      qtyA, qtyB, pnl, mode,
      executedAt: timestamp ? new Date(timestamp) : new Date(),
    });

    return res.status(201).json(trade);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la création du trade.', details: err.message });
  }
}

async function listTrades(req, res) {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 200, 2000);
    const trades = await Trade.find({}).sort({ executedAt: -1 }).limit(limit);
    return res.json(trades);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la récupération des trades.', details: err.message });
  }
}

// --- Statut / performance -------------------------------------------------------------

async function updateStatus(req, res) {
  try {
    const { botId = 'default', ...update } = req.body;
    const status = await BotStatus.findOneAndUpdate(
      { botId },
      { $set: update },
      { new: true, upsert: true }
    );
    return res.json(status);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la mise à jour du statut.', details: err.message });
  }
}

async function getStatus(req, res) {
  try {
    const botId = req.query.botId || 'default';
    const status = await BotStatus.findOne({ botId });
    return res.json(status || { botId, isRunning: false });
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la récupération du statut.', details: err.message });
  }
}

async function getPerformance(req, res) {
  try {
    const trades = await Trade.find({ signal: 'close' }).sort({ executedAt: 1 });

    let cumulativePnl = 0;
    let peak = 0;
    let maxDrawdown = 0;
    let wins = 0;

    const equityCurve = trades.map((t) => {
      cumulativePnl += t.pnl || 0;
      peak = Math.max(peak, cumulativePnl);
      const drawdown = peak > 0 ? (cumulativePnl - peak) / (peak || 1) : 0;
      maxDrawdown = Math.min(maxDrawdown, drawdown);
      if ((t.pnl || 0) > 0) wins += 1;
      return { time: t.executedAt, equity: cumulativePnl };
    });

    const nTrades = trades.length;
    const winRate = nTrades > 0 ? wins / nTrades : 0;

    return res.json({
      nTrades,
      winRate,
      cumulativePnl,
      maxDrawdown,
      equityCurve,
    });
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors du calcul de la performance.', details: err.message });
  }
}

// --- Snapshots marché/stratégie (un point par cycle, pour des graphes continus) ---

async function createSnapshot(req, res) {
  try {
    const { symbolA, symbolB, priceA, priceB, spread, zscore, beta, timestamp } = req.body;

    if (!symbolA || !symbolB || priceA == null || priceB == null) {
      return res.status(400).json({ error: 'Champs requis manquants (symbolA, symbolB, priceA, priceB).' });
    }

    const snapshot = await MarketSnapshot.create({
      symbolA, symbolB, priceA, priceB, spread, zscore, beta,
      recordedAt: timestamp ? new Date(timestamp) : new Date(),
    });

    return res.status(201).json(snapshot);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la création du snapshot.', details: err.message });
  }
}

async function listSnapshots(req, res) {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 300, 5000);
    const snapshots = await MarketSnapshot.find({}).sort({ recordedAt: -1 }).limit(limit);
    return res.json(snapshots.reverse()); // ordre chronologique croissant, prêt pour un graphique
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la récupération des snapshots.', details: err.message });
  }
}

// --- Configuration du bot (paramètres actifs + coupe-circuit manuel) ---

async function reportConfig(req, res) {
  try {
    const { botId = 'default', ...activeParams } = req.body;
    // On ne laisse jamais le bot écraser le coupe-circuit manuel en rapportant sa config.
    delete activeParams.manualOverride;
    const config = await BotConfig.findOneAndUpdate(
      { botId },
      { $set: activeParams },
      { new: true, upsert: true }
    );
    return res.json(config);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la mise à jour de la configuration.', details: err.message });
  }
}

async function getConfig(req, res) {
  try {
    const botId = req.query.botId || 'default';
    const config = await BotConfig.findOne({ botId });
    return res.json(config || { botId, manualOverride: { paused: false, reason: '' } });
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la récupération de la configuration.', details: err.message });
  }
}

async function setManualOverride(req, res) {
  try {
    const { botId = 'default', paused, reason = '' } = req.body;
    if (typeof paused !== 'boolean') {
      return res.status(400).json({ error: 'Le champ "paused" (booléen) est requis.' });
    }
    const config = await BotConfig.findOneAndUpdate(
      { botId },
      { $set: { manualOverride: { paused, reason, updatedBy: req.user?.email || 'inconnu' } } },
      { new: true, upsert: true }
    );
    return res.json(config);
  } catch (err) {
    return res.status(500).json({ error: 'Erreur lors de la mise à jour du coupe-circuit.', details: err.message });
  }
}

// --- Contrôle du process bot (démarrage/arrêt natif local) ---

async function startBotProcess(req, res) {
  try {
    const status = botProcess.start();
    return res.json(status);
  } catch (err) {
    return res.status(err.status || 500).json({ error: err.message });
  }
}

async function stopBotProcess(req, res) {
  try {
    const status = await botProcess.stop();
    // Le process ne pouvant plus se signaler lui-même une fois arrêté depuis
    // l'extérieur, on force isRunning=false directement ici.
    await BotStatus.findOneAndUpdate(
      { botId: 'default' },
      { $set: { isRunning: false, meta: { tradingEnabled: false, reason: "Arrêté manuellement depuis l'interface" } } },
      { upsert: true }
    );
    return res.json(status);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}

function getBotProcessStatus(req, res) {
  return res.json(botProcess.getStatus());
}

module.exports = {
  createLog, listLogs,
  createTrade, listTrades,
  updateStatus, getStatus,
  getPerformance,
  createSnapshot, listSnapshots,
  reportConfig, getConfig, setManualOverride,
  startBotProcess, stopBotProcess, getBotProcessStatus,
};

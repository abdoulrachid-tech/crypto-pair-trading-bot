const BotLog = require('../models/BotLog');
const Trade = require('../models/Trade');
const BotStatus = require('../models/BotStatus');

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

module.exports = {
  createLog, listLogs,
  createTrade, listTrades,
  updateStatus, getStatus,
  getPerformance,
};

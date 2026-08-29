const mongoose = require('mongoose');

/**
 * Un seul document "vivant" par bot (upsert), utile pour afficher rapidement
 * l'état courant (Mission 12/14) sans avoir à agréger tous les logs/trades.
 */
const botStatusSchema = new mongoose.Schema(
  {
    botId: { type: String, required: true, unique: true, default: 'default' },
    event: { type: String, default: 'heartbeat' },
    beta: { type: Number },
    halfLife: { type: Number },
    lastZscore: { type: Number },
    lastSignal: { type: String },
    isRunning: { type: Boolean, default: true },
    meta: { type: mongoose.Schema.Types.Mixed, default: {} },
  },
  { timestamps: true }
);

module.exports = mongoose.model('BotStatus', botStatusSchema);

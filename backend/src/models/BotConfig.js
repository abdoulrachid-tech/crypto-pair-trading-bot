const mongoose = require('mongoose');

/**
 * Document unique (upsert) par bot. Deux catégories de champs :
 * - Paramètres actifs, rapportés par le bot au démarrage (lecture seule côté
 *   frontend — ils viennent du .env du bot, pas éditables sans redémarrage).
 * - `manualOverride`, écrit par le frontend (utilisateur authentifié) : un
 *   coupe-circuit manuel, indépendant du garde-fou automatique de
 *   cointégration, pour mettre le trading en pause depuis l'interface sans
 *   avoir à toucher au serveur.
 */
const botConfigSchema = new mongoose.Schema(
  {
    botId: { type: String, required: true, unique: true, default: 'default' },

    // --- Paramètres actifs (rapportés par le bot, lecture seule) ---
    symbolA: { type: String },
    symbolB: { type: String },
    timeframe: { type: String },
    exchangeId: { type: String },
    tradingMode: { type: String }, // "simulation" | "live"
    liveTradingConfirmed: { type: Boolean },
    zscoreEntry: { type: Number },
    zscoreExit: { type: Number },
    zscoreStoploss: { type: Number },
    tradeSizeQuote: { type: Number },
    cycleIntervalSeconds: { type: Number },
    bootstrapHistoryDays: { type: Number },
    recalibrationIntervalHours: { type: Number },

    // --- Coupe-circuit manuel (écrit par le frontend) ---
    manualOverride: {
      paused: { type: Boolean, default: false },
      reason: { type: String, default: '' },
      updatedBy: { type: String, default: '' },
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model('BotConfig', botConfigSchema);

const mongoose = require('mongoose');

/**
 * Un point par cycle du bot (voir Mission 10), même quand aucun trade n'a
 * lieu — sert à tracer des graphes continus (prix, spread, Z-score) plutôt
 * que des graphes qui ne bougent qu'aux moments de trade.
 */
const marketSnapshotSchema = new mongoose.Schema(
  {
    symbolA: { type: String, required: true },
    symbolB: { type: String, required: true },
    priceA: { type: Number, required: true },
    priceB: { type: Number, required: true },
    spread: { type: Number },
    zscore: { type: Number },
    beta: { type: Number },
    recordedAt: { type: Date, default: Date.now },
  },
  { timestamps: true }
);

marketSnapshotSchema.index({ recordedAt: -1 });

module.exports = mongoose.model('MarketSnapshot', marketSnapshotSchema);

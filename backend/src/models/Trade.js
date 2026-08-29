const mongoose = require('mongoose');

const tradeSchema = new mongoose.Schema(
  {
    symbolA: { type: String, required: true },
    symbolB: { type: String, required: true },
    signal: {
      type: String,
      enum: ['long', 'short', 'close', 'hold'],
      required: true,
    },
    priceA: { type: Number, required: true },
    priceB: { type: Number, required: true },
    zscore: { type: Number, required: true },
    qtyA: { type: Number, default: 0 },
    qtyB: { type: Number, default: 0 },
    pnl: { type: Number, default: 0 },
    mode: {
      type: String,
      enum: ['simulation', 'live'],
      default: 'simulation',
    },
    // Horodatage transmis par le bot Python (au format ISO 8601, UTC)
    executedAt: { type: Date, default: Date.now },
  },
  { timestamps: true }
);

tradeSchema.index({ executedAt: -1 });
tradeSchema.index({ symbolA: 1, symbolB: 1 });

module.exports = mongoose.model('Trade', tradeSchema);

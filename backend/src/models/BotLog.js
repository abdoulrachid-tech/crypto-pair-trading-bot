const mongoose = require('mongoose');

const botLogSchema = new mongoose.Schema(
  {
    level: {
      type: String,
      enum: ['info', 'warning', 'error'],
      default: 'info',
    },
    message: { type: String, required: true },
    meta: { type: mongoose.Schema.Types.Mixed, default: {} },
  },
  { timestamps: true }
);

botLogSchema.index({ createdAt: -1 });

module.exports = mongoose.model('BotLog', botLogSchema);

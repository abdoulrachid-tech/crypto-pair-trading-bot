const mongoose = require('mongoose');

async function connectDB() {
  const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/trading_bot';

  mongoose.connection.on('connected', () => {
    console.log(`[MongoDB] Connecté à ${uri}`);
  });
  mongoose.connection.on('error', (err) => {
    console.error('[MongoDB] Erreur de connexion :', err.message);
  });
  mongoose.connection.on('disconnected', () => {
    console.warn('[MongoDB] Déconnecté.');
  });

  await mongoose.connect(uri);
}

module.exports = connectDB;

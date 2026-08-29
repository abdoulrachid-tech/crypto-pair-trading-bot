require('dotenv').config();

const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');

const authRoutes = require('./src/routes/auth');
const botRoutes = require('./src/routes/bot');

function createApp() {
  const app = express();

  app.use(express.json());
  app.use(cookieParser());
  app.use(
    cors({
      origin: process.env.FRONTEND_ORIGIN || 'http://localhost:5173',
      credentials: true, // indispensable pour que le cookie HttpOnly JWT soit transmis
    })
  );

  app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  app.use('/api/auth', authRoutes);
  app.use('/api/bot', botRoutes);

  // Gestionnaire d'erreurs générique (attrape tout ce qui n'a pas été géré plus haut)
  app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Erreur interne du serveur.' });
  });

  app.use((req, res) => {
    res.status(404).json({ error: 'Route non trouvée.' });
  });

  return app;
}

module.exports = createApp;

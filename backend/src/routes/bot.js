const express = require('express');
const {
  createLog, listLogs,
  createTrade, listTrades,
  updateStatus, getStatus,
  getPerformance,
  createSnapshot, listSnapshots,
} = require('../controllers/botController');
const { requireAuth } = require('../middleware/auth');
const { requireBotToken } = require('../middleware/botAuth');

const router = express.Router();

// --- Ingestion depuis le bot Python (protégée par un token statique, pas un JWT utilisateur) ---
router.post('/logs', requireBotToken, createLog);
router.post('/trades', requireBotToken, createTrade);
router.post('/status', requireBotToken, updateStatus);
router.post('/snapshots', requireBotToken, createSnapshot);

// --- Consultation depuis le frontend React (protégée par JWT utilisateur) ---
router.get('/logs', requireAuth, listLogs);
router.get('/trades', requireAuth, listTrades);
router.get('/status', requireAuth, getStatus);
router.get('/performance', requireAuth, getPerformance);
router.get('/snapshots', requireAuth, listSnapshots);

module.exports = router;

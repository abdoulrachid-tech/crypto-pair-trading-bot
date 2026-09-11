const express = require('express');
const {
  createLog, listLogs,
  createTrade, listTrades,
  updateStatus, getStatus,
  getPerformance,
  createSnapshot, listSnapshots,
  reportConfig, getConfig, setManualOverride,
  startBotProcess, stopBotProcess, getBotProcessStatus,
} = require('../controllers/botController');
const { requireAuth } = require('../middleware/auth');
const { requireBotToken } = require('../middleware/botAuth');

const router = express.Router();

// --- Ingestion depuis le bot Python (protégée par un token statique, pas un JWT utilisateur) ---
router.post('/logs', requireBotToken, createLog);
router.post('/trades', requireBotToken, createTrade);
router.post('/status', requireBotToken, updateStatus);
router.post('/snapshots', requireBotToken, createSnapshot);
router.post('/config/report', requireBotToken, reportConfig);
router.get('/config/control', requireBotToken, getConfig); // lecture par le bot lui-même (token bot, pas de cookie JWT)

// --- Consultation depuis le frontend React (protégée par JWT utilisateur) ---
router.get('/logs', requireAuth, listLogs);
router.get('/trades', requireAuth, listTrades);
router.get('/status', requireAuth, getStatus);
router.get('/performance', requireAuth, getPerformance);
router.get('/snapshots', requireAuth, listSnapshots);
router.get('/config', requireAuth, getConfig);
router.post('/config/override', requireAuth, setManualOverride);
router.post('/process/start', requireAuth, startBotProcess);
router.post('/process/stop', requireAuth, stopBotProcess);
router.get('/process/status', requireAuth, getBotProcessStatus);

module.exports = router;

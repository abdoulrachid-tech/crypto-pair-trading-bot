/**
 * Authentifie les requêtes provenant du bot Python (src/api_client.py), qui
 * envoie un simple token statique en en-tête `Authorization: Bearer <token>`
 * plutôt que le flux JWT utilisateur complet — le bot n'est pas un "utilisateur"
 * au sens propre, c'est un service backend-to-backend.
 */
function requireBotToken(req, res, next) {
  const expected = process.env.BOT_API_TOKEN;

  // Si aucun token n'est configuré côté serveur, on n'exige rien (pratique en dev local).
  if (!expected) {
    return next();
  }

  const header = req.headers.authorization || '';
  const provided = header.startsWith('Bearer ') ? header.slice(7) : null;

  if (provided !== expected) {
    return res.status(401).json({ error: 'Token bot invalide.' });
  }

  return next();
}

module.exports = { requireBotToken };

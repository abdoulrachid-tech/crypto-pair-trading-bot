const jwt = require('jsonwebtoken');

/**
 * Vérifie le JWT stocké dans le cookie HttpOnly `token` (voir Mission 13 du guide).
 * En cas de succès, attache `req.user = { id, email, role }` et poursuit.
 */
function requireAuth(req, res, next) {
  const token = req.cookies && req.cookies.token;

  if (!token) {
    return res.status(401).json({ error: 'Non authentifié : token manquant.' });
  }

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    req.user = payload;
    return next();
  } catch (err) {
    return res.status(401).json({ error: 'Token invalide ou expiré.' });
  }
}

/**
 * Autorise uniquement les utilisateurs ayant le rôle "admin".
 * À utiliser après `requireAuth`.
 */
function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Accès réservé aux administrateurs.' });
  }
  return next();
}

module.exports = { requireAuth, requireAdmin };

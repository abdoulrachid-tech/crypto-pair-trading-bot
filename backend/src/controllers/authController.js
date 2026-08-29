const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const SALT_ROUNDS = 10;

function signToken(user) {
  return jwt.sign(
    { id: user._id.toString(), email: user.email, role: user.role },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
  );
}

function setAuthCookie(res, token) {
  res.cookie('token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 jours
  });
}

async function register(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email et mot de passe requis.' });
    }
    if (password.length < 8) {
      return res.status(400).json({ error: 'Le mot de passe doit contenir au moins 8 caractères.' });
    }

    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing) {
      return res.status(409).json({ error: 'Un compte existe déjà avec cet email.' });
    }

    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);
    const user = await User.create({ email: email.toLowerCase(), passwordHash });

    const token = signToken(user);
    setAuthCookie(res, token);

    return res.status(201).json({ id: user._id, email: user.email, role: user.role });
  } catch (err) {
    return res.status(500).json({ error: 'Erreur serveur lors de l\'inscription.', details: err.message });
  }
}

async function login(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email et mot de passe requis.' });
    }

    const user = await User.findOne({ email: email.toLowerCase() });
    if (!user) {
      return res.status(401).json({ error: 'Identifiants invalides.' });
    }

    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
      return res.status(401).json({ error: 'Identifiants invalides.' });
    }

    const token = signToken(user);
    setAuthCookie(res, token);

    return res.json({ id: user._id, email: user.email, role: user.role });
  } catch (err) {
    return res.status(500).json({ error: 'Erreur serveur lors de la connexion.', details: err.message });
  }
}

function logout(req, res) {
  res.clearCookie('token');
  return res.json({ message: 'Déconnecté.' });
}

function me(req, res) {
  // req.user est peuplé par le middleware requireAuth
  return res.json(req.user);
}

module.exports = { register, login, logout, me };

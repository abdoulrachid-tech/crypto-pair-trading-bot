# backend — API Express.js + MongoDB

Implémente la Mission 13 du guide : authentification JWT (cookies HttpOnly),
persistance des logs/trades/statut du bot dans MongoDB, routes RESTful
consommées par le frontend React.

## Structure

```text
backend/
├── app.js                        # Application Express (routes, middlewares) — testable sans DB
├── server.js                     # Bootstrap : connexion MongoDB puis app.listen()
├── src/
│   ├── config/db.js              # Connexion Mongoose
│   ├── models/
│   │   ├── User.js                # email, passwordHash (bcrypt), role
│   │   ├── BotLog.js              # level, message, meta
│   │   ├── Trade.js                # symbolA/B, signal, prix, zscore, pnl, mode
│   │   └── BotStatus.js            # document unique par bot (upsert)
│   ├── middleware/
│   │   ├── auth.js                 # requireAuth (JWT cookie), requireAdmin
│   │   └── botAuth.js               # requireBotToken (token statique pour le bot Python)
│   ├── controllers/
│   │   ├── authController.js        # register / login / logout / me
│   │   └── botController.js         # logs, trades, status, performance
│   └── routes/
│       ├── auth.js                   # /api/auth/*
│       └── bot.js                     # /api/bot/*
└── tests/                              # 25 tests Jest (mocks, sans DB réelle nécessaire)
```

## Installation

```bash
cd backend
npm install
cp .env.example .env   # puis éditez .env (JWT_SECRET, MONGODB_URI, etc.)
```

## Lancer le serveur

```bash
# Nécessite une instance MongoDB accessible (voir docker-compose.yml à la racine)
npm start        # production
npm run dev       # avec nodemon (rechargement automatique)
```

## Lancer les tests

```bash
npm test
```

> **Note sur les tests** : les tests mockent systématiquement les modèles Mongoose
> (`jest.mock('../src/models/...')`), afin de valider la logique des contrôleurs et
> middlewares **sans nécessiter de connexion MongoDB réelle**. C'est un choix
> délibéré : dans cet environnement de développement, télécharger un binaire
> MongoDB pour des tests d'intégration complets (via `mongodb-memory-server`)
> n'était pas possible hors ligne. Pour des tests d'intégration de bout en bout
> avec une vraie base, démarrez MongoDB via `docker compose up -d mongo` et
> adaptez les tests pour vous connecter à cette instance plutôt que de mocker
> les modèles.

## Points clés d'implémentation (voir le guide, Mission 13)

- **Mots de passe** : hashés avec `bcrypt` (10 salt rounds), jamais stockés en clair.
- **JWT** : signé avec `JWT_SECRET`, transmis dans un cookie **HttpOnly** +
  `sameSite: strict` (+ `secure` en production) — inaccessible à JavaScript côté
  client, ce qui limite le risque de vol par XSS.
- **Deux mécanismes d'authentification distincts** :
  - `requireAuth` (JWT cookie) protège les routes `GET` consultées par le frontend React.
  - `requireBotToken` (token statique `Authorization: Bearer ...`) protège les
    routes `POST` d'ingestion utilisées par le bot Python (`trading-bot/src/api_client.py`).
- **CORS** : `credentials: true` + origine explicite (`FRONTEND_ORIGIN`), requis
  pour que le navigateur transmette le cookie JWT lors des appels cross-origin
  en développement (frontend sur un port différent du backend).

## Routes disponibles

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET | `/api/health` | Aucune | Vérification de disponibilité |
| POST | `/api/auth/register` | Aucune | Création de compte |
| POST | `/api/auth/login` | Aucune | Connexion |
| POST | `/api/auth/logout` | Aucune | Déconnexion (efface le cookie) |
| GET | `/api/auth/me` | JWT | Profil de l'utilisateur connecté |
| POST | `/api/bot/logs` | Token bot | Ingestion d'un log |
| GET | `/api/bot/logs` | JWT | Liste des logs |
| POST | `/api/bot/trades` | Token bot | Ingestion d'un trade |
| GET | `/api/bot/trades` | JWT | Liste des trades |
| POST | `/api/bot/status` | Token bot | Mise à jour du statut du bot |
| GET | `/api/bot/status` | JWT | Statut courant du bot |
| GET | `/api/bot/performance` | JWT | PnL cumulé, win rate, max drawdown, courbe d'équité |

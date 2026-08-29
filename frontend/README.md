# frontend — Dashboard React de monitoring

Implémente la Mission 14 du guide : tableau de bord de visualisation en temps
réel du bot (état courant, PnL, Z-score, historique des trades, logs).

## Structure

```text
frontend/
├── src/
│   ├── api/client.js           # Client axios (withCredentials pour le cookie JWT)
│   ├── context/AuthContext.jsx  # État d'authentification global (React Context)
│   ├── components/
│   │   ├── Layout.jsx            # Sidebar de navigation
│   │   ├── ProtectedRoute.jsx     # Redirige vers /login si non authentifié
│   │   ├── StatCards.jsx           # Cartes de métriques (PnL, win rate, drawdown...)
│   │   ├── PnlChart.jsx             # Courbe du PnL cumulé (Recharts)
│   │   ├── ZScoreChart.jsx           # Z-score + seuils d'entrée/sortie (Recharts)
│   │   └── TradeTable.jsx             # Tableau d'historique des trades
│   ├── pages/
│   │   ├── Login.jsx / Register.jsx    # Authentification
│   │   ├── Dashboard.jsx                # Page principale (auto-refresh 15s)
│   │   ├── TradesHistory.jsx             # Historique complet + filtres
│   │   └── Logs.jsx                       # Logs bruts du bot
│   ├── tests/                              # Tests Vitest + Testing Library
│   ├── App.jsx                             # Routage (react-router-dom)
│   └── main.jsx                            # Point d'entrée
└── vite.config.js                           # Proxy /api -> backend (port 5000)
```

## Installation

```bash
cd frontend
npm install
```

## Développement

```bash
npm run dev
# ouvre http://localhost:5173 — les appels /api/* sont automatiquement
# redirigés vers le backend Express sur http://localhost:5000 (voir vite.config.js)
```

## Tests

```bash
npm test
```

## Build de production

```bash
npm run build
# génère le dossier dist/ — c'est ce dossier qui sera servi par Nginx (Mission 16)
```

## Points clés d'implémentation (voir le guide, Mission 14)

- **Authentification** : `AuthContext` interroge `GET /api/auth/me` au chargement
  pour savoir si un cookie JWT valide est déjà présent ; `ProtectedRoute` redirige
  vers `/login` si ce n'est pas le cas.
- **Rafraîchissement automatique** : le Dashboard interroge l'API toutes les 15
  secondes (`setInterval`) — une alternative plus réactive (WebSocket / SSE) est
  évoquée dans le guide (Mission 14) mais volontairement non implémentée ici pour
  rester simple.
- **Visualisation du Z-score avec seuils** : `ZScoreChart` trace des
  `ReferenceLine` Recharts pour les seuils d'entrée (±2 par défaut) et de sortie
  (±0.5), superposées à la courbe réelle du Z-score — exactement la vue demandée
  dans le guide ("visualiser les seuils d'entrée et de sortie directement sur le
  graphique du Z-score").

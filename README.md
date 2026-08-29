# Crypto Pair Trading Bot

Bot de trading algorithmique complet mettant en œuvre une stratégie
d'**arbitrage statistique par pair trading** sur Bitcoin (BTC) et Ethereum
(ETH), avec un pipeline complet : recherche quantitative hors ligne
(collecte, nettoyage, backtesting), moteur d'exécution temps réel, API de
persistance, et dashboard web de supervision.

Ce projet implémente, de bout en bout, les 22 missions du guide de
construction associé (collecte de données → nettoyage → analyse statistique →
backtesting → bot temps réel → API → frontend → déploiement).

## ⚠️ Avertissement sur les risques

L'utilisation de bots de trading automatisés comporte des risques financiers
réels et significatifs. Ce projet est fourni **par défaut en mode simulation**
(`TRADING_MODE=simulation` dans `trading-bot/.env`) : aucun ordre réel n'est
jamais envoyé à un exchange tant que vous ne changez pas explicitement ce
paramètre. Si vous passez en mode réel (`TRADING_MODE=live`) avec des clés API
d'exchange valides, vous exposez du capital réel à des pertes potentielles,
pouvant aller jusqu'à la totalité du capital engagé. **Ne risquez jamais plus
que ce que vous pouvez vous permettre de perdre**, et validez rigoureusement la
stratégie (Missions 8-9) avant toute mise en production.

## Fonctionnalités clés

- **Stratégie de pair trading** basée sur la cointégration (test ADF /
  Engle-Granger), le hedge ratio et le Z-score du spread.
- **Backtesting robuste** avec sizing de position réaliste, frais de
  transaction, validation in-sample / out-of-sample.
- **Bot temps réel** (Python + CCXT) : génération de signaux, exécution
  simulée ou réelle, recalibrage automatique périodique avec garde-fous de
  désactivation.
- **API backend sécurisée** (Express.js + MongoDB) : authentification JWT via
  cookies HttpOnly, persistance des logs/trades/statut.
- **Dashboard de monitoring** (React) : PnL cumulé, Z-score en temps réel,
  historique des trades, logs.
- **Suite de tests** : 19 tests Python (pytest), 25 tests backend (Jest), 6
  tests frontend (Vitest) — tous exécutés et passants au moment de la livraison.

## Architecture

```text
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   trading-bot/       │     │      backend/         │     │     frontend/        │
│   (Python + CCXT)    │────▶│   (Express + MongoDB) │◀────│      (React)         │
│                       │     │                        │     │                      │
│  - Collecte (CCXT)    │     │  - Auth JWT/bcrypt      │     │  - Dashboard          │
│  - Nettoyage (Pandas) │     │  - Logs/Trades/Statut    │     │  - Historique trades   │
│  - Stats (statsmodels)│     │  - API REST               │     │  - Logs                 │
│  - Backtest            │     └──────────────────────────┘     └──────────────────────┘
│  - Signal temps réel    │
│  - Exécution ordres      │     ┌──────────────────────┐
│  - Recalibrage auto       │────▶│    PostgreSQL          │
└─────────────────────────────┘     │  (historique/backtests) │
                                     └──────────────────────────┘
```

## Structure du dépôt

```text
crypto-pair-trading-bot/
├── trading-bot/         # Bot Python (Missions 3-12, 20)
│   ├── src/               # Modules : config, collecte, nettoyage, stats, backtest, signal, exécution, monitoring, recalibrage
│   ├── scripts/             # CLI : collect_data.py, clean_data.py, run_backtest.py
│   ├── tests/                # 19 tests pytest (données synthétiques cointégrées)
│   └── README.md
├── backend/               # API Express.js + MongoDB (Mission 13)
│   ├── src/                 # Modèles, middlewares, contrôleurs, routes
│   ├── tests/                 # 25 tests Jest (mocks, sans DB réelle nécessaire)
│   └── README.md
├── frontend/                # Dashboard React (Mission 14)
│   ├── src/                   # Composants, pages, contexte d'auth, client API
│   ├── src/tests/               # 6 tests Vitest + Testing Library
│   └── README.md
├── docs/                       # (captures d'écran, schémas — à compléter)
├── docker-compose.yml            # PostgreSQL + MongoDB pour le développement local
├── .env.example                   # Variables d'environnement globales (référence)
├── .gitignore
├── LICENSE                          # MIT
└── README.md                          # Ce fichier
```

## Installation et démarrage local

### 1. Bases de données (PostgreSQL + MongoDB)

```bash
docker compose up -d
```

### 2. Backend (Express.js)

```bash
cd backend
npm install
cp .env.example .env    # éditez JWT_SECRET, MONGODB_URI, BOT_API_TOKEN
npm start                 # démarre sur http://localhost:5000
```

### 3. Bot Python — pipeline de recherche quantitative

```bash
cd trading-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # éditez selon vos besoins

python -m src.db             # crée le schéma PostgreSQL
python scripts/collect_data.py --days 180   # Mission 5
python scripts/clean_data.py                 # Mission 6
python scripts/run_backtest.py               # Mission 8/9 — validez avant de continuer !
```

### 4. Bot Python — mode temps réel (simulation par défaut)

```bash
python -m src.main    # nécessite trading-bot/.env avec BACKEND_API_URL pointant vers l'API
```

### 5. Frontend (React)

```bash
cd frontend
npm install
npm run dev             # ouvre http://localhost:5173
```

Créez un compte via l'écran d'inscription, puis vous verrez le dashboard se
peupler dès que le bot Python commence à pousser des trades/logs vers l'API.

## Lancer tous les tests

```bash
# Bot Python
cd trading-bot && pytest -v

# Backend
cd backend && npm test

# Frontend
cd frontend && npm test
```

## Aller plus loin

Les missions suivantes du guide (déploiement VPS, nom de domaine,
communication, branches Git, multi-paires, diversification des stratégies)
sont des étapes **opérationnelles et stratégiques** qui s'appliquent à ce code
une fois qu'il tourne correctement en local — elles ne changent pas le code
source lui-même et sont donc décrites uniquement dans le guide texte associé,
pas reproduites ici sous forme de fichiers.

## Licence

Ce projet est distribué sous licence MIT — voir [LICENSE](LICENSE).

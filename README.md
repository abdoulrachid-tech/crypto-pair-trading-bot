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

Le bot et le backend se connectent via une simple chaîne de connexion
(`postgres_dsn` dans `trading-bot/src/config.py`, `MONGODB_URI` dans
`backend/.env`) : aucune des deux bases n'exige Docker. Deux options
équivalentes :

#### Option A — Tout natif (sans Docker), recommandé sous Windows 11

**PostgreSQL :**
1. Téléchargez l'installeur sur https://www.postgresql.org/download/windows/
   (le programme officiel EDB, inclut aussi pgAdmin).
2. Exécutez `trading-bot\scripts\setup_postgres_native.sql` (adaptez le mot
   de passe avant) — soit collé dans pgAdmin → Query Tool, soit en
   PowerShell si `psql` est dans le PATH :
   ```powershell
   psql -U postgres -f trading-bot\scripts\setup_postgres_native.sql
   ```
3. Dans `trading-bot\.env` : `POSTGRES_HOST=localhost`,
   `POSTGRES_PORT=5432` (valeurs par défaut de l'installeur Windows).

**MongoDB :**
1. Téléchargez **MongoDB Community Server** sur
   https://www.mongodb.com/try/download/community et installez-le en
   cochant "Install MongoDB as a Service" (il démarre alors automatiquement
   au démarrage de Windows, sur `localhost:27017`, sans rien à lancer
   manuellement). MongoDB Compass (GUI) est proposé en option dans le même
   installeur si vous voulez inspecter les collections visuellement.
2. Dans `backend\.env` : `MONGODB_URI=mongodb://localhost:27017/trading_bot`
   (valeur par défaut, aucune authentification requise en local).
3. Vérifier que le service tourne : PowerShell →
   ```powershell
   Get-Service -Name MongoDB
   ```
   (doit afficher `Running`; sinon `Start-Service -Name MongoDB`).

Avec cette option, `docker-compose.yml` n'est pas utilisé du tout — vous
pouvez ignorer Docker complètement.

#### Option B — Docker (PostgreSQL + MongoDB conteneurisés)

```bash
docker compose up -d
```

Pratique pour un développement multi-plateforme identique ou pour tout
réinitialiser d'un coup, mais nécessite Docker Desktop sous Windows.
Rien n'empêche non plus de mélanger les deux (ex. Postgres natif +
`docker compose up -d mongo`).

### 2. Backend (Express.js)

```bash
cd backend
npm install
cp .env.example .env    # éditez JWT_SECRET, MONGODB_URI, BOT_API_TOKEN
npm start                 # démarre sur http://localhost:5000
```

### 3. Bot Python — pipeline de recherche quantitative

**Linux/macOS :**

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

**Windows 11 (PowerShell) :**

```powershell
cd trading-bot
python -m venv .venv
.venv\Scripts\Activate.ps1
# Si l'exécution de scripts est bloquée par la politique PowerShell :
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
copy .env.example .env       # éditez selon vos besoins

python -m src.db             # crée le schéma PostgreSQL
python scripts\collect_data.py --days 180   # Mission 5
python scripts\clean_data.py                 # Mission 6
python scripts\run_backtest.py               # Mission 8/9 — validez avant de continuer !
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

## Passer en mode réel (live trading)

⚠️ **Lisez l'avertissement sur les risques en haut de ce document avant
d'aller plus loin.** Ceci n'est pas un conseil financier — c'est une
description de la procédure technique. La décision de risquer du capital
réel vous appartient entièrement.

Le code d'exécution (`trading-bot/src/executor.py`) et de connexion à
l'exchange (`trading-bot/src/data_collector.py::build_exchange`) supportent
déjà nativement les deux modes ; passer en réel ne change aucun fichier de
code, seulement la configuration :

1. **Validez d'abord en simulation et en backtest.** Le mode simulation par
   défaut n'envoie aucun ordre — utilisez-le (ainsi que
   `scripts/run_backtest.py`) tant que les statistiques (Sharpe, drawdown,
   win rate) ne vous semblent pas robustes sur une période out-of-sample.
2. **Générez des clés API sur votre exchange** avec uniquement les
   permissions "trading spot" — jamais les permissions de retrait
   ("withdraw"). Renseignez-les dans `trading-bot/.env` :
   `EXCHANGE_API_KEY`, `EXCHANGE_API_SECRET`.
3. **Désactivez le sandbox** : `EXCHANGE_SANDBOX=false`.
4. **Activez les deux interrupteurs requis** : `TRADING_MODE=live` **et**
   `LIVE_TRADING_CONFIRMED=true`. Les deux sont volontairement séparés :
   tant que le second n'est pas explicitement à `true`, le bot reste en
   simulation même si `TRADING_MODE=live`, pour éviter qu'un mode réel ne
   s'active par erreur (mauvais `.env`, copier-coller, etc.).
5. **Démarrez avec une `TRADE_SIZE_QUOTE` faible** pour votre premier
   run réel, et surveillez le dashboard React ainsi que les alertes
   Telegram (`monitor.py`) de près les premières heures.
6. Le garde-fou de recalibrage (`recalibrator.py`, Mission 20) coupe
   automatiquement le bot si la cointégration se dégrade ou si la
   half-life devient trop élevée — mais il ne remplace pas une
   surveillance humaine active, surtout au début.

## Aller plus loin

Les missions suivantes du guide (déploiement VPS, nom de domaine,
communication, branches Git, multi-paires, diversification des stratégies)
sont des étapes **opérationnelles et stratégiques** qui s'appliquent à ce code
une fois qu'il tourne correctement en local — elles ne changent pas le code
source lui-même et sont donc décrites uniquement dans le guide texte associé,
pas reproduites ici sous forme de fichiers.

## Licence

Ce projet est distribué sous licence MIT — voir [LICENSE](LICENSE).

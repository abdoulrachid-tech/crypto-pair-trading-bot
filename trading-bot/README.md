# trading-bot (Python) — Bot de pair trading BTC/ETH

Cœur quantitatif et moteur temps réel du projet. Implémente les Missions 3 à 12
et 20 du guide : stratégie, collecte/nettoyage de données, analyse statistique,
backtesting, exécution (simulation/réel), monitoring, recalibrage automatique.

## Structure

```text
trading-bot/
├── src/
│   ├── config.py            # Configuration centralisée (variables d'environnement)
│   ├── data_collector.py    # Mission 5  — collecte OHLCV via CCXT
│   ├── data_cleaner.py      # Mission 6  — nettoyage, alignement, log-returns
│   ├── stats.py             # Mission 7/20 — hedge ratio, cointégration, Z-score, half-life
│   ├── backtester.py        # Mission 8/9 — moteur de backtest + métriques
│   ├── signal_generator.py  # Mission 10 — génération du signal (long/short/close/hold)
│   ├── executor.py          # Mission 11 — exécution simulée ou réelle des ordres
│   ├── monitor.py           # Mission 12 — logging + alertes Telegram
│   ├── recalibrator.py      # Mission 20 — recalibrage automatique + garde-fous
│   ├── db.py                 # Missions 4/6 — persistance PostgreSQL
│   ├── api_client.py         # Pousse logs/trades/statut vers le backend Express
│   └── main.py               # Orchestrateur : boucle temps réel complète
├── scripts/
│   ├── collect_data.py       # CLI Mission 5
│   ├── clean_data.py         # CLI Mission 6
│   └── run_backtest.py       # CLI Mission 8/9
├── tests/                    # Suite pytest (19 tests, données synthétiques)
├── requirements.txt
└── .env.example
```

## Installation

```bash
cd trading-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis éditez .env avec vos propres valeurs
```

## Lancer les tests

Les tests utilisent des données **synthétiques** (un spread cointégré généré
par un processus d'Ornstein-Uhlenbeck), donc aucune connexion réseau/exchange
n'est nécessaire pour les exécuter :

```bash
pytest -v
```

## Utilisation en pratique (dans l'ordre du guide)

**1. Base PostgreSQL (Mission 4)** — voir le `docker-compose.yml` à la racine du repo :

```bash
docker compose up -d postgres
python -m src.db   # crée le schéma (idempotent)
```

**2. Collecte des données historiques (Mission 5)**

```bash
python scripts/collect_data.py --days 180
```

**3. Nettoyage (Mission 6)**

```bash
python scripts/clean_data.py
```

**4. Backtest et validation (Mission 8/9)**

```bash
python scripts/run_backtest.py --entry 2.0 --exit 0.5 --window 200
```

**5. Bot temps réel (Mission 10/11/12/20)**

```bash
# Mode simulation par défaut (TRADING_MODE=simulation dans .env)
python -m src.main
```

> ⚠️ Pour passer en trading réel, changez `TRADING_MODE=live` dans `.env` et
> renseignez des clés API d'exchange **sans permission de retrait**. Relisez
> l'avertissement sur les risques dans le README principal avant toute mise en
> production avec de l'argent réel.

## Notes de conception

- **Aucun look-ahead bias** : le backtester (`backtester.py`) et le générateur
  de signal temps réel (`signal_generator.py`) partagent la même logique de
  décision, pour garantir que ce qui a été validé hors ligne est bien ce qui
  s'exécute en production.
- **Sizing réaliste** : les positions sont dimensionnées en fraction du
  capital courant (`position_size_fraction`), pas en unités arbitraires — les
  frais sont donc comparés à un P&L en dollars réellement comparables.
- **Découplage** : une panne de l'API backend (`api_client.py`) ne bloque
  jamais la boucle du bot — les appels sont "best-effort" et échouent silencieusement
  (avec un simple log en mode debug).

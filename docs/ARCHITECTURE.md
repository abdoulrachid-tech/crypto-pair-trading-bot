# Notes d'architecture

Ce dossier est destiné à accueillir, au fil du développement (Mission 15) :

- des captures d'écran du dashboard React (`dashboard.png`, `trades.png`, ...) ;
- un schéma d'architecture exporté (Mission 2) ;
- des résultats de backtest exportés (courbes d'équité, rapports de validation).

## Résumé du flux de données

1. **`trading-bot/scripts/collect_data.py`** interroge l'exchange via CCXT et
   écrit des CSV bruts dans `trading-bot/data/`.
2. **`trading-bot/scripts/clean_data.py`** nettoie et aligne ces CSV en un
   fichier unique `cleaned_pair.csv`.
3. **`trading-bot/scripts/run_backtest.py`** charge ce fichier, calcule la
   cointégration/le hedge ratio, et simule la stratégie (in-sample / out-of-sample).
4. Une fois la stratégie validée, **`trading-bot/src/main.py`** tourne en
   continu : il récupère les prix live, génère des signaux, exécute (ou simule)
   des ordres, et pousse logs/trades/statut vers l'API backend.
5. **`backend/`** persiste ces données dans MongoDB et les expose via une API
   REST protégée par JWT.
6. **`frontend/`** interroge cette API toutes les 15 secondes pour afficher un
   dashboard à jour.

## Schéma des tables PostgreSQL (recherche quantitative)

Voir `trading-bot/src/db.py::SCHEMA_SQL` pour la définition exacte :
`ohlcv_raw`, `ohlcv_aligned`, `backtest_results`, `recalibration_history`.

## Schéma des collections MongoDB (application web)

Voir `backend/src/models/` : `User`, `BotLog`, `Trade`, `BotStatus`.

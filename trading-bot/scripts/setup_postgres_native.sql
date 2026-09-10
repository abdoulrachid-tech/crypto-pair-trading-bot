-- Provisionnement d'un PostgreSQL natif (installé directement sur la machine,
-- sans Docker) pour le bot de trading.
--
-- Usage (en tant que superuser, ex. l'utilisateur système `postgres`) :
--   sudo -u postgres psql -f setup_postgres_native.sql
--
-- Adaptez le mot de passe ci-dessous, puis reportez les mêmes valeurs dans
-- trading-bot/.env (POSTGRES_HOST=localhost, POSTGRES_PORT=5432, etc.).
-- Le schéma applicatif (tables) est créé séparément par `python -m src.db`,
-- une fois que le bot peut se connecter à la base ci-dessous.

CREATE USER dev_user WITH PASSWORD 'my_strong_password';
CREATE DATABASE trading_data OWNER dev_user;
GRANT ALL PRIVILEGES ON DATABASE trading_data TO dev_user;

"""
Configuration centralisée du bot, chargée depuis les variables d'environnement.

Toutes les autres modules importent leurs paramètres depuis cet objet `settings`
plutôt que de relire `os.environ` directement, pour garder une seule source de vérité.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    return float(val) if val is not None and val != "" else default


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val is not None and val != "" else default


@dataclass
class Settings:
    # Exchange
    exchange_id: str = os.getenv("EXCHANGE_ID", "binance")
    exchange_api_key: str = os.getenv("EXCHANGE_API_KEY", "")
    exchange_api_secret: str = os.getenv("EXCHANGE_API_SECRET", "")
    exchange_sandbox: bool = field(default_factory=lambda: _get_bool("EXCHANGE_SANDBOX", True))

    # PostgreSQL
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = field(default_factory=lambda: _get_int("POSTGRES_PORT", 5432))
    postgres_db: str = os.getenv("POSTGRES_DB", "trading_data")
    postgres_user: str = os.getenv("POSTGRES_USER", "dev_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "my_strong_password")

    # Paire
    symbol_a: str = os.getenv("SYMBOL_A", "BTC/USDT")
    symbol_b: str = os.getenv("SYMBOL_B", "ETH/USDT")
    timeframe: str = os.getenv("TIMEFRAME", "1m")

    # Stratégie
    zscore_window: int = field(default_factory=lambda: _get_int("ZSCORE_WINDOW", 200))
    zscore_entry: float = field(default_factory=lambda: _get_float("ZSCORE_ENTRY", 2.0))
    zscore_exit: float = field(default_factory=lambda: _get_float("ZSCORE_EXIT", 0.5))
    zscore_stoploss: float = field(default_factory=lambda: _get_float("ZSCORE_STOPLOSS", 4.0))

    # Exécution
    trading_mode: str = os.getenv("TRADING_MODE", "simulation")  # "simulation" | "live"
    # Second interrupteur, distinct de TRADING_MODE, qui doit être positionné
    # explicitement à "true" pour que le mode live soit réellement actif.
    # Objectif : qu'un TRADING_MODE=live posé par erreur (mauvais fichier .env,
    # copier-coller, etc.) n'envoie jamais d'ordre réel tout seul.
    live_trading_confirmed: bool = field(default_factory=lambda: _get_bool("LIVE_TRADING_CONFIRMED", False))
    trade_size_quote: float = field(default_factory=lambda: _get_float("TRADE_SIZE_QUOTE", 100.0))
    min_seconds_between_trades: int = field(default_factory=lambda: _get_int("MIN_SECONDS_BETWEEN_TRADES", 60))

    # Backend API
    backend_api_url: str = os.getenv("BACKEND_API_URL", "http://localhost:5000/api")
    backend_api_token: str = os.getenv("BACKEND_API_TOKEN", "")

    # Alertes
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Cycle
    cycle_interval_seconds: int = field(default_factory=lambda: _get_int("CYCLE_INTERVAL_SECONDS", 300))
    recalibration_interval_hours: int = field(default_factory=lambda: _get_int("RECALIBRATION_INTERVAL_HOURS", 168))
    # Fenêtre d'historique chargée au démarrage pour le premier calcul de
    # hedge ratio / test de cointégration. Une fenêtre trop courte peut faire
    # échouer le test de cointégration sur du bruit court terme alors que la
    # relation est stable sur une période plus longue.
    bootstrap_history_days: int = field(default_factory=lambda: _get_int("BOOTSTRAP_HISTORY_DAYS", 30))

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_live(self) -> bool:
        return self.trading_mode.strip().lower() == "live" and self.live_trading_confirmed


settings = Settings()

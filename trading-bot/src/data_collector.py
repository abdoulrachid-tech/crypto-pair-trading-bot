"""
Mission 5 — Collecte des données historiques.

Récupère l'historique OHLCV d'une paire via CCXT, avec pagination automatique
pour couvrir de longues périodes malgré les limites de bougies par requête
imposées par les exchanges.
"""
import time
import logging
from datetime import datetime, timezone

import ccxt
import pandas as pd

from .config import settings

logger = logging.getLogger(__name__)


def build_exchange(exchange_id: str = None) -> ccxt.Exchange:
    """Instancie un client CCXT pour l'exchange configuré, avec rate limiting actif."""
    exchange_id = exchange_id or settings.exchange_id
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        "apiKey": settings.exchange_api_key or None,
        "secret": settings.exchange_api_secret or None,
        "enableRateLimit": True,
    })
    if settings.exchange_sandbox and "test" in exchange.urls:
        exchange.set_sandbox_mode(True)
    return exchange


def fetch_ohlcv_history(
    exchange: ccxt.Exchange,
    symbol: str,
    timeframe: str = "1m",
    since_ms: int = None,
    until_ms: int = None,
    limit_per_call: int = 1000,
    max_retries: int = 5,
) -> pd.DataFrame:
    """
    Récupère un historique OHLCV complet en paginant sur `since`.

    Retourne un DataFrame avec les colonnes : timestamp (UTC, tz-aware), open, high, low, close, volume.
    """
    all_rows = []
    cursor = since_ms
    until_ms = until_ms or exchange.milliseconds()

    while True:
        attempt = 0
        while True:
            try:
                batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=cursor, limit=limit_per_call)
                break
            except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as exc:
                attempt += 1
                if attempt > max_retries:
                    raise
                wait = min(2 ** attempt, 30)
                logger.warning("Erreur réseau (%s), nouvelle tentative dans %ss", exc, wait)
                time.sleep(wait)

        if not batch:
            break

        all_rows.extend(batch)
        last_ts = batch[-1][0]

        if last_ts >= until_ms or len(batch) < limit_per_call:
            break

        # Avance le curseur d'une bougie pour éviter de re-récupérer la dernière
        cursor = last_ts + 1
        time.sleep(exchange.rateLimit / 1000)

    if not all_rows:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    return df


def collect_pair_history(
    symbol_a: str = None,
    symbol_b: str = None,
    timeframe: str = None,
    days_back: int = 180,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Récupère l'historique des deux actifs de la paire sur `days_back` jours."""
    symbol_a = symbol_a or settings.symbol_a
    symbol_b = symbol_b or settings.symbol_b
    timeframe = timeframe or settings.timeframe

    exchange = build_exchange()
    now_ms = exchange.milliseconds()
    since_ms = now_ms - days_back * 24 * 60 * 60 * 1000

    logger.info("Collecte de %s depuis %s", symbol_a, datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc))
    df_a = fetch_ohlcv_history(exchange, symbol_a, timeframe, since_ms=since_ms, until_ms=now_ms)

    logger.info("Collecte de %s depuis %s", symbol_b, datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc))
    df_b = fetch_ohlcv_history(exchange, symbol_b, timeframe, since_ms=since_ms, until_ms=now_ms)

    return df_a, df_b


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    a, b = collect_pair_history(days_back=7)
    print(f"{settings.symbol_a}: {len(a)} lignes")
    print(f"{settings.symbol_b}: {len(b)} lignes")
    a.to_csv("data/raw_symbol_a.csv", index=False)
    b.to_csv("data/raw_symbol_b.csv", index=False)

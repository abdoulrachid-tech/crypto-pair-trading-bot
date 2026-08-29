"""
Mission 4 / 6 — Persistance des données historiques et nettoyées dans PostgreSQL.
"""
import logging

import pandas as pd
from sqlalchemy import create_engine, text

from .config import settings

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.postgres_dsn)
    return _engine


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ohlcv_raw (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    UNIQUE (symbol, timeframe, ts)
);

CREATE TABLE IF NOT EXISTS ohlcv_aligned (
    ts TIMESTAMPTZ PRIMARY KEY,
    symbol_a TEXT NOT NULL,
    symbol_b TEXT NOT NULL,
    close_a DOUBLE PRECISION,
    close_b DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ DEFAULT now(),
    symbol_a TEXT,
    symbol_b TEXT,
    params JSONB,
    sharpe_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    n_trades INTEGER,
    total_return_pct DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS recalibration_history (
    id SERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ DEFAULT now(),
    beta DOUBLE PRECISION,
    intercept DOUBLE PRECISION,
    spread_mean DOUBLE PRECISION,
    spread_std DOUBLE PRECISION,
    adf_pvalue DOUBLE PRECISION,
    coint_pvalue DOUBLE PRECISION,
    is_cointegrated BOOLEAN,
    half_life_periods DOUBLE PRECISION,
    disabled BOOLEAN,
    disable_reason TEXT
);
"""


def init_schema():
    """Crée les tables nécessaires si elles n'existent pas encore (idempotent)."""
    engine = get_engine()
    with engine.begin() as conn:
        for statement in SCHEMA_SQL.strip().split(";\n\n"):
            if statement.strip():
                conn.execute(text(statement))
    logger.info("Schéma PostgreSQL initialisé.")


def save_raw_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str):
    """Insère un DataFrame OHLCV brut, en ignorant les doublons (symbol, timeframe, ts)."""
    engine = get_engine()
    tmp = df.rename(columns={"timestamp": "ts"}).copy()
    tmp["symbol"] = symbol
    tmp["timeframe"] = timeframe

    with engine.begin() as conn:
        for _, row in tmp.iterrows():
            conn.execute(
                text("""
                    INSERT INTO ohlcv_raw (symbol, timeframe, ts, open, high, low, close, volume)
                    VALUES (:symbol, :timeframe, :ts, :open, :high, :low, :close, :volume)
                    ON CONFLICT (symbol, timeframe, ts) DO NOTHING
                """),
                {
                    "symbol": row["symbol"], "timeframe": row["timeframe"], "ts": row["ts"],
                    "open": row["open"], "high": row["high"], "low": row["low"],
                    "close": row["close"], "volume": row["volume"],
                },
            )
    logger.info("Insertion de %d lignes OHLCV brutes pour %s (%s)", len(tmp), symbol, timeframe)


def save_cleaned_pair(df: pd.DataFrame, symbol_a: str, symbol_b: str, col_a: str, col_b: str):
    """Persiste la série nettoyée et alignée (Mission 6) dans `ohlcv_aligned`."""
    engine = get_engine()
    with engine.begin() as conn:
        for ts, row in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO ohlcv_aligned (ts, symbol_a, symbol_b, close_a, close_b)
                    VALUES (:ts, :symbol_a, :symbol_b, :close_a, :close_b)
                    ON CONFLICT (ts) DO UPDATE SET close_a = EXCLUDED.close_a, close_b = EXCLUDED.close_b
                """),
                {"ts": ts, "symbol_a": symbol_a, "symbol_b": symbol_b, "close_a": row[col_a], "close_b": row[col_b]},
            )
    logger.info("Insertion/maj de %d lignes alignées (%s / %s)", len(df), symbol_a, symbol_b)


def save_backtest_result(symbol_a: str, symbol_b: str, params: dict, result) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO backtest_results
                    (symbol_a, symbol_b, params, sharpe_ratio, max_drawdown, win_rate, n_trades, total_return_pct)
                VALUES (:a, :b, :params, :sharpe, :dd, :wr, :nt, :ret)
            """),
            {
                "a": symbol_a, "b": symbol_b, "params": params,
                "sharpe": result.sharpe_ratio, "dd": result.max_drawdown,
                "wr": result.win_rate, "nt": result.n_trades, "ret": result.total_return_pct,
            },
        )


def save_recalibration(report) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO recalibration_history
                    (beta, intercept, spread_mean, spread_std, adf_pvalue, coint_pvalue,
                     is_cointegrated, half_life_periods, disabled, disable_reason)
                VALUES (:beta, :intercept, :mean, :std, :adf, :coint, :iscoint, :hl, :disabled, :reason)
            """),
            {
                "beta": report.beta, "intercept": report.intercept,
                "mean": report.spread_mean, "std": report.spread_std,
                "adf": report.adf_pvalue, "coint": report.coint_pvalue,
                "iscoint": report.is_cointegrated, "hl": report.half_life_periods,
                "disabled": report.should_disable, "reason": report.disable_reason,
            },
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_schema()

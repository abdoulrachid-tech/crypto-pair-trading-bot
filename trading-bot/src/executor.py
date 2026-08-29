"""
Mission 11 — Exécution des ordres : simulation (paper trading) ou trading réel.

Le OrderExecutor expose une interface unique (`execute`) quel que soit le mode ;
la différence entre simulation et réel est entièrement encapsulée ici, pour que
le reste du bot (main.py) n'ait pas à connaître ce détail.
"""
import csv
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .config import settings
from .signal_generator import Signal, SignalContext

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    timestamp: str
    mode: str
    signal: str
    symbol_a: str
    symbol_b: str
    price_a: float
    price_b: float
    zscore: float
    qty_a: float
    qty_b: float
    pnl: float
    order_id_a: str = ""
    order_id_b: str = ""
    note: str = ""


class OrderExecutor:
    """
    Gère la taille des positions, le délai minimum entre deux trades, et
    l'exécution effective (simulée ou réelle via CCXT).
    """

    def __init__(self, exchange=None, log_path: str = "logs/executions.csv"):
        self.exchange = exchange  # instance ccxt, requis seulement en mode "live"
        self.log_path = log_path
        self._last_trade_ts = 0.0
        self._open_entry_prices: tuple[float, float] | None = None
        self._open_qty: tuple[float, float] | None = None
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._ensure_header()

    def _ensure_header(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(asdict(ExecutionResult(
                    timestamp="", mode="", signal="", symbol_a="", symbol_b="",
                    price_a=0, price_b=0, zscore=0, qty_a=0, qty_b=0, pnl=0,
                )).keys()))
                writer.writeheader()

    def _too_soon(self) -> bool:
        return (time.time() - self._last_trade_ts) < settings.min_seconds_between_trades

    def execute(self, ctx: SignalContext) -> ExecutionResult | None:
        """Traduit un SignalContext en action concrète (ou ne fait rien si `hold`)."""
        if ctx.signal == Signal.HOLD:
            return None

        if self._too_soon():
            logger.info("Signal %s ignoré : délai minimum entre trades non écoulé", ctx.signal)
            return None

        if ctx.signal in (Signal.LONG, Signal.SHORT):
            result = self._open_position(ctx)
        else:  # CLOSE
            result = self._close_position(ctx)

        self._last_trade_ts = time.time()
        self._write_log(result)
        return result

    def _compute_quantities(self, ctx: SignalContext) -> tuple[float, float]:
        """Détermine la quantité de chaque actif pour une taille de trade en devise de cotation fixe."""
        qty_a = settings.trade_size_quote / ctx.price_a
        qty_b = settings.trade_size_quote / ctx.price_b
        return qty_a, qty_b

    def _open_position(self, ctx: SignalContext) -> ExecutionResult:
        qty_a, qty_b = self._compute_quantities(ctx)
        self._open_entry_prices = (ctx.price_a, ctx.price_b)
        self._open_qty = (qty_a, qty_b)

        side_a = "sell" if ctx.signal == Signal.SHORT else "buy"
        side_b = "buy" if ctx.signal == Signal.SHORT else "sell"

        order_id_a, order_id_b = "SIMULATED", "SIMULATED"
        if settings.is_live and self.exchange is not None:
            order_a = self.exchange.create_order(settings.symbol_a, "market", side_a, qty_a)
            order_b = self.exchange.create_order(settings.symbol_b, "market", side_b, qty_b)
            order_id_a, order_id_b = order_a.get("id", ""), order_b.get("id", "")

        logger.info("OUVERTURE %s | %s qty=%.6f @ %.2f | %s qty=%.6f @ %.2f",
                    ctx.signal, side_a, qty_a, ctx.price_a, side_b, qty_b, ctx.price_b)

        return ExecutionResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=settings.trading_mode,
            signal=ctx.signal.value,
            symbol_a=settings.symbol_a,
            symbol_b=settings.symbol_b,
            price_a=ctx.price_a,
            price_b=ctx.price_b,
            zscore=ctx.zscore,
            qty_a=qty_a,
            qty_b=qty_b,
            pnl=0.0,
            order_id_a=order_id_a,
            order_id_b=order_id_b,
            note="ouverture",
        )

    def _close_position(self, ctx: SignalContext) -> ExecutionResult:
        pnl = 0.0
        qty_a, qty_b = 0.0, 0.0

        if self._open_entry_prices and self._open_qty:
            entry_a, entry_b = self._open_entry_prices
            qty_a, qty_b = self._open_qty
            # PnL théorique = variation de valeur des deux jambes de la position
            pnl = qty_a * (ctx.price_a - entry_a) - qty_b * (ctx.price_b - entry_b)

        order_id_a, order_id_b = "SIMULATED", "SIMULATED"
        if settings.is_live and self.exchange is not None and self._open_qty:
            order_a = self.exchange.create_order(settings.symbol_a, "market", "sell", qty_a)
            order_b = self.exchange.create_order(settings.symbol_b, "market", "buy", qty_b)
            order_id_a, order_id_b = order_a.get("id", ""), order_b.get("id", "")

        logger.info("CLÔTURE position | PnL théorique = %.4f", pnl)

        self._open_entry_prices = None
        self._open_qty = None

        return ExecutionResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=settings.trading_mode,
            signal=ctx.signal.value,
            symbol_a=settings.symbol_a,
            symbol_b=settings.symbol_b,
            price_a=ctx.price_a,
            price_b=ctx.price_b,
            zscore=ctx.zscore,
            qty_a=qty_a,
            qty_b=qty_b,
            pnl=pnl,
            order_id_a=order_id_a,
            order_id_b=order_id_b,
            note="clôture",
        )

    def _write_log(self, result: ExecutionResult):
        with open(self.log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(result).keys()))
            writer.writerow(asdict(result))

"""
Mission 10 / 11 / 12 / 20 — Orchestrateur principal du bot temps réel.

Cycle exécuté toutes les `CYCLE_INTERVAL_SECONDS` secondes :
  1. Récupère les derniers prix (CCXT)
  2. Met à jour l'historique local en mémoire
  3. Recalcule spread / Z-score (et recalibre beta périodiquement)
  4. Génère un signal (long/short/close/hold)
  5. Exécute (ou simule) l'ordre correspondant
  6. Journalise, alerte, et transmet à l'API backend

Lancement : `python -m src.main` depuis le dossier trading-bot/, avec un `.env` configuré.
"""
import logging
import time
from collections import deque
from datetime import datetime, timezone

import pandas as pd

from . import api_client, monitor
from .config import settings
from .data_collector import build_exchange, fetch_ohlcv_history
from .executor import OrderExecutor
from .recalibrator import recalibrate
from .signal_generator import Signal, SignalGenerator
from .stats import compute_hedge_ratio, compute_spread

logger = logging.getLogger(__name__)

HISTORY_MAXLEN = 5000  # nombre de points conservés en mémoire pour les calculs glissants


class TradingBot:
    def __init__(self):
        self.exchange = build_exchange()
        self.executor = OrderExecutor(exchange=self.exchange)
        self.history_a = deque(maxlen=HISTORY_MAXLEN)
        self.history_b = deque(maxlen=HISTORY_MAXLEN)
        self.signal_generator: SignalGenerator | None = None
        self.last_recalibration = None
        self.peak_equity = settings.trade_size_quote * 10  # valeur de référence arbitraire pour le drawdown
        self.cumulative_pnl = 0.0

    def bootstrap_history(self, days_back: int = 10):
        """Charge un historique initial pour pouvoir calculer beta/moyenne/écart-type dès le premier cycle."""
        logger.info("Chargement de l'historique initial (%s jours)...", days_back)
        now_ms = self.exchange.milliseconds()
        since_ms = now_ms - days_back * 24 * 60 * 60 * 1000

        df_a = fetch_ohlcv_history(self.exchange, settings.symbol_a, settings.timeframe, since_ms=since_ms)
        df_b = fetch_ohlcv_history(self.exchange, settings.symbol_b, settings.timeframe, since_ms=since_ms)

        merged = pd.merge(df_a[["timestamp", "close"]], df_b[["timestamp", "close"]],
                           on="timestamp", suffixes=("_a", "_b")).dropna()

        self.history_a.extend(merged["close_a"].tolist())
        self.history_b.extend(merged["close_b"].tolist())

        self._recalibrate()
        logger.info("Historique initial chargé : %d points.", len(self.history_a))

    def _recalibrate(self):
        series_a = pd.Series(list(self.history_a))
        series_b = pd.Series(list(self.history_b))

        if len(series_a) < settings.zscore_window * 2:
            logger.warning("Historique insuffisant pour recalibrer (%d points).", len(series_a))
            return

        report = recalibrate(series_a, series_b, lookback=HISTORY_MAXLEN)

        if self.signal_generator is None:
            self.signal_generator = SignalGenerator(
                beta=report.beta, intercept=report.intercept,
                entry=settings.zscore_entry, exit_=settings.zscore_exit,
                stoploss=settings.zscore_stoploss,
            )
        else:
            self.signal_generator.update_parameters(report.beta, report.intercept)

        if report.should_disable:
            monitor.send_telegram_alert(f"🛑 Bot désactivé automatiquement : {report.disable_reason}")
            raise SystemExit(f"Arrêt du bot : {report.disable_reason}")

        self.last_recalibration = datetime.now(timezone.utc)
        api_client.push_status({"event": "recalibration", "beta": report.beta, "half_life": report.half_life_periods})

    def _should_recalibrate(self) -> bool:
        if self.last_recalibration is None:
            return True
        elapsed_hours = (datetime.now(timezone.utc) - self.last_recalibration).total_seconds() / 3600
        return elapsed_hours >= settings.recalibration_interval_hours

    def run_cycle(self):
        ticker_a = self.exchange.fetch_ticker(settings.symbol_a)
        ticker_b = self.exchange.fetch_ticker(settings.symbol_b)
        price_a, price_b = ticker_a["last"], ticker_b["last"]

        self.history_a.append(price_a)
        self.history_b.append(price_b)

        if self._should_recalibrate():
            self._recalibrate()

        spread_series = compute_spread(
            pd.Series(list(self.history_a)), pd.Series(list(self.history_b)),
            self.signal_generator.beta, self.signal_generator.intercept,
        )
        window = spread_series.tail(settings.zscore_window)
        mean, std = window.mean(), window.std()

        ctx = self.signal_generator.next(price_a, price_b, mean, std)

        monitor.check_zscore_alert(ctx.zscore)
        logger.info(
            "[%s] price_a=%.2f price_b=%.2f zscore=%+.2f signal=%s position=%d",
            datetime.now(timezone.utc).isoformat(), price_a, price_b, ctx.zscore, ctx.signal, ctx.current_position,
        )

        api_client.push_snapshot({
            "symbolA": settings.symbol_a, "symbolB": settings.symbol_b,
            "priceA": price_a, "priceB": price_b,
            "spread": float(spread_series.iloc[-1]), "zscore": ctx.zscore,
            "beta": self.signal_generator.beta,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        result = self.executor.execute(ctx)
        if result:
            self.cumulative_pnl += result.pnl
            self.peak_equity = max(self.peak_equity, self.peak_equity + self.cumulative_pnl)
            monitor.notify_execution(result.signal, result.price_a, result.price_b, result.pnl)
            monitor.check_drawdown_alert(self.peak_equity + self.cumulative_pnl, self.peak_equity)
            api_client.push_trade({
                "symbolA": result.symbol_a, "symbolB": result.symbol_b,
                "signal": result.signal, "priceA": result.price_a, "priceB": result.price_b,
                "zscore": result.zscore, "qtyA": result.qty_a, "qtyB": result.qty_b,
                "pnl": result.pnl, "mode": result.mode, "timestamp": result.timestamp,
            })

        api_client.push_log("info", "cycle_completed", {
            "zscore": ctx.zscore, "signal": ctx.signal.value, "priceA": price_a, "priceB": price_b,
        })

    def run_forever(self):
        logger.info("Démarrage du bot en mode '%s' sur %s / %s", settings.trading_mode, settings.symbol_a, settings.symbol_b)
        self.bootstrap_history()

        while True:
            try:
                self.run_cycle()
            except SystemExit:
                logger.error("Arrêt demandé par le module de recalibrage.")
                break
            except Exception as exc:  # noqa: BLE001 — on ne veut jamais planter la boucle sans le savoir
                monitor.notify_error("run_cycle", exc)

            time.sleep(settings.cycle_interval_seconds)


def _warn_if_live():
    mode_requested = settings.trading_mode.strip().lower() == "live"
    if mode_requested and not settings.is_live:
        logger.warning(
            "TRADING_MODE=live demandé mais LIVE_TRADING_CONFIRMED n'est pas à 'true' : "
            "le bot reste en SIMULATION par sécurité. Voir trading-bot/.env.example."
        )
    elif settings.is_live:
        logger.warning(
            "\n"
            "==================================================================\n"
            "  MODE LIVE ACTIF — des ordres RÉELS seront envoyés à %s.\n"
            "  Capital exposé par trade : ~%.2f (TRADE_SIZE_QUOTE) sur %s / %s.\n"
            "  Assurez-vous d'avoir validé la stratégie en simulation/backtest\n"
            "  au préalable. Ctrl+C dans les 10 prochaines secondes pour annuler.\n"
            "==================================================================",
            settings.exchange_id, settings.trade_size_quote, settings.symbol_a, settings.symbol_b,
        )
        time.sleep(10)


def main():
    monitor.setup_logging()
    _warn_if_live()
    bot = TradingBot()
    bot.run_forever()


if __name__ == "__main__":
    main()

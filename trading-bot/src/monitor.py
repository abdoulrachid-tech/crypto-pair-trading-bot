"""
Mission 12 — Suivi de la performance en production : logging et alertes.
"""
import logging
import os
from datetime import datetime, timezone

import requests

from .config import settings

logger = logging.getLogger("trading_bot")


def setup_logging(log_dir: str = "logs"):
    """Configure un logger double sortie : console + fichier journalier."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"bot_{datetime.now(timezone.utc).date()}.log")

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [file_handler, console_handler]

    return root_logger


def send_telegram_alert(message: str) -> bool:
    """Envoie une alerte Telegram si les identifiants sont configurés. Ne lève jamais d'exception."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Alerte Telegram non envoyée (identifiants absents) : %s", message)
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": settings.telegram_chat_id, "text": message}, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Échec d'envoi de l'alerte Telegram : %s", exc)
        return False


def check_zscore_alert(zscore: float, threshold: float = 5.0):
    if abs(zscore) >= threshold:
        msg = f"⚠️ ALERTE Z-SCORE ABERRANT : Z = {zscore:+.2f} (seuil = ±{threshold})"
        logger.warning(msg)
        send_telegram_alert(msg)


def check_drawdown_alert(equity: float, peak_equity: float, threshold_pct: float = 10.0):
    if peak_equity <= 0:
        return
    drawdown_pct = (peak_equity - equity) / peak_equity * 100
    if drawdown_pct >= threshold_pct:
        msg = f"🔴 ALERTE DRAWDOWN : -{drawdown_pct:.2f}% depuis le pic de capital (seuil = {threshold_pct}%)"
        logger.warning(msg)
        send_telegram_alert(msg)


def notify_execution(signal: str, price_a: float, price_b: float, pnl: float = 0.0):
    msg = (
        f"✅ ORDRE {signal.upper()} | "
        f"{settings.symbol_a} @ {price_a:.2f} | {settings.symbol_b} @ {price_b:.2f}"
    )
    if pnl:
        msg += f" | PnL = {pnl:+.4f}"
    logger.info(msg)
    if settings.is_live:
        send_telegram_alert(msg)


def notify_error(context: str, exc: Exception):
    msg = f"🛑 ERREUR [{context}] : {exc}"
    logger.error(msg)
    send_telegram_alert(msg)

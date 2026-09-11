"""
Client HTTP minimal permettant au bot Python de transmettre ses logs et trades
à l'API Express.js (backend/), qui les persiste dans MongoDB.

Volontairement "best-effort" : une panne de l'API backend ne doit jamais
interrompre l'exécution du bot (voir Mission 2 du guide — découplage des couches).
"""
import logging

import requests

from .config import settings

logger = logging.getLogger(__name__)


def _headers():
    headers = {"Content-Type": "application/json"}
    if settings.backend_api_token:
        headers["Authorization"] = f"Bearer {settings.backend_api_token}"
    return headers


def push_log(level: str, message: str, meta: dict = None) -> bool:
    try:
        resp = requests.post(
            f"{settings.backend_api_url}/bot/logs",
            json={"level": level, "message": message, "meta": meta or {}},
            headers=_headers(),
            timeout=5,
        )
        return resp.ok
    except requests.RequestException as exc:
        logger.debug("Impossible de pousser le log vers l'API backend : %s", exc)
        return False


def push_trade(trade: dict) -> bool:
    try:
        resp = requests.post(
            f"{settings.backend_api_url}/bot/trades",
            json=trade,
            headers=_headers(),
            timeout=5,
        )
        return resp.ok
    except requests.RequestException as exc:
        logger.debug("Impossible de pousser le trade vers l'API backend : %s", exc)
        return False


def push_status(status: dict) -> bool:
    try:
        resp = requests.post(
            f"{settings.backend_api_url}/bot/status",
            json=status,
            headers=_headers(),
            timeout=5,
        )
        return resp.ok
    except requests.RequestException as exc:
        logger.debug("Impossible de pousser le statut vers l'API backend : %s", exc)
        return False


def push_snapshot(snapshot: dict) -> bool:
    """Transmet un point par cycle (prix/spread/zscore), même sans trade, pour des graphes continus."""
    try:
        resp = requests.post(
            f"{settings.backend_api_url}/bot/snapshots",
            json=snapshot,
            headers=_headers(),
            timeout=5,
        )
        return resp.ok
    except requests.RequestException as exc:
        logger.debug("Impossible de pousser le snapshot vers l'API backend : %s", exc)
        return False

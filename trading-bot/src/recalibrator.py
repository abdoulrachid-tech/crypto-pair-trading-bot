"""
Mission 20 — Recalibrage automatique et maintenance continue.

Recalcule périodiquement le hedge ratio (beta), la moyenne/écart-type du spread,
et revalide la cointégration sur une fenêtre récente de données. Applique aussi
les conditions de désactivation automatique (garde-fou de sécurité).
"""
import logging
from dataclasses import dataclass

import pandas as pd

from .stats import check_cointegration, compute_spread, half_life

logger = logging.getLogger(__name__)


@dataclass
class RecalibrationReport:
    beta: float
    intercept: float
    spread_mean: float
    spread_std: float
    adf_pvalue: float
    coint_pvalue: float
    is_cointegrated: bool
    half_life_periods: float
    should_disable: bool
    disable_reason: str = ""


def recalibrate(
    price_a: pd.Series,
    price_b: pd.Series,
    lookback: int = 5000,
    max_pvalue: float = 0.05,
    max_half_life: float = 5000,
) -> RecalibrationReport:
    """
    Recalcule les paramètres de la stratégie sur les `lookback` dernières observations.

    `max_half_life` (en nombre de périodes) protège contre les paires dont le
    retour à la moyenne serait trop lent pour être exploitable en pratique.
    """
    window_a = price_a.tail(lookback)
    window_b = price_b.tail(lookback)

    coint_result = check_cointegration(window_a, window_b)
    spread = compute_spread(window_a, window_b, coint_result.beta, coint_result.intercept)
    hl = half_life(spread)

    should_disable = False
    reason = ""

    if not coint_result.is_cointegrated:
        should_disable = True
        reason = f"Cointégration invalidée (ADF p={coint_result.adf_pvalue:.3f}, EG p={coint_result.coint_pvalue:.3f})"
    elif hl > max_half_life:
        should_disable = True
        reason = f"Half-life trop élevée ({hl:.0f} périodes > seuil {max_half_life})"

    report = RecalibrationReport(
        beta=coint_result.beta,
        intercept=coint_result.intercept,
        spread_mean=float(spread.mean()),
        spread_std=float(spread.std()),
        adf_pvalue=coint_result.adf_pvalue,
        coint_pvalue=coint_result.coint_pvalue,
        is_cointegrated=coint_result.is_cointegrated,
        half_life_periods=hl,
        should_disable=should_disable,
        disable_reason=reason,
    )

    if should_disable:
        logger.warning("Recalibrage : désactivation recommandée -> %s", reason)
    else:
        logger.info(
            "Recalibrage OK : beta=%.4f, ADF p=%.4f, half-life=%.0f périodes",
            report.beta, report.adf_pvalue, report.half_life_periods,
        )

    return report

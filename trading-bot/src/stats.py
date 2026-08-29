"""
Mission 7 / 20 — Analyse statistique de la paire.

Implémente les briques mathématiques du pair trading :
- régression linéaire -> hedge ratio (beta)
- test de cointégration (Engle-Granger) et test ADF sur le spread
- Z-score glissant du spread
- half-life du retour à la moyenne (processus d'Ornstein-Uhlenbeck discrétisé)

Ces fonctions sont utilisées à la fois par le backtester (Mission 8) et par
le module de recalibrage automatique en production (Mission 20) : c'est la
même logique qui doit s'appliquer hors ligne et en temps réel.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint


@dataclass
class CointegrationResult:
    beta: float
    intercept: float
    adf_pvalue: float
    coint_pvalue: float
    is_cointegrated: bool


def compute_hedge_ratio(price_a: pd.Series, price_b: pd.Series) -> tuple[float, float]:
    """
    Régresse price_a sur price_b : price_a = intercept + beta * price_b + résidu.
    Retourne (beta, intercept). `beta` est le hedge ratio utilisé pour construire le spread.
    """
    x = sm.add_constant(price_b.values)
    model = sm.OLS(price_a.values, x).fit()
    intercept, beta = model.params[0], model.params[1]
    return float(beta), float(intercept)


def compute_spread(price_a: pd.Series, price_b: pd.Series, beta: float, intercept: float = 0.0) -> pd.Series:
    """spread_t = price_a_t - (intercept + beta * price_b_t)"""
    return price_a - (intercept + beta * price_b)


def check_cointegration(price_a: pd.Series, price_b: pd.Series) -> CointegrationResult:
    """
    Calcule le hedge ratio puis vérifie la stationnarité du spread résultant
    via un test ADF, ainsi que le test de cointégration d'Engle-Granger direct
    entre les deux séries de prix (redondant mais complémentaire comme garde-fou).
    """
    beta, intercept = compute_hedge_ratio(price_a, price_b)
    spread = compute_spread(price_a, price_b, beta, intercept)

    adf_stat, adf_pvalue, *_ = adfuller(spread.dropna(), autolag="AIC")
    _, coint_pvalue, _ = coint(price_a.values, price_b.values)

    is_cointegrated = bool(adf_pvalue < 0.05 and coint_pvalue < 0.05)

    return CointegrationResult(
        beta=beta,
        intercept=intercept,
        adf_pvalue=float(adf_pvalue),
        coint_pvalue=float(coint_pvalue),
        is_cointegrated=is_cointegrated,
    )


def rolling_zscore(spread: pd.Series, window: int = 200) -> pd.DataFrame:
    """
    Calcule la moyenne glissante, l'écart-type glissant et le Z-score du spread.
    Retourne un DataFrame avec les colonnes: spread, mean, std, zscore.
    """
    mean = spread.rolling(window=window, min_periods=window).mean()
    std = spread.rolling(window=window, min_periods=window).std()
    zscore = (spread - mean) / std
    return pd.DataFrame({"spread": spread, "mean": mean, "std": std, "zscore": zscore})


def half_life(spread: pd.Series) -> float:
    """
    Estime la half-life du retour à la moyenne via une régression AR(1) discrète
    sur le spread : delta_spread_t = lambda * spread_(t-1) + epsilon.
    half_life = -ln(2) / lambda  (lambda doit être négatif pour un vrai retour à la moyenne)
    """
    spread = spread.dropna()
    lagged = spread.shift(1).dropna()
    delta = spread.diff().dropna()
    lagged = lagged.loc[delta.index]

    x = sm.add_constant(lagged.values)
    model = sm.OLS(delta.values, x).fit()
    lam = model.params[1]

    if lam >= 0:
        return float("inf")  # pas de retour à la moyenne détectable
    return float(-np.log(2) / lam)


def rolling_correlation(price_a: pd.Series, price_b: pd.Series, window: int = 43200) -> pd.Series:
    """Corrélation glissante entre deux séries de prix (fenêtre par défaut ~30 jours en minutes)."""
    return price_a.rolling(window=window).corr(price_b)


if __name__ == "__main__":
    df = pd.read_csv("data/cleaned_pair.csv", index_col=0, parse_dates=True)
    result = check_cointegration(df["btc_close"], df["eth_close"])
    print(result)

    spread = compute_spread(df["btc_close"], df["eth_close"], result.beta, result.intercept)
    zdf = rolling_zscore(spread, window=200)
    print(zdf.tail())
    print("Half-life (périodes) :", half_life(spread))

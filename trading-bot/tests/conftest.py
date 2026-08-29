"""
Fixtures partagées pour les tests : génère une paire d'actifs synthétiques
dont le spread est volontairement construit comme un processus d'Ornstein-Uhlenbeck
(donc stationnaire par construction), afin de tester le pipeline sur un cas où
la cointégration est connue et garantie, plutôt que dépendante d'une API externe.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_ohlcv_pair():
    rng = np.random.default_rng(42)
    n = 5000
    t = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")

    log_b = np.cumsum(rng.normal(0, 0.0005, n)) + np.log(3000)
    price_b = np.exp(log_b)

    spread = np.zeros(n)
    for i in range(1, n):
        spread[i] = spread[i - 1] - 0.01 * spread[i - 1] + rng.normal(0, 1.0)

    beta_true = 15.0
    price_a = beta_true * price_b + spread

    df_a = pd.DataFrame({
        "timestamp": t, "open": price_a, "high": price_a, "low": price_a,
        "close": price_a, "volume": 1.0,
    })
    df_b = pd.DataFrame({
        "timestamp": t, "open": price_b, "high": price_b, "low": price_b,
        "close": price_b, "volume": 1.0,
    })
    return df_a, df_b, beta_true

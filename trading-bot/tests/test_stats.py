import numpy as np
import pandas as pd

from src.data_cleaner import clean_pair
from src.stats import compute_hedge_ratio, compute_spread, rolling_zscore, half_life, check_cointegration as run_cointegration_test


def test_hedge_ratio_recovers_true_beta(synthetic_ohlcv_pair):
    df_a, df_b, beta_true = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    beta, _ = compute_hedge_ratio(cleaned["a"], cleaned["b"])
    assert abs(beta - beta_true) < 1.0  # tolérance raisonnable sur données bruitées


def test_cointegration_detects_stationary_spread(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    result = run_cointegration_test(cleaned["a"], cleaned["b"])
    assert result.is_cointegrated is True
    assert result.adf_pvalue < 0.05


def test_cointegration_rejects_independent_random_walks():
    rng = np.random.default_rng(0)
    n = 3000
    x = pd.Series(np.cumsum(rng.normal(0, 1, n)) + 1000)
    y = pd.Series(np.cumsum(rng.normal(0, 1, n)) + 1000)  # totalement indépendante de x

    result = run_cointegration_test(x, y)
    # Deux marches aléatoires indépendantes ne doivent (généralement) pas être cointégrées
    assert result.adf_pvalue > 0.01


def test_rolling_zscore_has_expected_shape(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")
    beta, intercept = compute_hedge_ratio(cleaned["a"], cleaned["b"])
    spread = compute_spread(cleaned["a"], cleaned["b"], beta, intercept)

    zdf = rolling_zscore(spread, window=100)
    assert list(zdf.columns) == ["spread", "mean", "std", "zscore"]
    assert zdf["zscore"].dropna().abs().max() < 20  # pas de valeurs aberrantes de calcul


def test_half_life_is_positive_for_mean_reverting_spread(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")
    beta, intercept = compute_hedge_ratio(cleaned["a"], cleaned["b"])
    spread = compute_spread(cleaned["a"], cleaned["b"], beta, intercept)

    hl = half_life(spread)
    assert hl > 0
    assert hl < len(spread)  # une half-life plus longue que l'échantillon serait suspecte

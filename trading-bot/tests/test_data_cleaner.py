import numpy as np
import pandas as pd

from src.data_cleaner import clean_pair, remove_outliers_iqr, add_log_returns


def test_clean_pair_produces_aligned_series(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    assert len(cleaned) > 0
    assert set(["a", "b", "a_logret", "b_logret"]).issubset(cleaned.columns)
    assert cleaned.isna().sum().sum() == 0
    assert cleaned.index.is_monotonic_increasing


def test_clean_pair_handles_missing_data(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    # Simule un trou de 3 minutes dans df_b
    df_b_gappy = df_b.drop(df_b.index[100:103]).reset_index(drop=True)

    cleaned = clean_pair(df_a, df_b_gappy, name_a="a", name_b="b")
    assert len(cleaned) > 0
    assert cleaned.isna().sum().sum() == 0


def test_remove_outliers_iqr_drops_extreme_values():
    df = pd.DataFrame({"x": [10, 11, 9, 10, 12, 1000, 11, 9]})
    cleaned = remove_outliers_iqr(df, columns=["x"], k=1.5)
    assert 1000 not in cleaned["x"].values
    assert len(cleaned) == 7


def test_add_log_returns_matches_manual_calculation():
    df = pd.DataFrame({"price": [100.0, 110.0, 105.0]})
    out = add_log_returns(df, columns=["price"])
    expected = np.log(110.0 / 100.0)
    assert abs(out["price_logret"].iloc[1] - expected) < 1e-9
    assert np.isnan(out["price_logret"].iloc[0])

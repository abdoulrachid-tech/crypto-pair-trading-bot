from src.backtester import BacktestConfig, run_backtest, train_test_split_backtest
from src.data_cleaner import clean_pair


def test_backtest_runs_without_error_and_generates_trades(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    cfg = BacktestConfig(zscore_window=100, entry_threshold=2.0, exit_threshold=0.5,
                          stoploss_threshold=4.0, fee_rate=0.0001, capital=10_000, position_size_fraction=0.02)
    result = run_backtest(cleaned["a"], cleaned["b"], cfg)

    assert result.n_trades > 0
    assert len(result.equity_curve) > 0
    assert not result.trades.empty
    assert set(["entry_time", "exit_time", "direction", "pnl"]).issubset(result.trades.columns)


def test_lower_fees_improve_or_maintain_win_rate(synthetic_ohlcv_pair):
    """Vérifie la cohérence économique du moteur : moins de frais ne doit jamais nuire au win rate."""
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    cfg_high_fee = BacktestConfig(fee_rate=0.001, zscore_window=100)
    cfg_low_fee = BacktestConfig(fee_rate=0.00001, zscore_window=100)

    res_high = run_backtest(cleaned["a"], cleaned["b"], cfg_high_fee)
    res_low = run_backtest(cleaned["a"], cleaned["b"], cfg_low_fee)

    assert res_low.win_rate >= res_high.win_rate
    assert res_low.total_return_pct >= res_high.total_return_pct


def test_train_test_split_produces_two_independent_results(synthetic_ohlcv_pair):
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    cfg = BacktestConfig(zscore_window=100)
    train_res, test_res = train_test_split_backtest(cleaned["a"], cleaned["b"], cfg, train_frac=0.7)

    assert len(train_res.equity_curve) > len(test_res.equity_curve)


def test_no_trades_when_thresholds_are_unreachable(synthetic_ohlcv_pair):
    """Avec un seuil d'entrée extrêmement élevé, aucun trade ne devrait être déclenché."""
    df_a, df_b, _ = synthetic_ohlcv_pair
    cleaned = clean_pair(df_a, df_b, name_a="a", name_b="b")

    cfg = BacktestConfig(entry_threshold=1000.0, zscore_window=100)
    result = run_backtest(cleaned["a"], cleaned["b"], cfg)

    assert result.n_trades == 0
    assert result.total_return_pct == 0.0

"""
Mission 8 / 9 — Script CLI de backtesting et validation.

Usage:
    python scripts/run_backtest.py --entry 2.0 --exit 0.5 --window 200
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.backtester import BacktestConfig, train_test_split_backtest  # noqa: E402
from src.stats import check_cointegration  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Backteste la stratégie de pair trading sur les données nettoyées.")
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--entry", type=float, default=2.0)
    parser.add_argument("--exit", type=float, default=0.5)
    parser.add_argument("--stoploss", type=float, default=4.0)
    parser.add_argument("--fee", type=float, default=0.001)
    parser.add_argument("--capital", type=float, default=10_000.0)
    parser.add_argument("--data", type=str, default="data/cleaned_pair.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.data, index_col=0, parse_dates=True)
    col_a, col_b = df.columns[0], df.columns[1]

    print(f"Colonnes utilisées : {col_a}, {col_b} ({len(df)} lignes)\n")

    coint = check_cointegration(df[col_a], df[col_b])
    print("=== Test de cointégration (sur l'ensemble de la période) ===")
    print(f"beta={coint.beta:.6f} | ADF p-value={coint.adf_pvalue:.4f} | "
          f"Engle-Granger p-value={coint.coint_pvalue:.4f} | Cointégré = {coint.is_cointegrated}\n")

    cfg = BacktestConfig(
        zscore_window=args.window, entry_threshold=args.entry, exit_threshold=args.exit,
        stoploss_threshold=args.stoploss, fee_rate=args.fee, capital=args.capital,
    )

    train_res, test_res = train_test_split_backtest(df[col_a], df[col_b], cfg)

    def report(name, res):
        print(f"=== {name} ===")
        print(f"Sharpe ratio       : {res.sharpe_ratio:.2f}")
        print(f"Max drawdown       : {res.max_drawdown:.2%}")
        print(f"Nombre de trades   : {res.n_trades}")
        print(f"Taux de réussite   : {res.win_rate:.2%}")
        print(f"Rendement total    : {res.total_return_pct:.2f}%\n")

    report("In-sample (70% des données)", train_res)
    report("Out-of-sample (30% restants)", test_res)


if __name__ == "__main__":
    main()

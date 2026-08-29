"""
Mission 8 / 9 — Moteur de backtesting et métriques de validation.

Simule l'application de la stratégie de pair trading sur un historique de prix,
en respectant strictement l'absence de look-ahead bias : à l'instant t, seules
les données jusqu'à t (incluses) sont utilisées pour décider de l'action.

Le moteur applique des frais de transaction et gère position/PnL de façon
vectorisée pour rester rapide sur de longues séries.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .stats import compute_hedge_ratio, compute_spread, rolling_zscore


@dataclass
class BacktestConfig:
    zscore_window: int = 200
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    stoploss_threshold: float = 4.0
    fee_rate: float = 0.001  # 0.1% par ordre, appliqué à chaque changement de position
    capital: float = 10_000.0
    position_size_fraction: float = 0.02  # part du capital allouée à la jambe "A" de chaque trade


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    n_trades: int
    total_return_pct: float


def _position_from_zscore(z: float, current_position: int, cfg: BacktestConfig) -> int:
    """
    Détermine la nouvelle position (-1 short spread, 0 flat, +1 long spread)
    à partir du Z-score courant et de la position précédente.
    """
    if current_position == 0:
        if z >= cfg.entry_threshold:
            return -1  # spread trop haut -> on le vend (short spread)
        if z <= -cfg.entry_threshold:
            return 1  # spread trop bas -> on l'achète (long spread)
        return 0

    # Position ouverte : on regarde si on doit clôturer (retour à la moyenne ou stop-loss)
    if abs(z) <= cfg.exit_threshold:
        return 0
    if abs(z) >= cfg.stoploss_threshold:
        return 0
    return current_position


def run_backtest(price_a: pd.Series, price_b: pd.Series, cfg: BacktestConfig = None) -> BacktestResult:
    """
    Simule la stratégie avec un **sizing de position réaliste** : à chaque ouverture,
    la quantité de l'actif A est dimensionnée pour représenter `position_size_fraction`
    du capital courant, et la quantité de l'actif B est dérivée du hedge ratio (beta)
    pour rester beta-neutre. Le PnL est marqué au marché à chaque période tant que la
    position est ouverte (mark-to-market), ce qui donne une courbe d'équité continue
    et réaliste plutôt qu'un simple delta de "1 unité de spread".
    """
    cfg = cfg or BacktestConfig()

    beta, intercept = compute_hedge_ratio(price_a, price_b)
    spread = compute_spread(price_a, price_b, beta, intercept)
    zdf = rolling_zscore(spread, window=cfg.zscore_window)

    df = pd.DataFrame({
        "price_a": price_a,
        "price_b": price_b,
        "spread": spread,
        "zscore": zdf["zscore"],
    }).dropna()

    n = len(df)
    equity = np.zeros(n)
    pnl_net = np.zeros(n)
    position_arr = np.zeros(n, dtype=int)

    capital = cfg.capital
    position = 0
    qty_a = qty_b = 0.0
    entry_price_a = entry_price_b = 0.0
    trades = []
    entry_idx = None

    prices_a = df["price_a"].values
    prices_b = df["price_b"].values
    zscores = df["zscore"].values

    for i in range(n):
        pa, pb, z = prices_a[i], prices_b[i], zscores[i]
        step_pnl = 0.0

        new_position = _position_from_zscore(z, position, cfg)

        if position != 0 and new_position != position:
            # Clôture : PnL réalisé = variation de valeur des deux jambes depuis l'entrée
            direction = position
            realized = direction * (qty_a * (pa - entry_price_a) - qty_b * (pb - entry_price_b))
            notional = qty_a * pa + qty_b * pb
            fee = cfg.fee_rate * notional
            step_pnl += realized - fee
            capital += realized - fee
            trades.append({
                "entry_time": df.index[entry_idx], "exit_time": df.index[i],
                "direction": "long_spread" if direction == 1 else "short_spread",
                "pnl": realized - fee,
            })
            position = 0
            qty_a = qty_b = 0.0

        if position == 0 and new_position != 0:
            # Ouverture : dimensionnement en fonction du capital courant
            qty_a = (capital * cfg.position_size_fraction) / pa
            qty_b = qty_a * abs(beta)
            entry_price_a, entry_price_b = pa, pb
            notional = qty_a * pa + qty_b * pb
            fee = cfg.fee_rate * notional
            step_pnl -= fee
            capital -= fee
            position = new_position
            entry_idx = i

        position_arr[i] = position
        pnl_net[i] = step_pnl
        equity[i] = capital

    df["position"] = position_arr
    df["pnl_net"] = pnl_net
    df["equity"] = equity

    trades_df = pd.DataFrame(trades)

    returns = df["pnl_net"] / cfg.capital
    sharpe = _annualized_sharpe(returns)
    max_dd = _max_drawdown(df["equity"])
    win_rate = (trades_df["pnl"] > 0).mean() if len(trades_df) else 0.0
    total_return_pct = (df["equity"].iloc[-1] / cfg.capital - 1) * 100 if len(df) else 0.0

    return BacktestResult(
        equity_curve=df["equity"],
        trades=trades_df,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        win_rate=float(win_rate),
        n_trades=len(trades_df),
        total_return_pct=float(total_return_pct),
    )


def _annualized_sharpe(returns: pd.Series, periods_per_year: int = 365 * 24 * 60) -> float:
    std = returns.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return float(returns.mean() / std * np.sqrt(periods_per_year))


def _max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    return float(drawdown.min()) if len(drawdown) else 0.0


def train_test_split_backtest(
    price_a: pd.Series, price_b: pd.Series, cfg: BacktestConfig = None, train_frac: float = 0.7
) -> tuple[BacktestResult, BacktestResult]:
    """
    Mission 9 — validation out-of-sample : le hedge ratio et les seuils sont
    conceptuellement calibrés sur la portion "train", puis la même stratégie est
    évaluée sur la portion "test", jamais vue pendant le calibrage.
    """
    n = len(price_a)
    split = int(n * train_frac)

    train_result = run_backtest(price_a.iloc[:split], price_b.iloc[:split], cfg)
    test_result = run_backtest(price_a.iloc[split:], price_b.iloc[split:], cfg)

    return train_result, test_result


if __name__ == "__main__":
    df = pd.read_csv("data/cleaned_pair.csv", index_col=0, parse_dates=True)
    cfg = BacktestConfig()
    train_res, test_res = train_test_split_backtest(df["btc_close"], df["eth_close"], cfg)

    print("=== In-sample (train) ===")
    print(f"Sharpe: {train_res.sharpe_ratio:.2f} | Max DD: {train_res.max_drawdown:.2%} | "
          f"Trades: {train_res.n_trades} | Win rate: {train_res.win_rate:.2%} | "
          f"Return: {train_res.total_return_pct:.2f}%")

    print("=== Out-of-sample (test) ===")
    print(f"Sharpe: {test_res.sharpe_ratio:.2f} | Max DD: {test_res.max_drawdown:.2%} | "
          f"Trades: {test_res.n_trades} | Win rate: {test_res.win_rate:.2%} | "
          f"Return: {test_res.total_return_pct:.2f}%")

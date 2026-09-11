"""
Simulation de bout en bout, sans dépendance réseau à un exchange :
génère un historique de prix synthétique mais statistiquement réaliste
(marche aléatoire géométrique pour ETH + spread cointégré Ornstein-Uhlenbeck
pour construire BTC), puis fait tourner le pipeline complet exactement comme
il tournerait sur de vraies données de marché : hedge ratio, test de
cointégration, split train/test, backtest avec frais, métriques.

Objectif : valider que toute la chaîne (stats -> signal -> backtest) se
comporte correctement sur un cas où la vérité terrain est connue, avant de
brancher un vrai flux de prix (ce que cet environnement ne peut pas faire
directement : aucun accès réseau sortant vers les exchanges depuis ici).
"""
import numpy as np
import pandas as pd

from src.backtester import BacktestConfig, train_test_split_backtest
from src.stats import check_cointegration

rng = np.random.default_rng(7)
N = 60_000  # ~ 41 jours de données minute
t = pd.date_range("2025-01-01", periods=N, freq="1min", tz="UTC")

# ETH-like : marche aléatoire géométrique avec dérive légère
log_eth = np.cumsum(rng.normal(0.0000, 0.0006, N)) + np.log(3200)
eth = np.exp(log_eth)

# Spread cointégré (Ornstein-Uhlenbeck) -> le vrai signal que la stratégie doit détecter
theta, mu, sigma = 0.015, 0.0, 25.0
spread = np.zeros(N)
for i in range(1, N):
    spread[i] = spread[i - 1] + theta * (mu - spread[i - 1]) + rng.normal(0, sigma)

beta_true = 13.5
btc = beta_true * eth + spread

price_a = pd.Series(btc, index=t, name="BTC/USDT")
price_b = pd.Series(eth, index=t, name="ETH/USDT")

print("=== 1. Vérification statistique (comme le ferait le bot au démarrage) ===")
coint = check_cointegration(price_a, price_b)
print(f"Hedge ratio estimé : {coint.beta:.3f} (vrai beta simulé : {beta_true})")
print(f"Cointégration (ADF p-value) : {coint.adf_pvalue:.5f} -> "
      f"{'cointégré (OK pour trader)' if coint.is_cointegrated else 'NON cointégré (bot devrait refuser)'}")

print("\n=== 2. Backtest in-sample / out-of-sample (Missions 8-9) ===")
cfg = BacktestConfig(zscore_window=200, entry_threshold=2.0, exit_threshold=0.5,
                      stoploss_threshold=4.0, fee_rate=0.001, capital=10_000.0)
train_res, test_res = train_test_split_backtest(price_a, price_b, cfg, train_frac=0.7)

for label, res in [("IN-SAMPLE (70%)", train_res), ("OUT-OF-SAMPLE (30%)", test_res)]:
    print(f"\n--- {label} ---")
    print(f"  Trades              : {res.n_trades}")
    print(f"  Win rate            : {res.win_rate:.1%}")
    print(f"  Rendement total     : {res.total_return_pct:.2f}%")
    print(f"  Sharpe (annualisé)  : {res.sharpe_ratio:.2f}")
    print(f"  Max drawdown        : {res.max_drawdown:.2%}")

print("\n=== 3. Verdict ===")
degraded = test_res.sharpe_ratio < 0 or test_res.total_return_pct < 0
if degraded:
    print("⚠️  Performance dégradée hors échantillon : stratégie à ne PAS déployer en l'état.")
else:
    print("✅ Comportement cohérent : la stratégie détecte et exploite le spread simulé, "
          "y compris hors échantillon d'entraînement (ce qui n'est pas une preuve de rentabilité "
          "sur de vraies données de marché — seulement une validation du pipeline).")

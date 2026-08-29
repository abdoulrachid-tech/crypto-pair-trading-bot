"""
Mission 5 — Script CLI de collecte des données historiques.

Usage:
    python scripts/collect_data.py --days 180
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402
from src.data_collector import collect_pair_history  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Collecte l'historique OHLCV de la paire configurée.")
    parser.add_argument("--days", type=int, default=180, help="Nombre de jours d'historique à récupérer.")
    parser.add_argument("--out-dir", type=str, default="data", help="Dossier de sortie des CSV.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    df_a, df_b = collect_pair_history(days_back=args.days)

    path_a = out_dir / f"raw_{settings.symbol_a.replace('/', '_')}.csv"
    path_b = out_dir / f"raw_{settings.symbol_b.replace('/', '_')}.csv"
    df_a.to_csv(path_a, index=False)
    df_b.to_csv(path_b, index=False)

    print(f"{settings.symbol_a}: {len(df_a)} lignes -> {path_a}")
    print(f"{settings.symbol_b}: {len(df_b)} lignes -> {path_b}")


if __name__ == "__main__":
    main()

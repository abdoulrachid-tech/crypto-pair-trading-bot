"""
Mission 6 — Script CLI de nettoyage et alignement des données.

Usage:
    python scripts/clean_data.py
"""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402
from src.data_cleaner import clean_pair  # noqa: E402


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

    data_dir = Path("data")
    path_a = data_dir / f"raw_{settings.symbol_a.replace('/', '_')}.csv"
    path_b = data_dir / f"raw_{settings.symbol_b.replace('/', '_')}.csv"

    if not path_a.exists() or not path_b.exists():
        raise SystemExit(
            f"Fichiers bruts introuvables ({path_a}, {path_b}). "
            "Lancez d'abord scripts/collect_data.py."
        )

    df_a = pd.read_csv(path_a, parse_dates=["timestamp"])
    df_b = pd.read_csv(path_b, parse_dates=["timestamp"])

    name_a = settings.symbol_a.split("/")[0].lower() + "_close"
    name_b = settings.symbol_b.split("/")[0].lower() + "_close"

    cleaned = clean_pair(df_a, df_b, name_a=name_a, name_b=name_b)

    out_path = data_dir / "cleaned_pair.csv"
    cleaned.to_csv(out_path)
    print(f"Données nettoyées : {len(cleaned)} lignes -> {out_path}")
    print(cleaned.tail())


if __name__ == "__main__":
    main()

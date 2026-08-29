"""
Mission 6 — Nettoyage et préparation des données pour l'analyse.

Fonctions pures (aucun effet de bord) qui transforment des DataFrames OHLCV bruts
en une série jointe, propre, alignée en UTC et sans outliers, prête pour l'analyse
statistique (Partie 3) et le calcul du Z-score.
"""
import numpy as np
import pandas as pd


def to_close_series(df: pd.DataFrame, name: str) -> pd.Series:
    """Extrait la série de prix de clôture, indexée par timestamp UTC."""
    s = df.set_index("timestamp")["close"].rename(name)
    if s.index.tz is None:
        s.index = s.index.tz_localize("UTC")
    else:
        s.index = s.index.tz_convert("UTC")
    return s


def align_and_resample(series_a: pd.Series, series_b: pd.Series, freq: str = "1min") -> pd.DataFrame:
    """
    Uniformise la fréquence des deux séries et les fusionne par jointure interne :
    on ne conserve que les timestamps où les deux actifs ont une donnée.
    """
    a = series_a.resample(freq).last()
    b = series_b.resample(freq).last()
    merged = pd.concat([a, b], axis=1, join="inner")
    return merged


def fill_small_gaps(df: pd.DataFrame, max_gap: int = 5) -> pd.DataFrame:
    """
    Interpole linéairement les trous de taille <= max_gap points consécutifs.
    Les trous plus longs sont laissés en NaN pour être supprimés ensuite
    (on ne veut pas inventer des heures de données manquantes).
    """
    return df.interpolate(method="linear", limit=max_gap, limit_direction="both")


def drop_remaining_na(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna()


def remove_outliers_iqr(df: pd.DataFrame, columns: list[str] = None, k: float = 3.0) -> pd.DataFrame:
    """
    Supprime les lignes dont au moins une colonne dépasse [Q1 - k*IQR, Q3 + k*IQR].
    k=3.0 est volontairement conservateur (on ne veut retirer que les vrais artefacts,
    pas des mouvements de marché légitimes mais rapides).
    """
    columns = columns or list(df.columns)
    mask = pd.Series(True, index=df.index)
    for col in columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - k * iqr, q3 + k * iqr
        mask &= df[col].between(lower, upper)
    return df[mask]


def add_log_returns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Ajoute une colonne `<col>_logret` = log(P_t / P_t-1) pour chaque colonne demandée."""
    out = df.copy()
    for col in columns:
        out[f"{col}_logret"] = np.log(out[col] / out[col].shift(1))
    return out


def clean_pair(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str = "asset_a",
    name_b: str = "asset_b",
    freq: str = "1min",
    max_gap: int = 5,
    outlier_k: float = 3.0,
) -> pd.DataFrame:
    """
    Pipeline complet de nettoyage : extraction des clôtures -> alignement ->
    comblement des petits trous -> suppression des trous restants -> suppression
    des outliers -> calcul des log-returns.

    Retourne un DataFrame indexé par timestamp UTC avec les colonnes :
    <name_a>, <name_b>, <name_a>_logret, <name_b>_logret
    """
    series_a = to_close_series(df_a, name_a)
    series_b = to_close_series(df_b, name_b)

    merged = align_and_resample(series_a, series_b, freq=freq)
    merged = fill_small_gaps(merged, max_gap=max_gap)
    merged = drop_remaining_na(merged)
    merged = remove_outliers_iqr(merged, columns=[name_a, name_b], k=outlier_k)
    merged = add_log_returns(merged, columns=[name_a, name_b])
    merged = merged.dropna()

    return merged


if __name__ == "__main__":
    import sys

    a = pd.read_csv("data/raw_symbol_a.csv", parse_dates=["timestamp"])
    b = pd.read_csv("data/raw_symbol_b.csv", parse_dates=["timestamp"])
    cleaned = clean_pair(a, b, name_a="btc_close", name_b="eth_close")
    cleaned.to_csv("data/cleaned_pair.csv")
    print(f"Données nettoyées : {len(cleaned)} lignes -> data/cleaned_pair.csv", file=sys.stderr)

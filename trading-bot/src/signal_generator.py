"""
Mission 10 — Générateur de signal en temps réel.

Réutilise exactement la même logique de décision que le backtester
(src/backtester.py::_position_from_zscore) pour garantir la cohérence entre
validation historique et exécution live — un principe essentiel rappelé
dans le guide (Partie 3 / Partie 4).
"""
from dataclasses import dataclass
from enum import Enum

from .stats import compute_spread


class Signal(str, Enum):
    LONG = "long"    # long spread : acheter asset_a, vendre asset_b
    SHORT = "short"  # short spread : vendre asset_a, acheter asset_b
    CLOSE = "close"
    HOLD = "hold"


@dataclass
class SignalContext:
    price_a: float
    price_b: float
    spread: float
    zscore: float
    signal: Signal
    current_position: int  # -1, 0, 1


class SignalGenerator:
    """
    Objet à état : conserve la position actuelle du bot et applique les seuils
    de Z-score configurés pour décider de l'action à chaque nouveau cycle.
    """

    def __init__(self, beta: float, intercept: float, entry: float, exit_: float, stoploss: float):
        self.beta = beta
        self.intercept = intercept
        self.entry_threshold = entry
        self.exit_threshold = exit_
        self.stoploss_threshold = stoploss
        self.current_position = 0  # -1 short spread, 0 flat, +1 long spread

    def update_parameters(self, beta: float, intercept: float):
        """Appelé par le module de recalibrage (Mission 20) après un nouveau calcul de beta."""
        self.beta = beta
        self.intercept = intercept

    def next(self, price_a: float, price_b: float, mean: float, std: float) -> SignalContext:
        spread = price_a - (self.intercept + self.beta * price_b)

        if std is None or std == 0:
            zscore = 0.0
        else:
            zscore = (spread - mean) / std

        signal = self._decide(zscore)

        if signal == Signal.LONG:
            self.current_position = 1
        elif signal == Signal.SHORT:
            self.current_position = -1
        elif signal == Signal.CLOSE:
            self.current_position = 0

        return SignalContext(
            price_a=price_a,
            price_b=price_b,
            spread=spread,
            zscore=zscore,
            signal=signal,
            current_position=self.current_position,
        )

    def _decide(self, zscore: float) -> Signal:
        if self.current_position == 0:
            if zscore <= -self.entry_threshold:
                return Signal.LONG
            if zscore >= self.entry_threshold:
                return Signal.SHORT
            return Signal.HOLD

        # Position ouverte : clôture sur retour à la moyenne ou stop-loss
        if abs(zscore) <= self.exit_threshold or abs(zscore) >= self.stoploss_threshold:
            return Signal.CLOSE

        return Signal.HOLD

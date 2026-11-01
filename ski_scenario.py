"""Szenario: Kaufpreis B und die Verteilung der Nutzungsdauer n = 1, 2, 3, ... (Tage, vorab unbekannt)."""

from dataclasses import dataclass

import numpy as np

import ski_constants as C


def mittlere_dauer(b: int, mx: float) -> int:
    """Mittlere Nutzungsdauer m in Tagen: Vielfaches mx von B, ganzzahlig und mindestens 1."""
    return max(1, int(round(mx * b)))


def kauftag(b: int, tx: float) -> int:
    """Kauftag t in Tagen: Vielfaches tx von B, ganzzahlig und mindestens 1 (t = 1: sofort kaufen)."""
    return max(1, int(round(tx * b)))


@dataclass(frozen=True)
class Szenario:
    b: int
    kind: str
    m: int            # mittlere Dauer in Tagen (ganzzahlig, >= 1)

    def traeger(self) -> int:
        """Größte Dauer, die die Verteilung noch abbildet (Restmasse unter 1e-12 bei den geometrischen Teilen)."""
        if self.kind == "fest":
            return self.m
        if self.kind == "gleichverteilt":
            return 2 * self.m - 1
        mu = self.m if self.kind == "geometrisch" else 1.0 + C.FAKTOR_LANG * (self.m - 1)
        return int(C.TAIL_LAENGEN * mu) + 2 * self.b + 50

    def pmf(self) -> np.ndarray:
        """Wahrscheinlichkeiten P(n) für n = 1 .. traeger() (Index n − 1); summiert auf 1."""
        n_max = self.traeger()
        ns = np.arange(1, n_max + 1)
        if self.kind == "fest":
            p = np.zeros(n_max)
            p[self.m - 1] = 1.0
            return p
        if self.kind == "gleichverteilt":
            return np.full(n_max, 1.0 / n_max)
        if self.kind == "geometrisch":
            p = _geometrisch(ns, float(self.m))
        elif self.kind == "Ausreißer":
            kurz = 1.0 + (self.m - 1) / 5.0
            lang = 1.0 + C.FAKTOR_LANG * (self.m - 1)
            p = (1.0 - C.ANTEIL_LANG) * _geometrisch(ns, kurz) + C.ANTEIL_LANG * _geometrisch(ns, lang)
        else:
            raise ValueError(f"unbekanntes Szenario: {self.kind}")
        return p / p.sum()


def _geometrisch(ns: np.ndarray, mu: float) -> np.ndarray:
    """Geometrische Verteilung auf n = 1, 2, ... mit Mittel mu >= 1 (Erfolgswahrscheinlichkeit 1/mu je Tag)."""
    q = 1.0 / mu
    return q * (1.0 - q) ** (ns - 1)

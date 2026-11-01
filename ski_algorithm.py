"""Kern: Mieten oder Kaufen (Ski-Rental) mit unbekannter Nutzungsdauer.

Miete 1 je Tag, Kaufpreis B (in Tagesmieten), die Nutzung endet nach n >= 1 Tagen. Das Optimum mit Vorwissen kostet
OPT(n) = min(n, B). Eine Regel „kaufe am Tag t“ zahlt n, wenn die Nutzung vor Tag t endet, sonst (t − 1) + B.
Die Zufallsregel kauft am Tag t mit der Wahrscheinlichkeit p_t (Karlin u. a.). Alle Erwartungen sind exakt (keine Stichprobe)."""

import math

import numpy as np

# ---------------------------------------------------------------------------------------------------------------------------------
# Einzelne Kosten


def opt(n: int, b: int) -> int:
    """Kosten mit Vorwissen über die Dauer n: mieten oder gleich kaufen, je nachdem, was billiger ist."""
    return min(n, b)


def cost_threshold(t: int, n: int, b: int) -> int:
    """Kosten der Regel „kaufe am Tag t“ bei Nutzungsdauer n (t >= 1). Endet die Nutzung vor Tag t, wird nie gekauft."""
    return n if n < t else (t - 1) + b


def simulate_cost(t: int, n: int, b: int) -> int:
    """Dieselben Kosten tagweise gezählt (unabhängiger Prüfer): jeder Tag kostet 1 Miete; am Beginn von Tag t wird gekauft."""
    total, bought = 0, False
    for day in range(1, n + 1):
        if not bought and day == t:
            total += b
            bought = True
        if not bought:
            total += 1
    return total


def ratio_threshold(t: int, n: int, b: int) -> float:
    return cost_threshold(t, n, b) / opt(n, b)


def worst_case(t: int, b: int, n_max: int | None = None) -> tuple[float, int]:
    """Schlechtester Quotient der Regel „kaufe am Tag t“ über alle Dauern n = 1 .. n_max und die Dauer, bei der er auftritt.

    Der Quotient hat sein Maximum bei n = t (Kauf direkt vor dem Ende) oder, für t > B, bei n = t; für n_max genügt 2 t + b."""
    n_max = n_max or 2 * t + b
    best, at = 0.0, 1
    for n in range(1, n_max + 1):
        q = ratio_threshold(t, n, b)
        if q > best:
            best, at = q, n
    return best, at


# ---------------------------------------------------------------------------------------------------------------------------------
# Zufallsregel (Karlin u. a.)


def karlin(b: int) -> np.ndarray:
    """Kaufwahrscheinlichkeiten p_t für t = 1 .. B (Index t − 1), proportional zu (1 − 1/B)^(B − t)."""
    w = (1.0 - 1.0 / b) ** (b - np.arange(1, b + 1))
    return w / w.sum()


def random_guarantee(b: int) -> float:
    """Schlechtester erwarteter Quotient der Zufallsregel: 1 / (1 − (1 − 1/B)^B); wächst mit B gegen e/(e − 1)."""
    return 1.0 / (1.0 - (1.0 - 1.0 / b) ** b)


def det_guarantee(b: int) -> float:
    """Schlechtester Quotient der Regel „kaufe am Tag B“: 2 − 1/B."""
    return 2.0 - 1.0 / b


E_OVER_E_MINUS_1 = math.e / (math.e - 1.0)
TIE_TOL = 1e-9                                   # relative Toleranz, unter der zwei erwartete Kosten als gleich gelten
NEVER_TOL = 1e-6                                 # relative Toleranz, unter der „nie kaufen“ als beste Regel gilt
EXACT_TOL = 1e-12                                # relative Toleranz für exakte Gleichheit (Rundung)


def random_cost_curve(b: int, n_max: int) -> np.ndarray:
    """Erwartete Kosten der Zufallsregel für n = 1 .. n_max (Index n − 1). Ab n = B sind sie konstant (B + E[t] − 1)."""
    p = karlin(b)
    ts = np.arange(1, b + 1)
    out = np.empty(n_max)
    for n in range(1, n_max + 1):
        out[n - 1] = float(np.sum(p * np.where(n < ts, n, ts - 1 + b)))
    return out


# ---------------------------------------------------------------------------------------------------------------------------------
# Erwartungen über eine Verteilung der Dauer


def expected_opt(pmf: np.ndarray, b: int) -> float:
    ns = np.arange(1, len(pmf) + 1)
    return float(np.sum(pmf * np.minimum(ns, b)))


def expected_cost_all_t(pmf: np.ndarray, b: int) -> np.ndarray:
    """Erwartete Kosten der Regel „kaufe am Tag t“ für t = 1 .. N + 1 (Index t − 1; t = N + 1: nie kaufen innerhalb des Trägers).

    E(t) = Σ_{n<t} n P(n) + (t − 1 + B) P(n ≥ t), über Summen von links und rechts in einem Durchgang."""
    n_max = len(pmf)
    ns = np.arange(1, n_max + 1)
    left = np.concatenate(([0.0], np.cumsum(ns * pmf)))                 # left[t − 1] = Σ_{n<t} n P(n),  t = 1 .. N + 1
    tail = np.concatenate((np.cumsum(pmf[::-1])[::-1], [0.0]))          # tail[t − 1] = P(n ≥ t)
    ts = np.arange(1, n_max + 2)
    return left + (ts - 1 + b) * tail


def expected_cost_threshold(pmf: np.ndarray, b: int, t: int) -> float:
    t = min(t, len(pmf) + 1)
    return float(expected_cost_all_t(pmf, b)[t - 1])


def expected_cost_never(pmf: np.ndarray) -> float:
    return float(np.sum(np.arange(1, len(pmf) + 1) * pmf))


def expected_cost_random(pmf: np.ndarray, b: int) -> float:
    curve = random_cost_curve(b, min(len(pmf), b))
    n_max = len(pmf)
    head = float(np.sum(pmf[: len(curve)] * curve))
    if n_max > len(curve):
        p = karlin(b)
        const = b + float(np.sum(p * (np.arange(1, b + 1) - 1)))
        head += float(np.sum(pmf[len(curve):])) * const
    return head


def best_fixed_t(pmf: np.ndarray, b: int) -> tuple[int | None, float]:
    """Kauftag mit den kleinsten erwarteten Kosten (None = nie kaufen) und diese Kosten. Bei Gleichstand der kleinste Tag.

    Liegt „nie kaufen“ innerhalb von NEVER_TOL (relativ) am Minimum, gilt es als die beste Regel: ein Kauftag weit hinter dem Träger
    der Verteilung (etwa Tag 99 bei Mittel 5) ist numerisch nicht von „nie“ zu unterscheiden und wäre eine irreführende Angabe.
    Sind alle Regeln gleich gut (rules_tie), gilt der kleinste Tag."""
    costs = expected_cost_all_t(pmf, b)
    inner = costs[:-1]
    t = int(np.flatnonzero(inner <= inner.min() * (1.0 + TIE_TOL))[0]) + 1       # kleinster Tag unter allen (fast) gleich guten
    best = float(costs[t - 1])
    never = expected_cost_never(pmf)
    if rules_tie(pmf, b):
        return t, best
    if abs(never - best) > EXACT_TOL * best and never <= best * (1.0 + NEVER_TOL):    # „nie“ ist besser oder praktisch gleich (Kauftag hinter dem Träger)
        return None, never
    return t, best


def rules_tie(pmf: np.ndarray, b: int) -> bool:
    """Sind alle festen Regeln (jeder Kauftag und „nie kaufen“) im Erwartungswert gleich gut? (Geometrische Dauer mit Mittel B.)"""
    costs = expected_cost_all_t(pmf, b)
    return float(costs.max() - costs.min()) <= TIE_TOL * float(costs.min())



def mean_of_ratios_threshold(pmf: np.ndarray, b: int, t: int) -> float:
    """Mittel der Quotienten E[ALG/OPT] (anders als das Verhältnis der Erwartungen E[ALG]/E[OPT])."""
    ns = np.arange(1, len(pmf) + 1)
    cost = np.where(ns < t, ns, (t - 1) + b)
    return float(np.sum(pmf * cost / np.minimum(ns, b)))


# ---------------------------------------------------------------------------------------------------------------------------------
# Stufen: mehrere Optionen (Anschaffung c, Tageskosten r), z. B. Miete / Leasing / Kauf


def multi_opt(n: int, tiers: list[tuple[float, float]]) -> float:
    return min(c + r * n for c, r in tiers)


def multi_rule_cost(n: int, tiers: list[tuple[float, float]]) -> float:
    """Wechselregel: steige auf die nächste Stufe, sobald die bisherigen Kosten deren Anschaffungspreis erreicht haben.
    Tagweise; beim Wechsel wird der Anschaffungspreis der neuen Stufe zusätzlich gezahlt."""
    total, stage = 0.0, 0
    for _ in range(n):
        while stage + 1 < len(tiers) and total >= tiers[stage + 1][0]:
            stage += 1
            total += tiers[stage][0]
        total += tiers[stage][1]
    return total


def multi_worst(tiers: list[tuple[float, float]], n_max: int) -> tuple[float, int]:
    best, at = 0.0, 1
    for n in range(1, n_max + 1):
        q = multi_rule_cost(n, tiers) / multi_opt(n, tiers)
        if q > best:
            best, at = q, n
    return best, at

"""Orakel-Test ski-rental-demo / ski_rental: unabhängige Rechenwege gegen den Kern.

Orakel 1: das Spiel „Regel gegen Gegner“ als lineares Programm (scipy.linprog, HiGHS). Der Wert des Programms ist der beste schlechteste
erwartete Quotient einer Zufallsregel über Kauftage; er muss gleich der geschlossenen Formel 1/(1 − (1 − 1/B)^B) sein, und die optimale
Verteilung muss die Karlin-Verteilung des Kerns sein.
Orakel 2: exakte Bruchrechnung (fractions) für Erwartungen über eine kleine Verteilung.
Orakel 3: tagweise gezählte Kosten (simulate_cost) und eine Aufzählung aller festen Regeln für best_fixed_t.
Orakel 4: die Stufenregel gegen eine zweite, rekursive Fassung."""

from fractions import Fraction

import numpy as np
import pytest

import ski_algorithm as A


def _lp_value(b, t_max=None, n_max=None):
    """min c unter Σ_t p_t cost(t, n) ≤ c · OPT(n) für alle n, Σ p = 1, p ≥ 0: über Kauftage 1 .. t_max, Dauern 1 .. n_max."""
    linprog = pytest.importorskip("scipy.optimize").linprog
    t_max = t_max or 3 * b
    n_max = n_max or 6 * b
    cost = np.array([[A.cost_threshold(t, n, b) for t in range(1, t_max + 1)] for n in range(1, n_max + 1)], dtype=float)
    optv = np.array([A.opt(n, b) for n in range(1, n_max + 1)], dtype=float)
    a_ub = np.hstack([cost, -optv[:, None]])
    res = linprog(np.r_[np.zeros(t_max), 1.0], A_ub=a_ub, b_ub=np.zeros(n_max), A_eq=[np.r_[np.ones(t_max), 0.0]], b_eq=[1.0],
                  bounds=[(0, None)] * (t_max + 1), method="highs")
    assert res.success
    return float(res.x[-1]), res.x[:t_max]


@pytest.mark.parametrize("b", [2, 3, 4, 5, 8, 13])
def test_game_value_equals_the_closed_formula(b):
    value, _ = _lp_value(b)
    assert value == pytest.approx(A.random_guarantee(b), rel=1e-9)


@pytest.mark.parametrize("b", [2, 3, 4, 6, 10])
def test_optimal_mixed_strategy_is_the_karlin_distribution(b):
    _, p = _lp_value(b)
    assert p[:b] == pytest.approx(A.karlin(b), abs=1e-7)
    assert p[b:] == pytest.approx(0.0, abs=1e-7)


def test_deterministic_game_value_is_two_minus_one_over_b():
    # der beste Wert unter reinen Strategien: Aufzählung aller Tage und aller Dauern, ohne den Kern zu benutzen
    for b in (2, 3, 5, 9):
        best = min(
            max(
                (n if n < t else (t - 1) + b) / min(n, b)
                for n in range(1, 5 * b)
            )
            for t in range(1, 4 * b)
        )
        assert best == pytest.approx(2 - 1 / b)


def test_expected_costs_in_exact_fractions():
    # kleine Verteilung auf n = 1 .. 6 mit Gewichten 1 .. 6 (Summe 21), B = 3
    b = 3
    weights = [Fraction(n, 21) for n in range(1, 7)]
    pmf = np.array([float(w) for w in weights])
    for t in (1, 2, 3, 4, 7):
        exact = sum(w * (n if n < t else (t - 1) + b) for n, w in zip(range(1, 7), weights))
        assert A.expected_cost_threshold(pmf, b, t) == pytest.approx(float(exact), rel=1e-12)
    assert A.expected_opt(pmf, b) == pytest.approx(float(sum(w * min(n, b) for n, w in zip(range(1, 7), weights))), rel=1e-12)
    # Zufallsregel in exakten Brüchen: p_t ∝ (2/3)^(3 − t)
    raw = [Fraction(2, 3) ** (b - t) for t in range(1, b + 1)]
    p = [r / sum(raw) for r in raw]
    exact_random = sum(w * sum(pt * (n if n < t else (t - 1) + b) for t, pt in zip(range(1, b + 1), p)) for n, w in zip(range(1, 7), weights))
    assert A.expected_cost_random(pmf, b) == pytest.approx(float(exact_random), rel=1e-12)


def test_best_fixed_rule_matches_full_enumeration_on_small_instances():
    rng = np.random.default_rng(11)
    for _ in range(40):
        b = int(rng.integers(2, 7))
        pmf = rng.random(int(rng.integers(1, 20)))
        pmf /= pmf.sum()
        costs = [sum(pmf[n - 1] * A.simulate_cost(t, n, b) for n in range(1, len(pmf) + 1)) for t in range(1, len(pmf) + 2)]
        never = sum(pmf[n - 1] * n for n in range(1, len(pmf) + 1))
        t, best = A.best_fixed_t(pmf, b)
        assert best == pytest.approx(min(min(costs), never), rel=1e-12)


def _multi_cost_recursive(n, tiers, stage=0, total=0.0):
    """Zweite Fassung der Wechselregel: rekursiv über die Tage statt Schleife."""
    if n == 0:
        return total
    while stage + 1 < len(tiers) and total >= tiers[stage + 1][0]:
        stage += 1
        total += tiers[stage][0]
    return _multi_cost_recursive(n - 1, tiers, stage, total + tiers[stage][1])


@pytest.mark.parametrize("tiers", [[(0, 1), (20, 0)], [(0, 1), (10, 0.3), (40, 0)], [(0, 1), (6, 0.5), (20, 0.2), (60, 0)]])
def test_multi_tier_rule_matches_a_recursive_version(tiers):
    for n in (1, 5, 10, 21, 50, 100):
        assert A.multi_rule_cost(n, tiers) == pytest.approx(_multi_cost_recursive(n, tiers))

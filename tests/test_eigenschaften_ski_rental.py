"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für Ski-Rental gelten müssen, ohne das richtige Ergebnis zu kennen.

Jede Eigenschaft folgt aus der Definition (nicht aus dem heutigen Verhalten des Codes): Quotienten ≥ 1, Erwartungen liegen zwischen
Minimum und Maximum der Quotienten je Dauer, die Zufallsregel hat bei jeder Verteilung denselben erwarteten Quotienten, Skalierung der
Preise ändert Quotienten nicht, gleicher Seed gibt gleiche Ziehung."""

import numpy as np
import pytest

import ski_algorithm as A
import ski_constants as C
import ski_evaluation as ev
from ski_scenario import Szenario


def _random_pmf(rng, n):
    p = rng.random(n) + 0.01
    return p / p.sum()


def test_every_ratio_is_at_least_one():
    for b in (2, 5, 12):
        for t in range(1, 3 * b):
            for n in range(1, 4 * b):
                assert A.ratio_threshold(t, n, b) >= 1.0


def test_expected_ratio_is_bounded_by_the_worst_case_ratio_of_the_rule():
    rng = np.random.default_rng(21)
    for _ in range(40):
        b = int(rng.integers(2, 15))
        pmf = _random_pmf(rng, int(rng.integers(1, 60)))
        e_opt = A.expected_opt(pmf, b)
        for t in (1, b, b + 3, 2 * b):
            worst = A.worst_case(t, b)[0]
            assert A.expected_cost_threshold(pmf, b, t) / e_opt <= worst + 1e-12
        assert A.expected_cost_random(pmf, b) / e_opt <= A.random_guarantee(b) + 1e-12


def test_random_rule_has_the_same_expected_ratio_for_every_distribution():
    rng = np.random.default_rng(22)
    for _ in range(40):
        b = int(rng.integers(2, 25))
        pmf = _random_pmf(rng, int(rng.integers(1, 80)))
        assert A.expected_cost_random(pmf, b) / A.expected_opt(pmf, b) == pytest.approx(A.random_guarantee(b), rel=1e-12)


def test_point_mass_gives_the_ratio_of_that_duration():
    for b in (3, 8):
        for n in (1, b, 3 * b):
            pmf = np.zeros(n)
            pmf[n - 1] = 1.0
            for t in (1, b, 2 * b):
                assert A.expected_cost_threshold(pmf, b, t) / A.expected_opt(pmf, b) == pytest.approx(A.ratio_threshold(t, n, b))


def test_guarantees_grow_with_b_and_stay_below_their_limits():
    rand = [A.random_guarantee(b) for b in range(2, 200)]
    det = [A.det_guarantee(b) for b in range(2, 200)]
    assert all(x < y for x, y in zip(rand, rand[1:])) and all(x < y for x, y in zip(det, det[1:]))
    assert max(rand) < A.E_OVER_E_MINUS_1 and max(det) < 2.0
    assert all(r < d for r, d in zip(rand, det))                       # Zufall ist immer besser als die beste feste Regel


def test_scaling_the_tier_prices_does_not_change_the_ratio():
    tiers = [(0, 1), (10, 0.3), (40, 0)]
    scaled = [(c * 7, r * 7) for c, r in tiers]
    for n in (3, 30, 80, 150):
        assert A.multi_rule_cost(n, scaled) / A.multi_opt(n, scaled) == pytest.approx(A.multi_rule_cost(n, tiers) / A.multi_opt(n, tiers), rel=1e-12)


def test_memoryless_duration_with_mean_b_makes_every_buying_day_equal():
    b = 20
    pmf = Szenario(b, "geometrisch", b).pmf()
    costs = A.expected_cost_all_t(pmf, b)
    assert costs.max() - costs.min() < 1e-9 * costs.min()
    assert costs.min() == pytest.approx(b, rel=1e-9)                   # alle gleich dem Mittel B


def test_expected_cost_never_is_the_mean_duration():
    for kind in C.SZENARIEN:
        sc = Szenario(20, kind, 40)
        assert A.expected_cost_never(sc.pmf()) == pytest.approx(40, rel=1e-6)


def test_more_stages_never_make_the_optimum_dearer():
    base = [(0, 1), (20, 0)]
    more = [(0, 1), (10, 0.3), (20, 0)]
    for n in range(1, 200):
        assert A.multi_opt(n, more) <= A.multi_opt(n, base)


def test_same_seed_gives_the_same_draws_and_a_longer_run_extends_the_shorter():
    s = ev.Settings(20, 1.0, "gleichverteilt", 1.0, 99)
    short = ev.beispiellaeufe(s, 5)
    long = ev.beispiellaeufe(s, 12)
    assert [r["Dauer n"] for r in long][:5] == [r["Dauer n"] for r in short]


def test_costs_of_a_draw_never_fall_below_the_optimum():
    for kind in C.SZENARIEN:
        for row in ev.beispiellaeufe(ev.Settings(20, 0.5, kind, 1.0, 3), 40):
            assert row["Deine Regel"] >= row["Optimum"] and row["Break-even"] >= row["Optimum"]

"""Kern gegen Handrechnung auf der Mini-Instanz (B = 4) und gegen kleine Brute-Force-Aufzählungen."""

import numpy as np
import pytest

import ski_algorithm as A


def test_mini_instance_by_hand():
    # B = 4, Regel „kaufe am Tag 4“: Tage 1 bis 3 gemietet (n), ab n = 4 insgesamt 3 + 4 = 7; Optimum min(n, 4)
    assert [A.cost_threshold(4, n, 4) for n in range(1, 9)] == [1, 2, 3, 7, 7, 7, 7, 7]
    assert [A.opt(n, 4) for n in range(1, 9)] == [1, 2, 3, 4, 4, 4, 4, 4]
    assert A.worst_case(4, 4) == (7 / 4, 4)


def test_mini_instance_fixture_uses_the_hand_numbers(mini):
    pmf = mini.pmf()
    assert pmf.sum() == pytest.approx(1.0) and pmf[3] == 1.0
    assert A.expected_cost_threshold(pmf, 4, 4) == 7 and A.expected_opt(pmf, 4) == 4


def test_buy_on_day_one_costs_b_and_never_buying_costs_n():
    assert [A.cost_threshold(1, n, 5) for n in (1, 2, 9)] == [5, 5, 5]
    assert [A.cost_threshold(10**9, n, 5) for n in (1, 2, 9)] == [1, 2, 9]


def test_simulate_cost_agrees_with_the_formula():
    for b in (2, 3, 5, 8):
        for t in range(1, 2 * b + 2):
            for n in range(1, 3 * b + 2):
                assert A.simulate_cost(t, n, b) == A.cost_threshold(t, n, b), (b, t, n)


def test_break_even_is_the_unique_minimum_of_the_worst_ratio():
    for b in range(2, 31):
        worst = {t: A.worst_case(t, b)[0] for t in range(1, 6 * b)}
        assert min(worst, key=worst.get) == b
        assert worst[b] == pytest.approx(2 - 1 / b)
        assert sorted(worst.values())[1] > worst[b] + 1e-12            # kein zweiter Tag erreicht denselben Wert


def test_worst_ratio_by_hand_for_b_four():
    # t = 3: (2 + 4)/3 = 2; t = 5: (4 + 4)/4 = 2; t = 1: 4/1 = 4
    assert A.worst_case(3, 4)[0] == pytest.approx(2.0)
    assert A.worst_case(5, 4)[0] == pytest.approx(2.0)
    assert A.worst_case(1, 4)[0] == pytest.approx(4.0)


def test_karlin_for_b_two_by_hand():
    # B = 2: p ∝ (1/2)^(2−t): t = 1 → 1/2, t = 2 → 1; normiert 1/3 und 2/3; Garantie 1/(1 − 1/4) = 4/3
    p = A.karlin(2)
    assert p == pytest.approx([1 / 3, 2 / 3])
    assert A.random_guarantee(2) == pytest.approx(4 / 3)
    # n = 1: (1/3)·2 + (2/3)·1 = 4/3 = (4/3)·OPT(1); n = 2: (1/3)·2 + (2/3)·3 = 8/3 = (4/3)·OPT(2)
    assert A.random_cost_curve(2, 2) == pytest.approx([4 / 3, 8 / 3])


def test_random_rule_is_an_equalizer_beyond_b():
    for b in (4, 10, 20):
        curve = A.random_cost_curve(b, 3 * b)
        assert np.allclose(curve[b - 1:], curve[b - 1])
        ratios = [curve[n - 1] / A.opt(n, b) for n in range(1, 3 * b + 1)]
        assert np.allclose(ratios, A.random_guarantee(b))


def test_expected_costs_match_a_loop_over_the_distribution():
    rng = np.random.default_rng(3)
    for _ in range(20):
        b = int(rng.integers(2, 9))
        pmf = rng.random(int(rng.integers(1, 25)))
        pmf /= pmf.sum()
        for t in range(1, len(pmf) + 3):
            loop = sum(pmf[n - 1] * A.cost_threshold(t, n, b) for n in range(1, len(pmf) + 1))
            assert A.expected_cost_threshold(pmf, b, t) == pytest.approx(loop)
        assert A.expected_cost_never(pmf) == pytest.approx(sum(pmf[n - 1] * n for n in range(1, len(pmf) + 1)))
        assert A.expected_opt(pmf, b) == pytest.approx(sum(pmf[n - 1] * A.opt(n, b) for n in range(1, len(pmf) + 1)))


def test_best_fixed_t_matches_enumeration():
    rng = np.random.default_rng(4)
    for _ in range(30):
        b = int(rng.integers(2, 9))
        pmf = rng.random(int(rng.integers(2, 30)))
        pmf /= pmf.sum()
        costs = {t: A.expected_cost_threshold(pmf, b, t) for t in range(1, len(pmf) + 1)}
        never = A.expected_cost_never(pmf)
        t, best = A.best_fixed_t(pmf, b)
        assert best == pytest.approx(min(min(costs.values()), never), rel=2e-6)
        if t is not None:
            assert costs[t] == pytest.approx(best)


def test_multi_tier_by_hand():
    tiers = [(0, 1), (20, 0)]
    # n = 21: 20 Tage Miete (20), dann ist total = 20 >= c, Kauf: +20 → 40; Optimum min(21, 20) = 20 → Quotient 2
    assert A.multi_rule_cost(21, tiers) == 40 and A.multi_opt(21, tiers) == 20
    assert A.multi_rule_cost(5, tiers) == 5
    assert A.multi_worst(tiers, 100) == (2.0, 21)


def test_best_fixed_t_reports_never_instead_of_a_day_far_behind_the_support():
    from ski_scenario import Szenario
    pmf = Szenario(20, "geometrisch", 5).pmf()                 # Mittel 5 < B: je später gekauft wird, desto besser
    t, best = A.best_fixed_t(pmf, 20)
    assert t is None and best == pytest.approx(A.expected_cost_never(pmf))
    t, _ = A.best_fixed_t(Szenario(20, "geometrisch", 80).pmf(), 20)       # Mittel 80 > B: sofort kaufen
    assert t == 1
    t, _ = A.best_fixed_t(Szenario(20, "geometrisch", 20).pmf(), 20)       # Gleichstand: der kleinste Tag
    assert t == 1

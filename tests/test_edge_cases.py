"""Randfälle: kürzeste Dauer, Extremwerte der Regler, jede Verteilung summiert auf 1 und hat das gewünschte Mittel."""

import numpy as np
import pytest

import ski_algorithm as A
import ski_constants as C
import ski_evaluation as ev
from ski_scenario import Szenario, kauftag, mittlere_dauer


@pytest.mark.parametrize("kind", C.SZENARIEN)
@pytest.mark.parametrize("b,mx", [(4, 0.25), (4, 8.0), (20, 1.0), (100, 8.0)])
def test_pmf_sums_to_one_and_has_the_wanted_mean(kind, b, mx):
    m = mittlere_dauer(b, mx)
    pmf = Szenario(b, kind, m).pmf()
    assert pmf.sum() == pytest.approx(1.0, abs=1e-12) and (pmf >= 0).all()
    mean = float(np.sum(np.arange(1, len(pmf) + 1) * pmf))
    assert mean == pytest.approx(m, rel=1e-6)


def test_shortest_duration_every_scenario_is_a_point_mass_at_one():
    for kind in C.SZENARIEN:
        pmf = Szenario(4, kind, 1).pmf()
        assert pmf[0] == pytest.approx(1.0)


def test_rounding_of_the_sliders():
    assert kauftag(20, 0.0) == 1 and kauftag(20, 1.0) == 20 and kauftag(20, 3.0) == 60 and kauftag(4, 0.05) == 1
    assert mittlere_dauer(20, 0.25) == 5 and mittlere_dauer(4, 0.25) == 1 and mittlere_dauer(100, 8.0) == 800


def test_single_day_job_costs_the_optimum_for_every_rule_except_buy_on_day_one():
    # n = 1: Mieten kostet 1; Kauf am Tag 1 kostet B
    assert A.cost_threshold(2, 1, 10) == 1 and A.cost_threshold(1, 1, 10) == 10 and A.opt(1, 10) == 1


def test_all_rules_tie_for_memoryless_duration_with_mean_b():
    assert A.rules_tie(Szenario(20, "geometrisch", 20).pmf(), 20)
    assert not A.rules_tie(Szenario(20, "geometrisch", 80).pmf(), 20)
    assert not A.rules_tie(Szenario(20, "fest", 20).pmf(), 20)


def test_extreme_settings_run_and_stay_finite():
    for kind in C.SZENARIEN:
        for s in (ev.Settings(C.B_MAX, C.TX_MAX, kind, C.MX_MAX), ev.Settings(C.B_MIN, C.TX_MIN, kind, C.MX_MIN)):
            a = ev.analyse(s)
            assert all(np.isfinite(v) and v >= 1.0 - 1e-12 for v in a.ratios.values()), (kind, s)


def test_no_expected_ratio_below_one():
    for kind in C.SZENARIEN:
        for mx in (0.25, 1.0, 4.0):
            a = ev.analyse(ev.Settings(20, 0.5, kind, mx))
            assert min(a.ratios.values()) >= 1.0 - 1e-12
            assert min(a.mean_ratios.values()) >= 1.0 - 1e-12


def test_draws_are_reproducible_and_depend_on_the_seed():
    s = ev.Settings(20, 1.0, "geometrisch", 1.0, 5)
    assert ev.beispiellaeufe(s) == ev.beispiellaeufe(s)
    assert ev.beispiellaeufe(s) != ev.beispiellaeufe(ev.Settings(20, 1.0, "geometrisch", 1.0, 6))
    assert len(ev.beispiellaeufe(s)) == C.N_DRAWS

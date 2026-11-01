"""Jede Zahl aus der README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie die App.

Die Erwartungen sind exakt (keine Stichprobe, kein Seed); Rundung wie in der README (zwei oder drei Nachkommastellen)."""

import pytest

import ski_algorithm as A
import ski_constants as C
import ski_evaluation as ev


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


# --- Garantien -------------------------------------------------------------------------------------------------------------------------


def test_guarantees_in_the_readme():
    assert A.det_guarantee(4) == 1.75 and A.det_guarantee(20) == pytest.approx(1.95) and A.det_guarantee(100) == pytest.approx(1.99)
    assert A.random_guarantee(4) == pytest.approx(1.463, abs=5e-4)
    assert A.random_guarantee(10) == pytest.approx(1.535, abs=5e-4)
    assert A.random_guarantee(20) == pytest.approx(1.559, abs=5e-4)
    assert A.random_guarantee(200) == pytest.approx(1.580, abs=5e-4)
    assert A.E_OVER_E_MINUS_1 == pytest.approx(1.582, abs=5e-4)


def test_mini_instance_numbers_in_the_readme():
    assert A.cost_threshold(4, 4, 4) == 7 and A.opt(4, 4) == 4 and 7 / 4 == 1.75
    a = _a("Mini-Instanz von Hand (B = 4)")
    assert a.worst == 1.75 and a.worst_at == 4 and a.ratios["Break-even"] == pytest.approx(1.75)
    assert a.ratios["Zufall"] == pytest.approx(1.463, abs=5e-4)


def test_buying_on_day_one_has_the_worst_ratio_b():
    assert A.worst_case(1, 20)[0] == pytest.approx(20.0) and A.worst_case(1, 20)[1] == 1


# --- Typischer Fall (Presets) ----------------------------------------------------------------------------------------------------------


def test_short_orders_table():
    a = _a("Kurze Aufträge")
    r = a.ratios
    assert (a.settings.m, round(a.p_beyond * 100)) == (5, 1)
    assert r["Break-even"] == pytest.approx(1.055, abs=5e-4) and r["Nie kaufen"] == pytest.approx(1.012, abs=5e-4)
    assert r["Sofort kaufen"] == pytest.approx(4.047, abs=5e-4) and r["Zufall"] == pytest.approx(1.559, abs=5e-4)
    assert a.best_t is None and a.best_ratio == pytest.approx(1.012, abs=5e-4)


def test_medium_orders_table():
    a = _a("Stapler (B = 20, mittlere Aufträge)")
    r = a.ratios
    assert (a.settings.m, round(a.p_beyond * 100)) == (20, 51)
    assert r["Break-even"] == pytest.approx(1.644, abs=5e-4) and r["Sofort kaufen"] == pytest.approx(1.322, abs=5e-4)
    assert r["Nie kaufen"] == pytest.approx(1.322, abs=5e-4)                    # Mittel gleich B: sofort kaufen und nie kaufen zahlen gleich viel
    assert r["Zufall"] == pytest.approx(1.559, abs=5e-4)
    assert a.best_t == 1 and a.best_ratio == pytest.approx(1.322, abs=5e-4)


def test_long_orders_table_break_even_is_close_to_its_guarantee_without_an_adversary():
    a = _a("Lange Aufträge")
    r = a.ratios
    assert (a.settings.m, round(a.p_beyond * 100)) == (80, 88)
    assert r["Break-even"] == pytest.approx(1.890, abs=5e-4) and a.guarantee == pytest.approx(1.95)
    assert r["Break-even"] > 0.95 * a.guarantee                                  # „nahe an der Garantie“ = mehr als 95 %
    assert r["Sofort kaufen"] == pytest.approx(1.064, abs=5e-4) and r["Nie kaufen"] == pytest.approx(4.254, abs=5e-4)
    assert a.best_t == 1


def test_buy_at_once_with_outliers_table():
    a = _a("Sofort kaufen, Ausreißer")
    r = a.ratios
    assert a.settings.t == 1 and a.worst == pytest.approx(20.0)
    assert r["Deine Regel"] == pytest.approx(3.245, abs=5e-4) and r["Break-even"] == pytest.approx(1.306, abs=5e-4)
    assert a.best_t == 17 and a.best_ratio == pytest.approx(1.294, abs=5e-4)
    assert round(a.p_beyond * 100) == 10


def test_mean_of_ratios_differs_strongly_from_the_ratio_of_expectations():
    a = _a("Kurze Aufträge")
    assert a.ratios["Sofort kaufen"] == pytest.approx(4.047, abs=5e-4) and a.mean_ratios["Sofort kaufen"] == pytest.approx(8.049, abs=5e-4)


def test_random_rule_is_the_same_in_every_preset():
    assert {round(_a(n).ratios["Zufall"], 3) for n in C.PRESETS if _a(n).settings.b == 20} == {1.559}


def test_memoryless_tie_at_mean_b():
    pmf = ev.Szenario(20, "geometrisch", 20).pmf()
    costs = A.expected_cost_all_t(pmf, 20)
    assert costs.min() == pytest.approx(20.0, rel=1e-9) and costs.max() == pytest.approx(20.0, rel=1e-9)
    assert A.expected_cost_never(pmf) == pytest.approx(20.0, rel=1e-6)


# --- Falsch geschätzte Dauer ----------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind,worst,be_max", [("fest", 4.00, 1.95), ("gleichverteilt", 4.254, 1.890), ("geometrisch", 4.496, 1.841), ("Ausreißer", 1.559, 1.567)])
def test_misestimated_mean_table(kind, worst, be_max):
    m = ev.fehlschaetzung(20, kind)
    assert m["ms"] == [5, 20, 80]
    assert max(q for row in m["abgestimmt"].values() for q in row.values()) == pytest.approx(worst, abs=5e-4)
    assert max(m["Break-even"].values()) == pytest.approx(be_max, abs=5e-4)
    assert max(m["Zufall"].values()) == pytest.approx(1.559, abs=5e-4)


def test_misestimated_mean_worst_case_is_the_short_world_rule_in_the_long_world():
    for kind in ("fest", "gleichverteilt", "geometrisch"):
        m = ev.fehlschaetzung(20, kind)
        assert m["t"][5] is None and m["abgestimmt"][5][80] == max(q for row in m["abgestimmt"].values() for q in row.values())


def test_outlier_scenario_hardly_punishes_misestimation():
    m = ev.fehlschaetzung(20, "Ausreißer")
    assert max(q for row in m["abgestimmt"].values() for q in row.values()) < 1.6
    assert m["t"] == {5: 8, 20: 17, 80: 11}


# --- Stufen ----------------------------------------------------------------------------------------------------------------------------


def test_tier_table():
    rows = ev.stufen_tabelle()
    assert [(r["Stufen"], r["bei Dauer n"]) for r in rows] == [(2, 21), (3, 78), (4, 123)]
    assert [round(r["schlechtester Quotient"], 2) for r in rows] == [2.00, 2.40, 2.69]
    assert C.STUFEN_N_MAX == 600                                                # „Dauern bis 600 Tage“ in der README


def test_best_fixed_rule_for_geometric_duration_is_always_a_corner():
    # E[Kosten](t) = m + (B − m)(1 − 1/m)^(t−1) ist monoton in t: der beste Kauftag ist sofort (m > B) oder nie (m < B); bei m = B Gleichstand
    for m in (2, 5, 10, 19, 21, 40, 80, 160):
        t, _ = A.best_fixed_t(ev.Szenario(20, "geometrisch", m).pmf(), 20)
        assert t == (1 if m > 20 else None), m
    t, _ = A.best_fixed_t(ev.Szenario(20, "geometrisch", 20).pmf(), 20)
    assert t == 1 and A.rules_tie(ev.Szenario(20, "geometrisch", 20).pmf(), 20)

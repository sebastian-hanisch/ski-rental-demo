"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); tests/test_verdicts.py prüft jede Zahl darin."""

from dataclasses import dataclass

import numpy as np

import ski_algorithm as A
import ski_constants as C
from ski_scenario import Szenario, kauftag, mittlere_dauer

REGELN = ("Deine Regel", "Break-even", "Sofort kaufen", "Nie kaufen", "Zufall")


@dataclass(frozen=True)
class Settings:
    b: int = C.DEFAULT_B
    tx: float = C.DEFAULT_TX
    szenario: str = C.DEFAULT_SZENARIO
    mx: float = C.DEFAULT_MX
    seed: int = C.DEFAULT_SEED

    @property
    def t(self) -> int:
        return kauftag(self.b, self.tx)

    @property
    def m(self) -> int:
        return mittlere_dauer(self.b, self.mx)


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    worst: float                 # schlechtester Quotient der Regel „kaufe am Tag t“
    worst_at: int                # bei dieser Dauer tritt er auf
    guarantee: float             # 2 − 1/B
    random_guarantee: float      # 1/(1 − (1 − 1/B)^B)
    ratios: dict                 # Regel -> E[ALG]/E[OPT] im Szenario
    mean_ratios: dict            # Regel -> E[ALG/OPT] im Szenario (Mittel der Quotienten)
    best_t: int | None           # beste feste Regel im Szenario (None = nie kaufen)
    best_ratio: float
    p_beyond: float              # P(n >= B): Anteil der Aufträge, die den Break-even-Kauf auslösen
    tie: bool                    # alle festen Regeln im Szenario gleich gut (geometrisch mit Mittel B)


def ratio_of_expectations(cost: float, opt_cost: float) -> float:
    """Verhältnis der Erwartungen E[ALG]/E[OPT]; ohne Optimumkosten (kann nicht vorkommen, n >= 1) ist 1 der neutrale Wert."""
    return 1.0 if opt_cost <= 0 else cost / opt_cost


def analyse(s: Settings) -> Analysis:
    sc = Szenario(s.b, s.szenario, s.m)
    pmf = sc.pmf()
    e_opt = A.expected_opt(pmf, s.b)
    t = s.t
    ratios = {
        "Deine Regel": ratio_of_expectations(A.expected_cost_threshold(pmf, s.b, t), e_opt),
        "Break-even": ratio_of_expectations(A.expected_cost_threshold(pmf, s.b, s.b), e_opt),
        "Sofort kaufen": ratio_of_expectations(A.expected_cost_threshold(pmf, s.b, 1), e_opt),
        "Nie kaufen": ratio_of_expectations(A.expected_cost_never(pmf), e_opt),
        "Zufall": ratio_of_expectations(A.expected_cost_random(pmf, s.b), e_opt),
    }
    mean_ratios = {
        "Deine Regel": A.mean_of_ratios_threshold(pmf, s.b, t),
        "Break-even": A.mean_of_ratios_threshold(pmf, s.b, s.b),
        "Sofort kaufen": A.mean_of_ratios_threshold(pmf, s.b, 1),
        "Nie kaufen": A.mean_of_ratios_threshold(pmf, s.b, len(pmf) + 1),
    }
    best_t, best_cost = A.best_fixed_t(pmf, s.b)
    worst, at = A.worst_case(t, s.b)
    return Analysis(
        s, worst, at, A.det_guarantee(s.b), A.random_guarantee(s.b), ratios, mean_ratios, best_t,
        ratio_of_expectations(best_cost, e_opt), float(np.sum(pmf[s.b - 1:])), A.rules_tie(pmf, s.b),
    )


def curves(s: Settings, n_max: int | None = None) -> dict:
    """Kosten und Quotienten über die Dauer n = 1 .. n_max für die Kurven der App."""
    n_max = n_max or max(3 * s.b, 2 * s.t + s.b)
    ns = list(range(1, n_max + 1))
    rand = A.random_cost_curve(s.b, min(n_max, s.b))
    rand_full = [float(rand[min(n, s.b) - 1]) for n in ns]
    return {
        "n": ns,
        "opt": [A.opt(n, s.b) for n in ns],
        "rent": ns,
        "alg": [A.cost_threshold(s.t, n, s.b) for n in ns],
        "break_even": [A.cost_threshold(s.b, n, s.b) for n in ns],
        "random": rand_full,
    }


def fehlschaetzung(b: int, szenario: str, mxs=C.MX_FALSCH) -> dict:
    """Matrix: auf die mittlere Dauer X abgestimmt (beste feste Regel), läuft bei der mittleren Dauer Y; Form der Verteilung wie gewählt.

    Spalten und Zeilen sind die mittleren Dauern in Tagen (aus mxs, in Vielfachen von B). Dazu Break-even und die Zufallsregel.
    Rückgabe: {"ms": [...], "abgestimmt": {X: {Y: Quotient}}, "t": {X: t oder None}, "tie": {X: bool}, "Break-even": {Y: q}, "Zufall": {Y: q}}."""
    ms = [mittlere_dauer(b, mx) for mx in mxs]
    pmfs = {m: Szenario(b, szenario, m).pmf() for m in ms}
    e_opt = {m: A.expected_opt(p, b) for m, p in pmfs.items()}
    tuned, tuned_t = {}, {}
    ties = {x: A.rules_tie(pmfs[x], b) for x in ms}
    for x in ms:
        t, _ = A.best_fixed_t(pmfs[x], b)
        tuned_t[x] = t
        tuned[x] = {}
        for y in ms:
            cost = A.expected_cost_never(pmfs[y]) if t is None else A.expected_cost_threshold(pmfs[y], b, t)
            tuned[x][y] = ratio_of_expectations(cost, e_opt[y])
    return {
        "ms": ms, "abgestimmt": tuned, "t": tuned_t, "tie": ties,
        "Break-even": {y: ratio_of_expectations(A.expected_cost_threshold(pmfs[y], b, b), e_opt[y]) for y in ms},
        "Zufall": {y: ratio_of_expectations(A.expected_cost_random(pmfs[y], b), e_opt[y]) for y in ms},
    }


def delta_text(value: float, reference: float, label: str) -> tuple[str, str]:
    """Text und Farbregel des Deltas einer Kennzahl: „mein Wert minus Referenz“. Ein auf zwei Stellen gleicher Wert bekommt keinen Pfeil und keine Farbe."""
    d = value - reference
    if abs(d) < 0.005:
        return f"gleich wie {label}", "off"
    return f"{d:+.2f} gegen {label}", "inverse"


def worst_of_row(row: dict) -> float:
    return max(row.values())


def beispiellaeufe(s: Settings, k: int = C.N_DRAWS) -> list[dict]:
    """k gezogene Nutzungsdauern (fester Seed) mit den Kosten der Regeln; die Spalten „Optimum“ und „Quotient“ je Zeile."""
    pmf = Szenario(s.b, s.szenario, s.m).pmf()
    rng = np.random.default_rng(s.seed)
    draws = rng.choice(np.arange(1, len(pmf) + 1), size=k, p=pmf)
    rows = []
    for n in draws:
        n = int(n)
        opt = A.opt(n, s.b)
        alg = A.cost_threshold(s.t, n, s.b)
        rows.append({"Dauer n": n, "Optimum": opt, "Deine Regel": alg, "Break-even": A.cost_threshold(s.b, n, s.b),
                     "Quotient deiner Regel": alg / opt})
    return rows


def stufen_tabelle(n_max: int = C.STUFEN_N_MAX) -> list[dict]:
    rows = []
    for name, tiers in C.PREISLISTEN.items():
        worst, at = A.multi_worst(tiers, n_max)
        rows.append({"Preisliste": name, "Stufen": len(tiers), "schlechtester Quotient": worst, "bei Dauer n": at})
    return rows


# ---------------------------------------------------------------------------------------------------------------------------------
# Verdikte (rein: Art, Text)


def verdict_gegner(a: Analysis) -> tuple[str, str]:
    """Kernfrage 1: Was kostet die Regel im schlimmsten Fall, und wo ist sie am besten?"""
    t, b = a.settings.t, a.settings.b
    if t == b:
        return "success", (f"Der Kauf am Tag {b} (Break-even) kostet im schlimmsten Fall das **{a.worst:.2f}-Fache** des Optimums, nämlich bei Dauer n = {a.worst_at}. "
                           f"Das ist die kleinste Garantie, die eine feste Regel haben kann (2 − 1/B = {a.guarantee:.2f}); die Zufallsregel kommt auf {a.random_guarantee:.2f}.")
    return "warning", (f"Der Kauf am Tag {t} kostet im schlimmsten Fall das **{a.worst:.2f}-Fache** des Optimums (bei Dauer n = {a.worst_at}); "
                  f"der Kauf am Tag {b} (Break-even) käme auf {a.guarantee:.2f}, die Zufallsregel auf {a.random_guarantee:.2f}.")


def verdict_typisch(a: Analysis) -> tuple[str, str]:
    """Kernfrage 2: Was kostet die Regel im Szenario, verglichen mit ihrer Garantie?"""
    own = a.ratios["Deine Regel"]
    be = a.ratios["Break-even"]
    rnd = a.ratios["Zufall"]
    best = "nie kaufen" if a.best_t is None else f"Kauf am Tag {a.best_t}"
    best_phrase = f"jede feste Regel {a.best_ratio:.2f} (Gleichstand, die Dauer ist ohne Gedächtnis)" if a.tie else f"die beste feste Regel ({best}) {a.best_ratio:.2f}"
    if a.settings.t == a.settings.b:
        return "info", (f"Im Szenario „{a.settings.szenario}“ mit Mittel m = {a.settings.m} Tage zahlt Break-even im Mittel das **{be:.2f}-Fache** des Optimums "
                        f"(Garantie {a.guarantee:.2f}); die Zufallsregel zahlt {rnd:.2f}, {best_phrase}. "
                        f"{a.p_beyond * 100:.0f} % der Aufträge dauern mindestens B = {a.settings.b} Tage und lösen den Kauf aus.")
    return "info", (f"Im Szenario „{a.settings.szenario}“ mit Mittel m = {a.settings.m} Tage zahlt der Kauf am Tag {a.settings.t} im Mittel das **{own:.2f}-Fache** des Optimums, "
                    f"Break-even {be:.2f}, die Zufallsregel {rnd:.2f}, {best_phrase}. "
                    f"{a.p_beyond * 100:.0f} % der Aufträge dauern mindestens B = {a.settings.b} Tage.")


def verdict_fehlschaetzung(m: dict, b: int) -> tuple[str, str]:
    """Kernfrage 3: Was kostet eine falsch geschätzte mittlere Dauer gegenüber der Garantie?"""
    ms = m["ms"]
    x, y, q = max(((x, y, m["abgestimmt"][x][y]) for x in ms for y in ms), key=lambda e: e[2])
    t = m["t"][x]
    regel = "nie kaufen" if t is None else f"kaufe am Tag {t}"
    be_worst = worst_of_row(m["Break-even"])
    rnd_worst = worst_of_row(m["Zufall"])
    return "warning", (f"Eine Regel, die auf eine mittlere Dauer von {x} Tagen abgestimmt ist ({regel}), zahlt bei einer mittleren Dauer von {y} Tagen das **{q:.2f}-Fache** des Optimums. "
                       f"Break-even bleibt über alle drei Dauern bei höchstens {be_worst:.2f} (Garantie {A.det_guarantee(b):.2f}), die Zufallsregel bei höchstens {rnd_worst:.2f}.")


def verdict_zufall(b: int) -> tuple[str, str]:
    """Kernfrage 4: Was kauft die Zufallsregel, und was nicht?"""
    g_r, g_d = A.random_guarantee(b), A.det_guarantee(b)
    return "info", (f"Die Zufallsregel zahlt bei **jeder** Dauer im Mittel das {g_r:.3f}-Fache des Optimums (deterministisch im schlimmsten Fall {g_d:.3f}); "
                    f"der Grenzwert für große B ist e/(e − 1) = {A.E_OVER_E_MINUS_1:.3f}. Sie kauft Gleichmäßigkeit, keinen Vorteil bei günstigen Dauern.")


def verdict_stufen(rows: list[dict]) -> tuple[str, str]:
    """Kernfrage 5: Wie wirkt sich eine weitere Stufe auf die Wechselregel aus?"""
    first, last = rows[0], rows[-1]
    return "info", (f"Bei {first['Stufen']} Stufen zahlt die Wechselregel im schlimmsten Fall das {first['schlechtester Quotient']:.2f}-Fache des Optimums, "
                    f"bei {last['Stufen']} Stufen das {last['schlechtester Quotient']:.2f}-Fache (Dauer n = {last['bei Dauer n']}). "
                    "Das gilt für diese drei Preislisten und diese Wechselregel, nicht für die beste Regel.")

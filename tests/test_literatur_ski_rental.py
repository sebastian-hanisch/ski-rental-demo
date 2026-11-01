"""Literatur-Referenzwerte (ORACLE-PLAYBOOK §5.1).

Stand der Einsicht: 2026-11-01, **Websuche-Auszüge und Sekundärdarstellungen**, die Volltexte wurden nicht eingesehen (in der README unter „offen“).

- Karlin, Manasse, McGeoch, Owicki: *Competitive randomized algorithms for non-uniform problems*, Algorithmica 11 (1994) 542–571 (Konferenz
  SODA 1990). Aus den Auszügen: die Zufallsregel erreicht erwartet höchstens e/(e − 1) ≈ 1,58 mal die Kosten mit Vorwissen, und kein Zufallsverfahren
  ist besser; der Kauftag d aus {1, …, B} wird mit Wahrscheinlichkeit etwa (1 − 1/B)^(B − d) / (B (1 − 1/e)) gezogen (Vorlesungsnotiz, Näherung für große B).
- Die beste deterministische Regel hat Faktor 2 (Auszug eines späteren Aufsatzes, der „Karlin u. a. 1988“ zitiert); hier ist es 2 − 1/B für endliches B."""

import math

import pytest

import ski_algorithm as A


def test_limit_of_the_randomized_ratio_is_e_over_e_minus_one():
    assert A.E_OVER_E_MINUS_1 == pytest.approx(1.5820, abs=5e-5)         # e/(e−1) ≈ 1,58 (Auszug)
    assert A.random_guarantee(200000) == pytest.approx(math.e / (math.e - 1), rel=1e-5)


def test_karlin_probabilities_match_the_published_approximation_for_large_b():
    b = 5000
    p = A.karlin(b)
    for d in (1, 1000, 4000, 5000):
        approx = (1 - 1 / b) ** (b - d) / (b * (1 - 1 / math.e))
        assert p[d - 1] == pytest.approx(approx, rel=2e-3)                # Näherung ist von der Ordnung 1/(2B)


def test_deterministic_factor_two_is_the_limit():
    assert A.det_guarantee(10**6) == pytest.approx(2.0, abs=2e-6)
    assert all(A.det_guarantee(b) < 2.0 for b in range(2, 1000))

"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Verzweigung steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text). Die Tests geben ihr Analyse-Objekte mit gesetzten Werten und prüfen die Art und jede genannte Zahl."""

import ski_evaluation as ev


def _analysis(t_tag=20, b=20, worst=1.95, worst_at=20, ratios=None, best_t=1, best_ratio=1.32, p_beyond=0.513, tie=False, szenario="gleichverteilt", m=20):
    s = ev.Settings(b, t_tag / b, szenario, m / b)
    ratios = ratios or {"Deine Regel": 1.644, "Break-even": 1.644, "Sofort kaufen": 1.322, "Nie kaufen": 1.322, "Zufall": 1.559}
    return ev.Analysis(s, worst, worst_at, 2 - 1 / b, 1.559, ratios, {}, best_t, best_ratio, p_beyond, tie)


def test_gegner_break_even_is_a_success_and_names_the_numbers():
    kind, text = ev.verdict_gegner(_analysis(t_tag=20, worst=1.95, worst_at=20))
    assert kind == "success"
    assert "Der Kauf am Tag 20 (Break-even) kostet" in text
    assert "**1.95-Fache**" in text and "n = 20" in text and "2 − 1/B = 1.95" in text and "Zufallsregel kommt auf 1.56" in text


def test_gegner_other_day_is_a_warning_and_names_break_even_and_random():
    kind, text = ev.verdict_gegner(_analysis(t_tag=10, worst=2.9, worst_at=10))
    assert kind == "warning"
    assert "Der Kauf am Tag 10 kostet" in text and "**2.90-Fache**" in text and "n = 10" in text
    assert "Tag 20 (Break-even) käme auf 1.95" in text and "Zufallsregel auf 1.56" in text


def test_typisch_for_break_even_names_garantie_zufall_best_and_share():
    kind, text = ev.verdict_typisch(_analysis())
    assert kind == "info"
    assert "„gleichverteilt“ mit Mittel m = 20 Tage" in text and "**1.64-Fache**" in text and "(Garantie 1.95)" in text
    assert "Zufallsregel zahlt 1.56" in text and "(Kauf am Tag 1) 1.32" in text and "51 % der Aufträge dauern mindestens B = 20 Tage und lösen den Kauf aus" in text


def test_typisch_for_another_day_names_the_own_rule():
    a = _analysis(t_tag=5, ratios={"Deine Regel": 2.31, "Break-even": 1.5, "Sofort kaufen": 1.0, "Nie kaufen": 3.0, "Zufall": 1.559}, p_beyond=0.2)
    kind, text = ev.verdict_typisch(a)
    assert "Kauf am Tag 5 im Mittel das **2.31-Fache**" in text and "Break-even 1.50" in text and "20 % der Aufträge dauern mindestens B = 20 Tage." in text


def test_typisch_best_rule_never_buy_and_tie_wording():
    _, text = ev.verdict_typisch(_analysis(best_t=None, best_ratio=1.01))
    assert "(nie kaufen) 1.01" in text
    _, text = ev.verdict_typisch(_analysis(tie=True, best_ratio=1.56))
    assert "jede feste Regel 1.56 (Gleichstand" in text and "beste feste Regel" not in text


def _matrix(tuned, t, be, rnd, ms=(5, 20, 80)):
    return {"ms": list(ms), "abgestimmt": tuned, "t": t, "tie": {m: False for m in ms}, "Break-even": be, "Zufall": rnd}


def test_fehlschaetzung_names_the_worst_pair_and_the_row_maxima():
    m = _matrix(
        {5: {5: 1.0, 20: 1.0, 80: 4.0}, 20: {5: 3.9, 20: 1.0, 80: 1.0}, 80: {5: 3.9, 20: 1.1, 80: 1.0}},
        {5: None, 20: 1, 80: 7},
        {5: 1.05, 20: 1.6, 80: 1.84}, {5: 1.56, 20: 1.56, 80: 1.56},
    )
    kind, text = ev.verdict_fehlschaetzung(m, 20)
    assert kind == "warning"
    assert "auf eine mittlere Dauer von 5 Tagen abgestimmt ist (nie kaufen)" in text and "bei einer mittleren Dauer von 80 Tagen das **4.00-Fache**" in text
    assert "höchstens 1.84 (Garantie 1.95)" in text and "Zufallsregel bei höchstens 1.56" in text


def test_fehlschaetzung_names_the_buying_day_of_the_tuned_rule():
    m = _matrix({5: {5: 1.0, 20: 1.2, 80: 1.3}, 20: {5: 5.5, 20: 1.0, 80: 1.0}, 80: {5: 1.0, 20: 1.0, 80: 1.0}}, {5: 3, 20: 17, 80: 1},
                {5: 1.0, 20: 1.0, 80: 1.0}, {5: 1.5, 20: 1.5, 80: 1.5})
    _, text = ev.verdict_fehlschaetzung(m, 20)
    assert "von 20 Tagen abgestimmt ist (kaufe am Tag 17)" in text and "bei einer mittleren Dauer von 5 Tagen das **5.50-Fache**" in text


def test_zufall_names_both_guarantees_and_the_limit():
    kind, text = ev.verdict_zufall(20)
    assert kind == "info"
    assert "das 1.559-Fache" in text and "deterministisch im schlimmsten Fall 1.950" in text and "e/(e − 1) = 1.582" in text


def test_stufen_names_first_and_last_row():
    rows = [{"Stufen": 2, "schlechtester Quotient": 2.0, "bei Dauer n": 21}, {"Stufen": 3, "schlechtester Quotient": 2.4, "bei Dauer n": 78},
            {"Stufen": 4, "schlechtester Quotient": 2.69, "bei Dauer n": 123}]
    kind, text = ev.verdict_stufen(rows)
    assert kind == "info"
    assert "Bei 2 Stufen" in text and "das 2.00-Fache" in text and "bei 4 Stufen das 2.69-Fache (Dauer n = 123)" in text and "nicht für die beste Regel" in text


def test_delta_text_is_mine_minus_reference_with_inverse_colour():
    assert ev.delta_text(1.64, 1.55, "Break-even") == ("+0.09 gegen Break-even", "inverse")
    assert ev.delta_text(1.50, 1.59, "Break-even") == ("-0.09 gegen Break-even", "inverse")


def test_delta_text_without_a_difference_has_no_arrow_and_no_colour():
    assert ev.delta_text(1.644, 1.644, "Break-even") == ("gleich wie Break-even", "off")
    assert ev.delta_text(1.6449, 1.6401, "Break-even") == ("gleich wie Break-even", "off")        # Differenz unter 0,005
    assert ev.delta_text(1.65, 1.64, "Break-even")[1] == "inverse"

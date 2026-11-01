"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink; Fehlschätzungs-Experiment über feste Mittel."""

import ski_constants as C
import ski_evaluation as ev
import ski_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.B_MIN <= preset["b"] <= C.B_MAX and C.TX_MIN <= preset["tx"] <= C.TX_MAX and C.MX_MIN <= preset["mx"] <= C.MX_MAX
        assert preset["szenario"] in C.SZENARIEN and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Stapler (B = 20, mittlere Aufträge)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_slider_defaults_are_inside_their_bounds_and_on_the_step_grid():
    assert C.B_MIN <= C.DEFAULT_B <= C.B_MAX and C.DEFAULT_SZENARIO in C.SZENARIEN
    for lo, hi, default, step in ((C.TX_MIN, C.TX_MAX, C.DEFAULT_TX, C.TX_STEP), (C.MX_MIN, C.MX_MAX, C.DEFAULT_MX, C.MX_STEP)):
        assert lo <= default <= hi and abs((default - lo) / step - round((default - lo) / step)) < 1e-9


def test_fehlschaetzung_uses_the_fixed_means_and_is_square():
    m = ev.fehlschaetzung(C.DEFAULT_B, C.DEFAULT_SZENARIO)
    assert m["ms"] == [5, 20, 80] and set(m["abgestimmt"]) == set(m["ms"])
    for x in m["ms"]:
        assert set(m["abgestimmt"][x]) == set(m["ms"])
        assert all(q >= 1.0 - 1e-12 for q in m["abgestimmt"][x].values())


def test_fehlschaetzung_means_are_distinct_for_every_b():
    for b in range(C.B_MIN, C.B_MAX + 1):
        ms = ev.fehlschaetzung(b, "geometrisch")["ms"]
        assert len(set(ms)) == 3, b

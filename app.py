"""Ski-Rental – mieten oder kaufen, ohne die Dauer zu kennen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück der Reihe „Online-Algorithmen“: eine Entscheidung fällt, bevor die Dauer bekannt ist, und wird am Optimum mit Vorwissen gemessen.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import ski_algorithm as A
import ski_constants as C
from ski_evaluation import (
    Settings,
    analyse,
    beispiellaeufe,
    curves,
    delta_text,
    fehlschaetzung,
    stufen_tabelle,
    verdict_fehlschaetzung,
    verdict_gegner,
    verdict_stufen,
    verdict_typisch,
    verdict_zufall,
)
from ski_layout import dunkles_design, kopf_css
from ski_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from ski_scenario import Szenario
from ski_visualization import build_costs, build_karlin, build_matrix, build_ratios, build_scenario, build_stufen, build_typisch

st.set_page_config(page_title="Ski-Rental – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _curves(settings):
    return curves(settings)


@st.cache_data(show_spinner=False)
def _fehlschaetzung(b, szenario):
    return fehlschaetzung(b, szenario)


@st.cache_data(show_spinner=False)
def _stufen():
    rows = stufen_tabelle()
    lines = {}
    for name, tiers in C.PREISLISTEN.items():
        ns = list(range(1, C.STUFEN_N_MAX + 1))
        lines[name.split(":")[0]] = (ns, [A.multi_rule_cost(n, tiers) / A.multi_opt(n, tiers) for n in ns])
    return rows, lines


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ski_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎿 Ski-Rental – mieten oder kaufen, ohne die Dauer zu kennen")
st.markdown(
    """
**Erstes Stück der Reihe „Online-Algorithmen“** (Entscheiden ohne Kenntnis der Zukunft). Ein Stapler kostet **1 je Tag Miete** oder **B einmalig** beim Kauf; wie lange der Auftrag dauert, weiß vorab niemand.
Gemessen wird jede Regel am **Optimum mit Vorwissen**: Das **Wettbewerbsverhältnis** ist der schlechteste Quotient aus gezahlten Kosten und Optimum über alle Dauern.

Weiter unten: die **Kernfrage** (was kostet die Regel im schlimmsten Fall), vier Experimente (**Zufall**, **typische Aufträge**, **falsch geschätzte Dauer**, **mehrere Stufen**), **🚧 Wo die Annahmen enden**, **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Ski-Rental", expanded=True):
    st.markdown(
        """
1. **Die Regel „kaufe am Tag t“:** bis Tag t − 1 wird gemietet, am Tag t gekauft. Endet der Auftrag früher, wurde nie gekauft und nur Miete gezahlt.
2. **Das Optimum mit Vorwissen** kennt die Dauer n und zahlt min(n, B): mieten, wenn der Auftrag kurz ist, sonst sofort kaufen.
3. **Break-even (t = B):** wer früher kauft, zahlt bei kurzen Aufträgen zu viel; wer später kauft, bei langen. Genau am Tag B ist der **schlechteste Quotient** am kleinsten: 2 − 1/B, also fast das Doppelte des Optimums, aber nie mehr.
4. **Zufall hilft:** wer den Kauftag zufällig nach einer festen Verteilung zieht, drückt den schlechtesten erwarteten Quotienten auf 1/(1 − (1 − 1/B)^B), für große B etwa 1,58.
5. **Garantie ist nicht Erwartung:** wie sich die Regeln bei *typischen* Dauern schlagen und was eine falsch geschätzte Dauer kostet, zeigen die Experimente.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Kaufpreis und Regel**")
    b = st.slider("Kaufpreis B (in Tagesmieten)", *bounds("b_slider"), key="b_slider", help="Der Kauf kostet so viel wie B Tage Miete (Miete: 1 je Tag).")
    tx = st.slider(
        "Kauftag t (in Vielfachen von B)", *bounds("tx_slider"), step=C.TX_STEP, key="tx_slider",
        help="Gekauft wird am Tag t = Vielfaches von B (gerundet, mindestens 1). 1,0 ist Break-even, 0 kauft sofort am ersten Tag.",
    )
    st.markdown("**Dauer der Aufträge**")
    szenario = st.selectbox("Verteilung der Dauer", C.SZENARIEN, key="szenario_select", help="Wie lange ein Auftrag dauert; die Regeln kennen sie nicht.")
    st.caption(C.SZENARIO_HILFE[szenario])
    mx = st.slider(
        "Mittlere Dauer m (in Vielfachen von B)", *bounds("mx_slider"), step=C.MX_STEP, key="mx_slider",
        help="Mittel der Dauer in Tagen (gerundet, mindestens 1); bei „fest“ ist es die Dauer selbst.",
    )
    seed = st.number_input("Zufalls-Seed der Beispielläufe", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Beispielläufe", width="stretch", on_click=randomize_seed)

sync_query_params({"b_slider": int(b), "tx_slider": float(tx), "szenario_select": szenario, "mx_slider": float(mx), "seed_input": int(seed)})

settings = Settings(int(b), float(tx), szenario, float(mx), int(seed))
a = _analysis(settings)
c = _curves(settings)
t, m = settings.t, settings.m

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Kaufpreis B = {b} Tagesmieten · Kauf am Tag t = {t} · Dauer „{szenario}“ mit Mittel m = {m} Tage")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; Farbe und Text regelt delta_text (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
d1, k1 = delta_text(a.worst, a.guarantee, "Break-even")
m1.metric("Schlechtester Quotient (Garantie)", f"{a.worst:.2f}", delta=d1, delta_color=k1,
          help="Größter Quotient aus Kosten und Optimum über alle Dauern, bei Dauer n = " + str(a.worst_at) + ".")
d2, k2 = delta_text(a.ratios["Deine Regel"], a.ratios["Break-even"], "Break-even")
m2.metric("Im Szenario (Erwartung)", f"{a.ratios['Deine Regel']:.2f}", delta=d2, delta_color=k2,
          help="Erwartete Kosten geteilt durch erwartetes Optimum im gewählten Szenario.")
m3.metric("Break-even im Szenario", f"{a.ratios['Break-even']:.2f}", delta="Referenz", delta_color="off")
d4, k4 = delta_text(a.ratios["Zufall"], a.ratios["Break-even"], "Break-even")
m4.metric("Zufallsregel im Szenario", f"{a.ratios['Zufall']:.2f}", delta=d4, delta_color=k4,
          help="Die Zufallsregel zahlt bei jeder Dauer dasselbe Vielfache des Optimums.")
st.plotly_chart(build_costs(c, t, b), width="stretch", key="main_chart")
st.caption(
    "Kosten der Regel über die Dauer n des Auftrags. Bis zum Kauftag folgt die Regel der Mietgeraden, danach springt sie auf (t − 1) + B; "
    "das Optimum knickt bei n = B ab. Der Abstand beider Kurven ist der Preis der Unwissenheit."
)

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was kostet die Regel im schlimmsten Fall?")
kind, text = verdict_gegner(a)
getattr(st, kind)(text)
st.plotly_chart(build_ratios(c, b), width="stretch", key="ratio_chart")
st.caption(
    "Quotient aus Kosten und Optimum über die Dauer n. Die gewählte Regel hat ihren Gipfel bei n = t, direkt nach dem Kauf. "
    "Die Zufallsregel (violett) liegt bei jeder Dauer auf derselben Höhe."
)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Was kauft der Zufall?")
kind, text = verdict_zufall(b)
getattr(st, kind)(text)
st.plotly_chart(build_karlin(b), width="stretch", key="karlin_chart")
st.caption(
    "Wahrscheinlichkeit, am Tag t zu kaufen (Verteilung von Karlin u. a.): späte Tage sind wahrscheinlicher, aber kein Tag ist sicher. "
    "Der Gegner kennt die Verteilung, nicht die Ziehung."
)

st.markdown("---")

st.subheader("🔬 Experiment 2: Wie teuer ist die Regel bei typischen Aufträgen?")
pmf = Szenario(b, szenario, m).pmf()
st.plotly_chart(build_scenario(pmf, b, szenario), width="stretch", key="scenario_chart")
lang = float(pmf[4 * b:].sum()) if len(pmf) > 4 * b else 0.0
st.caption(
    f"Verteilung der Dauer im Szenario „{szenario}“ (grün: Dauer unter B, orange: mindestens B, dann löst Break-even den Kauf aus)."
    + (f" Weitere {lang * 100:.1f} % der Aufträge dauern länger als 4B und sind nicht eingezeichnet." if lang > 0 else "")
)
ratios = a.ratios
st.plotly_chart(build_typisch(ratios, a.guarantee, a.random_guarantee), width="stretch", key="typisch_chart")
kind, text = verdict_typisch(a)
getattr(st, kind)(text)
with st.expander("Mittel der Quotienten statt Verhältnis der Erwartungen"):
    st.markdown(
        "Die Balken zeigen **erwartete Kosten geteilt durch erwartetes Optimum**. Man kann auch **jeden Auftrag einzeln** durch sein Optimum teilen und dann mitteln; "
        "das Ergebnis weicht ab, weil kurze Aufträge mit kleinem Optimum stark gewichtet werden. Beides ist richtig, beantwortet aber verschiedene Fragen: "
        "das erste die Kosten des Betriebs, das zweite das Erlebnis des typischen Auftrags."
    )
    rows = [{"Regel": k, "Verhältnis der Erwartungen": a.ratios[k], "Mittel der Quotienten": a.mean_ratios[k]} for k in a.mean_ratios]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={"Verhältnis der Erwartungen": st.column_config.NumberColumn(format="%.3f"), "Mittel der Quotienten": st.column_config.NumberColumn(format="%.3f")})
with st.expander("Beispielläufe: zwölf gezogene Aufträge"):
    st.caption("Kosten in Tagesmieten; die Ziehung folgt dem Zufalls-Seed der Seitenleiste.")
    st.dataframe(pd.DataFrame(beispiellaeufe(settings)), hide_index=True, width="stretch",
                 column_config={"Quotient deiner Regel": st.column_config.NumberColumn(format="%.2f")})

st.markdown("---")

st.subheader("🔬 Experiment 3: Und wenn die mittlere Dauer falsch geschätzt war?")
matrix = _fehlschaetzung(b, szenario)
st.caption(
    "Jede Zeile ist eine feste Regel: die beste für eine mittlere Dauer m (bei der gewählten Form der Verteilung), dann eingesetzt bei einer anderen mittleren Dauer "
    "(ein Viertel, das Einfache, das Vierfache von B). Zahlen: erwartete Kosten geteilt durch erwartetes Optimum."
)
st.plotly_chart(build_matrix(matrix), width="stretch", key="matrix_chart")
kind, text = verdict_fehlschaetzung(matrix, b)
getattr(st, kind)(text)
ties = [str(k) for k, v in matrix["tie"].items() if v]
if ties:
    st.caption(f"Bei m = {', '.join(ties)} sind alle festen Regeln gleich gut (geometrische Dauer ohne Gedächtnis mit Mittel B); dort steht der kleinste Kauftag.")

st.markdown("---")

st.subheader("🔬 Experiment 4: Mehrere Stufen (Miete, Leasing, Kauf)")
rows_stufen, lines_stufen = _stufen()
st.caption(
    "Mit mehr als zwei Optionen gibt es mehrere Wechsel: Tageskosten r sinken, die Anschaffung c steigt. Die Wechselregel steigt auf die nächste Stufe, "
    "sobald die bisherigen Kosten deren Anschaffungspreis erreicht haben. Gerechnet wird für Dauern bis 600 Tage."
)
df = pd.DataFrame(rows_stufen)
st.dataframe(df, hide_index=True, width="stretch", column_config={"schlechtester Quotient": st.column_config.NumberColumn(format="%.2f")})
st.plotly_chart(build_stufen(lines_stufen), width="stretch", key="stufen_chart")
kind, text = verdict_stufen(rows_stufen)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Dauer ist vorab ganz unbekannt** | Mit einer Vorhersage über die Dauer lässt sich mehr herausholen, sie darf aber nicht blind gelten; Experiment 3 zeigt, was ein blindes Vertrauen auf eine Schätzung kostet. | Vorhersagen |
| **Eine einzelne Anschaffung** | Wer mehrere Dinge zugleich vorhalten muss (Seiten im Zwischenspeicher, Fahrzeuge im Netz), braucht ein anderes Maß: aus der Kaufentscheidung wird eine Auswahl. | Paging |
| **Die Entscheidung ist endgültig, der Kauf wird nicht verkauft** | Mit Wiederverkauf ändert sich das Optimum und damit die Garantie; nicht modelliert. | – |
| **Der Gegner wählt die Dauer, kennt aber nicht die Ziehung** | Ein Gegner, der die Ziehung kennt, macht die Zufallsregel wirkungslos; nicht modelliert. | – |
| **Kosten sind Tage Miete** | Zinsen, Abschreibung, Restwert und echte Preise fehlen; die App rechnet in Tagesmieten. | – |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        """
**Annahmen.** Miete 1 je Tag, Kaufpreis B Tagesmieten, Nutzungsdauer n ≥ 1 ganzzahlig. Das Optimum kennt n. Alle Erwartungen sind exakt über die Verteilung gerechnet (die Beispielläufe sind Ziehungen). Die Verteilungen „gleichverteilt“, „geometrisch“ und „Ausreißer“ sind gewählte Modelle mit gemeinsamem Mittel m, keine Messungen echter Aufträge. „Ausreißer“ ist eine Mischung: 90 % mit kurzer, 10 % mit sehr langer Dauer (je geometrisch), so gewählt, dass das Mittel genau m bleibt.

**Grenzen.** Die Demo ist nur an erfundenen Szenarien geprüft. Im Experiment 4 sind die drei Preislisten eine Beobachtung und die Wechselregel ist nicht die beste Regel; die Aussage „mehr Stufen, schlechterer Quotient“ gilt nur für diese Listen und diese Regel. Der Kauftag der Regler wird auf ganze Tage gerundet.

**Bekannte Probleme und Unsicherheiten.** Bei geometrischer Dauer mit Mittel B zahlen alle festen Regeln im Mittel dasselbe (die Dauer ist ohne Gedächtnis); dort zeigt die Demo einen Gleichstand und den kleinsten Kauftag. Verhältnis der Erwartungen und Mittel der Quotienten können stark abweichen (Expander in Experiment 2).
        """
    )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind der Kaufpreis $B$ und eine Regel; die Dauer $n$ ist vorab unbekannt. Gesucht ist, was die Regel im schlechtesten Fall und im Erwartungswert kostet.

| Symbol | Bedeutung |
|---|---|
| $B$ | Kaufpreis in Tagesmieten (Miete: 1 je Tag) |
| $n$ | Dauer der Nutzung in Tagen, $n \ge 1$ |
| $t$ | Kauftag der Regel: bis Tag $t-1$ mieten, am Tag $t$ kaufen |
| $\mathrm{OPT}(n)$ | Kosten mit Vorwissen über $n$ |
| $\mathrm{ALG}_t(n)$ | Kosten der Regel „kaufe am Tag $t$“ |
| $p_t$ | Wahrscheinlichkeit, am Tag $t$ zu kaufen (Zufallsregel) |

**Kosten.** $\mathrm{OPT}(n) = \min(n, B)$. $\mathrm{ALG}_t(n) = n$ für $n < t$, sonst $(t-1) + B$.

**Wettbewerbsverhältnis (deterministisch).** $\max_n \mathrm{ALG}_t(n)/\mathrm{OPT}(n)$. Der Höchstwert liegt bei $n = t$: für $t \le B$ gleich $(t-1+B)/t$, für $t > B$ gleich $(t-1+B)/B$. Das Minimum über $t$ liegt bei $t = B$ mit $2 - 1/B$.

**Zufallsregel.** $p_t = \dfrac{(1-1/B)^{B-t}}{B\,\bigl(1-(1-1/B)^B\bigr)}$ für $t = 1, \dots, B$. Dann gilt für jedes $n$: $\mathbb{E}[\mathrm{ALG}(n)] = \dfrac{\mathrm{OPT}(n)}{1-(1-1/B)^B}$; der Quotient ist also für jede Dauer gleich und strebt für $B \to \infty$ gegen $e/(e-1) \approx 1{,}58$.

**Erwartung im Szenario.** $\mathbb{E}[\mathrm{ALG}]/\mathbb{E}[\mathrm{OPT}]$ mit $\mathbb{E}[\mathrm{ALG}_t] = \sum_{n<t} nP(n) + (t-1+B)\,P(n \ge t)$. Davon verschieden ist das Mittel der Quotienten $\mathbb{E}[\mathrm{ALG}/\mathrm{OPT}]$.

**Stufen.** Optionen $(c_i, r_i)$ mit Anschaffung $c_i$ und Tageskosten $r_i$; $\mathrm{OPT}(n) = \min_i (c_i + r_i n)$. Die Wechselregel steigt auf Stufe $i+1$, sobald die bisherigen Kosten $c_{i+1}$ erreichen, und zahlt dann $c_{i+1}$ zusätzlich.

**Literatur (nicht nachgebaut, Volltext nicht eingesehen).** A. R. Karlin, M. S. Manasse, L. A. McGeoch, S. Owicki: *Competitive randomized algorithms for non-uniform problems*, Algorithmica 11 (1994) 542–571 (Konferenzfassung SODA 1990): Faktor $e/(e-1)$ für die Zufallsregel und dass kein Zufallsverfahren besser ist. Der Faktor 2 für feste Regeln wird hier durch vollständiges Durchrechnen aller Dauern belegt.
        """
    )

st.markdown("---")
st.caption(
    "Verwandte Demos: [Online-Matching](https://sebastianhanisch-online-matching-demo.streamlit.app/) (Zuordnen ohne Kenntnis der Zukunft, Wettbewerbsverhältnis für Zuordnungen), "
    "[No-Regret-Lernen](https://sebastianhanisch-noregret-demo.streamlit.app/) (Lernen aus Erfahrung mit dem Regret als Maß), rollierende Planung (Neuplanung mit Prognose, ohne Gegner) "
    "und Buchungsannahme mit Gewichtslimit (Annahme mit bekannter Nachfrageverteilung)."
)
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)

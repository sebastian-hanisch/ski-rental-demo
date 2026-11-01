"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ski_algorithm as A
import ski_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_costs(c: dict, t: int, b: int):
    """Kosten über die Dauer n: immer mieten, Optimum mit Vorwissen, die gewählte Regel (und Break-even, falls anders)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c["n"], y=c["rent"], mode="lines", name="Immer mieten", line=dict(color=C.COLOR_RENT, width=2, dash="dot"),
                             hovertemplate="n = %{x}: %{y}<extra>Immer mieten</extra>"))
    fig.add_trace(go.Scatter(x=c["n"], y=c["opt"], mode="lines", name="Optimum mit Vorwissen", line=dict(color=C.COLOR_OPT, width=3),
                             hovertemplate="n = %{x}: %{y}<extra>Optimum</extra>"))
    if t != b:
        fig.add_trace(go.Scatter(x=c["n"], y=c["break_even"], mode="lines", name=f"Break-even (Tag {b})", line=dict(color=C.COLOR_BREAK, width=2, dash="dash"),
                                 hovertemplate="n = %{x}: %{y}<extra>Break-even</extra>"))
    fig.add_trace(go.Scatter(x=c["n"], y=c["alg"], mode="lines", name=f"Deine Regel (Kauf am Tag {t})", line=dict(color=C.COLOR_ALG, width=3),
                             hovertemplate="n = %{x}: %{y}<extra>Deine Regel</extra>"))
    ymax = max(max(c["alg"]), b) * 1.1
    fig.update_xaxes(title_text="Dauer der Nutzung n (Tage)")
    fig.update_yaxes(title_text="Gezahlte Kosten (in Tagesmieten)", range=[0, ymax])
    return _base(fig)


def build_ratios(c: dict, b: int):
    """Quotient Kosten/Optimum über n für die gewählte Regel, Break-even und die Zufallsregel, mit den Garantien als Linien."""
    ns = c["n"]
    opt = c["opt"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[a / o for a, o in zip(c["alg"], opt)], mode="lines", name="Deine Regel", line=dict(color=C.COLOR_ALG, width=3),
                             hovertemplate="n = %{x}: %{y:.2f}<extra>Deine Regel</extra>"))
    fig.add_trace(go.Scatter(x=ns, y=[a / o for a, o in zip(c["break_even"], opt)], mode="lines", name="Break-even", line=dict(color=C.COLOR_BREAK, width=2, dash="dash"),
                             hovertemplate="n = %{x}: %{y:.2f}<extra>Break-even</extra>"))
    fig.add_trace(go.Scatter(x=ns, y=[a / o for a, o in zip(c["random"], opt)], mode="lines", name="Zufallsregel (Erwartung)", line=dict(color=C.COLOR_RANDOM, width=3),
                             hovertemplate="n = %{x}: %{y:.3f}<extra>Zufall</extra>"))
    top = max(2.2, max(a / o for a, o in zip(c["alg"], opt)) * 1.08)
    fig.update_xaxes(title_text="Dauer der Nutzung n (Tage)")
    fig.update_yaxes(title_text="Kosten geteilt durch Optimum", range=[0.9, top])
    return _base(fig)


def build_scenario(pmf, b: int, kind: str):
    """Verteilung der Nutzungsdauer (bis zum Vierfachen von B); die Masse dahinter steht in der Beschriftung der App."""
    n_show = min(len(pmf), 4 * b)
    xs = list(range(1, n_show + 1))
    colors = [C.COLOR_ALG if n < b else C.COLOR_BREAK for n in xs]
    fig = go.Figure(go.Bar(x=xs, y=[float(p) for p in pmf[:n_show]], marker_color=colors, hovertemplate="n = %{x}: %{y:.3f}<extra></extra>"))
    fig.update_xaxes(title_text="Dauer der Nutzung n (Tage)")
    fig.update_yaxes(title_text="Wahrscheinlichkeit")
    return _base(fig, height=260)


def build_karlin(b: int):
    p = A.karlin(b)
    xs = list(range(1, b + 1))
    fig = go.Figure(go.Bar(x=xs, y=[float(v) for v in p], marker_color=C.COLOR_RANDOM, hovertemplate="Tag %{x}: %{y:.3f}<extra></extra>"))
    fig.update_xaxes(title_text="Kauftag t")
    fig.update_yaxes(title_text="Wahrscheinlichkeit")
    return _base(fig, height=260)


def build_typisch(ratios: dict, guarantee: float, random_guarantee: float):
    """Verhältnis der Erwartungen je Regel im Szenario; die beiden Garantien als Linien."""
    names = list(ratios)
    colors = [C.COLOR_ALG, C.COLOR_BREAK, C.COLOR_NEVER, C.COLOR_NEVER, C.COLOR_RANDOM]
    fig = go.Figure(go.Bar(x=names, y=[ratios[k] for k in names], marker_color=colors, text=[f"{ratios[k]:.2f}" for k in names], textposition="outside",
                           hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.add_hline(y=guarantee, line=dict(color=C.COLOR_BREAK, dash="dash"), annotation_text=f"Garantie Break-even {guarantee:.2f}", annotation_position="top left")
    fig.add_hline(y=random_guarantee, line=dict(color=C.COLOR_RANDOM, dash="dot"), annotation_text=f"Garantie Zufall {random_guarantee:.2f}", annotation_position="bottom left")
    fig.update_yaxes(title_text="Erwartete Kosten geteilt durch erwartetes Optimum", range=[0, max(max(ratios.values()), guarantee) * 1.25])
    return _base(fig)


def build_matrix(m: dict):
    """Zeilen: Regel (auf eine mittlere Dauer abgestimmt, Break-even, Zufall); Spalten: mittlere Dauer, bei der sie läuft."""
    ms = m["ms"]
    rows, labels = [], []
    for x in ms:
        t = m["t"][x]
        labels.append(f"abgestimmt auf m = {x} ({'nie kaufen' if t is None else 'Tag ' + str(t)})")
        rows.append([m["abgestimmt"][x][y] for y in ms])
    labels += ["Break-even", "Zufallsregel"]
    rows.append([m["Break-even"][y] for y in ms])
    rows.append([m["Zufall"][y] for y in ms])
    fig = go.Figure(go.Heatmap(
        z=rows, x=[f"läuft bei m = {y}" for y in ms], y=labels, text=[[f"{v:.2f}" for v in r] for r in rows], texttemplate="%{text}",
        colorscale="YlOrRd", zmin=1.0, zmax=max(4.0, max(max(r) for r in rows)), showscale=False, hovertemplate="%{y}, %{x}: %{z:.3f}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=330)


def build_stufen(curves: dict):
    """Quotient der Wechselregel über n für jede Preisliste; curves: {Name: (ns, Quotienten)}."""
    fig = go.Figure()
    palette = [C.COLOR_OPT, C.COLOR_BREAK, C.COLOR_RANDOM]
    for color, (name, (ns, qs)) in zip(palette, curves.items()):
        fig.add_trace(go.Scatter(x=ns, y=qs, mode="lines", name=name, line=dict(color=color, width=2.5), hovertemplate="n = %{x}: %{y:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Dauer der Nutzung n (Tage)")
    fig.update_yaxes(title_text="Kosten geteilt durch Optimum")
    return _base(fig)

"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

B_MIN, B_MAX, DEFAULT_B = 4, 100, 20          # Kaufpreis in Tagesmieten (Miete: 1 je Tag)
TX_MIN, TX_MAX, DEFAULT_TX = 0.0, 3.0, 1.0    # Kauftag t in Vielfachen von B; t = max(1, round(TX * B)); 1,0 = Break-even
TX_STEP = 0.05
MX_MIN, MX_MAX, DEFAULT_MX = 0.25, 8.0, 1.0   # mittlere Nutzungsdauer m in Vielfachen von B; m = max(1, round(MX * B))
MX_STEP = 0.25
MX_FALSCH = (0.25, 1.0, 4.0)                  # mittlere Dauern des Fehlschätzungs-Experiments (Vielfache von B)
SEED_MAX, DEFAULT_SEED = 999999, 7
N_DRAWS = 12                                  # Länge der Beispielläufe

SZENARIEN = ("fest", "gleichverteilt", "geometrisch", "Ausreißer")
DEFAULT_SZENARIO = "gleichverteilt"
SZENARIO_HILFE = {
    "fest": "Der Auftrag dauert genau m Tage (der Fall des Gegners, der die Dauer wählt).",
    "gleichverteilt": "Jede Dauer von 1 bis 2m − 1 Tage ist gleich wahrscheinlich; Mittel m.",
    "geometrisch": "Jeden Tag endet der Auftrag mit der Wahrscheinlichkeit 1/m; Mittel m, ohne Gedächtnis.",
    "Ausreißer": "Meist kurz, selten sehr lang: 90 % mit kurzer, 10 % mit sehr langer Dauer (je geometrisch); Mittel m.",
}
ANTEIL_LANG = 0.1                              # Ausreißer: Anteil der langen Aufträge
FAKTOR_LANG = 8.2                              # Ausreißer: (mittlere lange Dauer − 1) = FAKTOR_LANG · (m − 1); Mittel insgesamt genau m
TAIL_LAENGEN = 30.0                            # Träger der Verteilung: bis zum 30-Fachen des größten Mittels (Restmasse < 1e-12)

# Preislisten der Stufen: (Anschaffung c, Tageskosten r) je Stufe; Stufe 0 ist die Miete (0, 1)
PREISLISTEN = {
    "2 Stufen: Miete, Kauf": [(0, 1), (20, 0)],
    "3 Stufen: Miete, Leasing, Kauf": [(0, 1), (10, 0.3), (40, 0)],
    "4 Stufen: Miete, zwei Leasingstufen, Kauf": [(0, 1), (6, 0.5), (20, 0.2), (60, 0)],
}
STUFEN_N_MAX = 600                             # größte Dauer der Stufen-Rechnung

COLOR_ALG = "#2F6B65"
COLOR_OPT = "#4c78a8"
COLOR_RENT = "rgba(150,150,150,0.8)"
COLOR_BREAK = "#d97706"
COLOR_RANDOM = "#7c3aed"
COLOR_NEVER = "rgba(150,150,150,0.55)"

PRESETS = {
    "Stapler (B = 20, mittlere Aufträge)": {"b": DEFAULT_B, "tx": 1.0, "szenario": "gleichverteilt", "mx": 1.0, "seed": DEFAULT_SEED},
    "Mini-Instanz von Hand (B = 4)": {"b": 4, "tx": 1.0, "szenario": "fest", "mx": 1.0, "seed": DEFAULT_SEED},
    "Kurze Aufträge": {"b": DEFAULT_B, "tx": 1.0, "szenario": "geometrisch", "mx": 0.25, "seed": DEFAULT_SEED},
    "Lange Aufträge": {"b": DEFAULT_B, "tx": 1.0, "szenario": "gleichverteilt", "mx": 4.0, "seed": DEFAULT_SEED},
    "Sofort kaufen, Ausreißer": {"b": DEFAULT_B, "tx": 0.0, "szenario": "Ausreißer", "mx": 1.0, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Stapler (B = 20, mittlere Aufträge)": "Ein Stapler kostet 20 Tagesmieten; die Dauer ist gleichverteilt mit Mittel 20 Tage; gekauft wird am Break-even-Tag.",
    "Mini-Instanz von Hand (B = 4)": "Der Fall zum Nachrechnen: Kaufpreis 4, der Auftrag endet nach genau 4 Tagen; die Regel zahlt 7 statt 4.",
    "Kurze Aufträge": "Aufträge dauern im Mittel ein Viertel des Kaufpreises (geometrisch): Kaufen lohnt sich fast nie, Break-even ist fast optimal.",
    "Lange Aufträge": "Die mittlere Dauer ist das Vierfache des Kaufpreises: 88 % der Aufträge dauern mindestens B Tage, Break-even liegt nahe an seiner Garantie.",
    "Sofort kaufen, Ausreißer": "Die Regel kauft am ersten Tag; die Aufträge sind meist kurz und selten sehr lang (Mittel B): sie zahlt den Kauf, den die meisten Aufträge nie gebraucht hätten.",
}

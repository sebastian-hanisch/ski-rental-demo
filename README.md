# Ski-Rental – mieten oder kaufen, ohne die Dauer zu kennen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-ski-rental-demo.streamlit.app/)**

Erstes Stück der Reihe **Online-Algorithmen** („Entscheiden ohne Kenntnis der Zukunft“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Konzept, die **Wettbewerbsanalyse**, an einem wachsenden Beispiel: von einer Instanz zum Nachrechnen (Kaufpreis 4) über einen Stapler mit Kaufpreis 20 bis zu mehreren Stufen (Miete, Leasing, Kauf).
Wurzel der Reihe: ohne sie fehlt den Folgestücken (Paging, Online-Packen, Sekretärproblem, k-Server, Vorhersagen, Online-Allokation) die Sprache aus Wettbewerbsverhältnis, Gegner und Randomisierung.

**Verwandte bestehende Demos:** `online-matching-demo` (Zuordnen ohne Zukunft, das Wettbewerbsverhältnis für Zuordnungen), `noregret-demo` (Lernen aus Erfahrung, Maß ist der Regret), `rolling-horizon-demo` (Neuplanung mit Prognose, ohne Gegner), `uld-buchungsannahme-demo` (Annahme mit bekannter Nachfrageverteilung). Keine davon enthält die Kaufentscheidung mit unbekannter Dauer.

## Warum dieses Problem

Ein Stapler kostet **1 je Tag** Miete oder **B** einmalig beim Kauf. Wie lange der Auftrag dauert, weiß vorab niemand. Wer früh kauft, zahlt bei kurzen Aufträgen zu viel; wer spät kauft, bei langen. Die Kernfrage: **Was kostet eine Regel im schlimmsten Fall, was kostet sie im Betrieb, und was kostet es, wenn man die Dauer falsch einschätzt?**

## Modell

Miete 1 je Tag, Kaufpreis B (in Tagesmieten), Nutzungsdauer n ≥ 1 Tage. Das Optimum mit Vorwissen kostet OPT(n) = min(n, B). Die Regel „kaufe am Tag t“ zahlt n, wenn der Auftrag vor Tag t endet, sonst (t − 1) + B. Das **Wettbewerbsverhältnis** der Regel ist der größte Quotient aus Kosten und Optimum über alle Dauern.
**Zufallsregel:** Kauftag t mit der Wahrscheinlichkeit p_t ∝ (1 − 1/B)^(B−t), t = 1 … B; sie zahlt bei **jeder** Dauer im Mittel das 1/(1 − (1 − 1/B)^B)-Fache des Optimums (ein „Gleichmacher“). Alle Erwartungen sind **exakt** über die Verteilung gerechnet (keine Stichprobe); die Beispielläufe sind Ziehungen mit festem Seed. Formeln im 📐-Expander der App.

Vier Verteilungen der Dauer mit gleichem Mittel m (ganzzahlig): **fest** (genau m Tage), **gleichverteilt** (1 bis 2m − 1), **geometrisch** (ohne Gedächtnis), **Ausreißer** (90 % mit kurzer, 10 % mit sehr langer Dauer, je geometrisch, Mittel genau m; Parameter in `ski_constants.py`).

## Methodik

| Abschnitt der App | Was gerechnet wird |
|---|---|
| Ergebnis, Kernfrage | schlechtester Quotient der gewählten Regel über alle Dauern, Quotientenkurve über n |
| Experiment 1 | die Zufallsregel: Verteilung der Kauftage, Quotient bei jeder Dauer |
| Experiment 2 | erwartete Kosten geteilt durch erwartetes Optimum je Regel in der gewählten Verteilung; beste feste Regel; Beispielläufe |
| Experiment 3 | auf eine mittlere Dauer abgestimmte beste feste Regel, eingesetzt bei einer anderen mittleren Dauer (ein Viertel, das Einfache, das Vierfache von B) |
| Experiment 4 | Wechselregel bei mehreren Stufen (Anschaffung c, Tageskosten r): schlechtester Quotient für drei Preislisten |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen in `tests/test_claims.py` nachgerechnet; Kaufpreis B = 20 und die Presets der App, soweit nicht anders genannt. „Quotient“ steht für erwartete Kosten geteilt durch erwartetes Optimum.

| Frage | Befund |
|---|---|
| Was kostet Break-even (Kauf am Tag B) im schlimmsten Fall? | 2 − 1/B: 1,75 bei B = 4, 1,95 bei B = 20, 1,99 bei B = 100; der Kauf am Tag B ist unter allen Kauftagen die **einzige** beste Regel. Sofort kaufen kostet im schlimmsten Fall das B-Fache (20 bei B = 20). |
| Was erreicht die Zufallsregel? | 1,463 (B = 4), 1,535 (B = 10), 1,559 (B = 20), 1,580 (B = 200), Grenzwert e/(e − 1) = 1,582; bei **jeder** Dauer derselbe Quotient. |
| Mini-Instanz von Hand (B = 4, Dauer 4) | Die Regel mietet drei Tage (3) und kauft am Tag 4 (4): 7 statt 4, Quotient 1,75. |
| Kurze Aufträge (Mittel 5, geometrisch; 1,4 % der Aufträge dauern mindestens B Tage) | Break-even 1,055, nie kaufen 1,012, sofort kaufen 4,047, Zufall 1,559. |
| Mittlere Aufträge (Mittel 20, gleichverteilt; 51 % dauern mindestens B) | Break-even 1,644, sofort kaufen und nie kaufen je 1,322 (Mittel gleich B), Zufall 1,559. |
| Lange Aufträge (Mittel 80, gleichverteilt; 88 % dauern mindestens B) | **Break-even 1,890, nahe an seiner Garantie 1,95**, ganz ohne Gegner; sofort kaufen 1,064, nie kaufen 4,254, Zufall 1,559. |
| Verhältnis der Erwartungen gegen Mittel der Quotienten | Sofort kaufen bei kurzen Aufträgen: 4,047 gegen 8,049. Beide Maße sind in der App sichtbar. |
| Sofort kaufen bei seltenen langen Aufträgen (Mittel 20, Ausreißer) | Die Regel zahlt das 3,245-Fache, Break-even 1,306, die beste feste Regel (Kauf am Tag 17) 1,294. |
| Beste feste Regel bei geometrischer Dauer | immer eine Ecke: sofort kaufen oder nie kaufen. Bei Mittel gleich B (ohne Gedächtnis) sind **alle** festen Regeln im Mittel gleich gut. |
| Falsch geschätzte mittlere Dauer (auf Mittel 5 abgestimmt, läuft bei Mittel 80) | gleichverteilt 4,254, geometrisch 4,496, fest 4,000; Break-even bleibt dabei bei höchstens 1,890, 1,841 und 1,95. Bei fester und gleichverteilter Dauer ist „nie kaufen“ nur eine von vielen gleich guten abgestimmten Regeln, die App wählt es (Konvention): Der Kauf am Tag 6 (fest) bzw. 10 (gleichverteilt) kostet bei Mittel 80 nur 1,250 bzw. 1,470 statt 4,000 bzw. 4,254. |
| Dasselbe bei der Form „Ausreißer“ | höchstens 1,559: die Mischung enthält kurze und lange Aufträge, keine abgestimmte Regel läuft in eine fremde Welt; Break-even höchstens 1,567. |
| Mehrere Stufen (Wechselregel) | schlechtester Quotient 2,00 (zwei Stufen, Dauer 21), 2,40 (drei, Dauer 78), 2,69 (vier, Dauer 123). Beobachtung an drei Preislisten, keine Aussage über die beste Regel. |

## Ehrliche Grenzen

- Die Demo ist **nur an erfundenen Szenarien** geprüft; die vier Verteilungen sind gewählte Modelle, keine Messung echter Aufträge.
- Die Aussage „Garantie als Versicherung“ hängt von der Form ab: bei fest, gleichverteilt und geometrisch kostet eine falsch geschätzte mittlere Dauer das Vierfache, bei „Ausreißer“ höchstens etwa 20 % mehr als die passende Regel (siehe Befunde).
- Die Stufen-Werte gelten für die gewählte Wechselregel und drei Preislisten (Dauern bis 600 Tage), nicht für die beste Regel; die Aussage „mehr Stufen, schlechterer Quotient“ ist eine Beobachtung, kein Satz.
- Der Gegner kennt die Regel, nicht die Ziehung. Ein adaptiver Gegner, Wiederverkauf, Zinsen und echte Preise sind nicht modelliert.
- Der Kauftag der Regler wird auf ganze Tage gerundet (Vielfache von B, Schritt 0,05).

## Befunde und Korrekturen gegenüber dem Plan

- **Erwartung widerlegt:** Der Plan erwartete, dass der mittlere Quotient bei zufälliger Nutzungsdauer „weit unter der Garantie“ liegt. Das gilt vor allem für **kurze** Aufträge (Break-even 1,055); bei mittleren gleichverteilten Aufträgen sind es 1,644. Bei langen Aufträgen liegt Break-even bei 1,890 gegen 1,95, weil die Masse hinter dem Kaufpunkt liegt und dort jede Dauer 2B − 1 gegen B kostet.
- **Experiment 3 umgebaut:** Geplant war ein Vergleich über die Form der Verteilung bei gleichem Mittel. Die natürliche Fehleinschätzung im Betrieb ist aber die **mittlere Dauer** (zu kurz oder zu lang erwartet); deshalb vergleicht Experiment 3 jetzt mittlere Dauern (ein Viertel, das Einfache, das Vierfache von B).
- **Gleichstand sichtbar gemacht:** Bei geometrischer Dauer mit Mittel gleich B sind alle festen Regeln gleich gut; ein Kauftag „als Sieger“ wäre irreführend. Die App nennt den Gleichstand ausdrücklich (`rules_tie`).
- **„Nie kaufen“ statt „Tag 99“:** Bei Mittel 5 fällt der beste Kauftag rechnerisch weit hinter den Träger der Verteilung; die Auswahl meldet dann „nie kaufen“ (`best_fixed_t`, Toleranz 1e-6).

## Verifikation

- **Umfang:** 122 Tests, rund 80 Sekunden lokal.
- **Kern:** Kosten gegen Handrechnung (Mini-Instanz), gegen eine tagweise Zählung und gegen Brute-Force-Aufzählungen; Erwartungen gegen eine Schleife über die Verteilung.
- **Orakel** (`tests/test_oracle_ski_rental.py`): das Spiel „Regel gegen Gegner“ als lineares Programm (`scipy.linprog`) liefert denselben Wert wie die Formel und die Karlin-Verteilung als optimale Strategie; exakte Brüche (`fractions`); Wechselregel gegen eine rekursive Fassung.
- **Eigenschaften** (`tests/test_eigenschaften_ski_rental.py`): Quotienten ≥ 1; erwarteter Quotient höchstens so groß wie der schlechteste der Regel; die Zufallsregel hat bei **jeder** Verteilung denselben Quotienten; Skalierung der Preise; gleicher Seed, gleiche Ziehung.
- **Literatur** (`tests/test_literatur_ski_rental.py`): e/(e − 1) und die veröffentlichte Näherung der Kaufwahrscheinlichkeiten für große B. **Offen:** die Primärquelle (Karlin, Manasse, McGeoch, Owicki, Algorithmica 1994) wurde nicht im Volltext eingesehen; die Werte stammen aus Suchauszügen und Vorlesungsnotizen.
- **Verdikte** (`tests/test_verdicts.py`): jede Zahl und jede Verzweigung der Texte an gesetzten Werten. **Claims** (`tests/test_claims.py`): jede Zahl dieser README.
- **Presets, Layout, Oberfläche:** vollständig, Werte in den Reglergrenzen; Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben, jede Regleränderung hebt die Markierung auf; AppTest-Rauchtest (jeder Button, jeder Regler an beiden Grenzen); Footer; Laufzeit-Importe.
- **Browser:** im Desktop-Browser durchgeklickt (alle fünf Presets, Seitenleiste, Expander, Heatmap). Nicht mit echtem Touch-Gerät getestet. Die Konsole meldet gelegentlich `<text> attribute y: Expected length, "-Infinity"`: ein bekanntes, zeitabhängiges Verhalten von Plotly, kein Fehler in dieser Demo.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, vier Experimente, Grenzen, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur für das Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `ski_algorithm.py` | Kern: Kosten, Zufallsregel, exakte Erwartungen, beste feste Regel, Stufen |
| `ski_constants.py` | Regler-Grenzen, Verteilungen, Preislisten, Farben, Presets |
| `ski_evaluation.py` | Kennzahlen, Verdikte, Fehlschätzungs-Matrix, Beispielläufe, Stufentabelle |
| `ski_layout.py` | Fester Kopf (Stylesheet) |
| `ski_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `ski_scenario.py` | Verteilungen der Nutzungsdauer |
| `ski_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Kern, Randfälle, Orakel, Eigenschaften, Literatur, Verdikte, Claims, Presets, Layout, Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Vorhersagen** über die Dauer und deren Fehlermaß (Konsistenz, Robustheit): eigenes Stück der Reihe.
- **Adaptive Gegner**, Wiederverkauf, Zinsen und Restwert, Preise aus echten Daten.
- **Beste Regel für mehrere Stufen** (Zufallsregeln für Multi-Slope-Ski-Rental): nur die einfache Wechselregel.
- **PDF-Export**: die Demo hat keine Ergebnisse, die man weitergibt; die Adresszeile (Permalink) reicht zum Teilen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Online-Algorithmen: Entscheiden ohne Zukunft](https://sebastianhanisch.net/konzepte-online-algorithmen.html).

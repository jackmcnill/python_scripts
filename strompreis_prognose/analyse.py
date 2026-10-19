"""Strompreis-Muster aus den Home-Assistant-Statistiken (Tibber) auswerten.

Aufruf:  python3 analyse.py
Liest die CSVs aus ./daten und gibt Monatsmittel, Wochenmittel und das
Tagesprofil (Werktag/Wochenende) der letzten 28 Tage aus.
"""
import csv
import datetime as dt
import statistics as st
from collections import defaultdict
from pathlib import Path

DATEN = Path(__file__).parent / "daten"


def lies(name, spalte="mean"):
    with open(DATEN / name, newline="") as f:
        for r in csv.DictReader(f):
            if r[spalte]:
                yield dt.datetime.fromisoformat(r["start_local"]), float(r[spalte])


def monatsmittel():
    m = defaultdict(list)
    for t, v in lies("tage_2023_08_bis_2026_05.csv"):
        m[(t.year, t.month)].append(v)
    for k, v in sorted(m.items()):
        print(k, round(st.mean(v), 3))


def wochenmittel(name):
    w = defaultdict(list)
    for t, v in lies(name):
        w[t.isocalendar()[:2]].append(v)
    for k, v in sorted(w.items()):
        print(k, round(st.mean(v), 3), round(min(v), 3), round(max(v), 3))


def tagesprofil(name, tage=28):
    rows = list(lies(name))[-24 * tage:]
    h = defaultdict(list)
    for t, v in rows:
        h[(t.weekday() >= 5, t.hour)].append(v)
    for we in (False, True):
        print("Wochenende" if we else "Werktag",
              [round(st.mean(h[(we, i)]), 3) for i in range(24)])
    alle = sorted(v for _, v in rows)
    n = len(alle)
    print("p25", round(alle[n // 4], 3), "Mittel", round(st.mean(alle), 3),
          "p75", round(alle[3 * n // 4], 3))


if __name__ == "__main__":
    print("== Monatsmittel (Tageswerte 2023-08 bis 2026-05) ==")
    monatsmittel()
    print("\n== Wochenmittel 2026 (Stundenwerte) ==")
    wochenmittel("stunden_2026_07_bis_10.csv")
    print("\n== Tagesprofil letzte 28 Tage ==")
    tagesprofil("stunden_2026_07_bis_10.csv")

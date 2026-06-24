"""Unittests für die Berechnungen in formulas.py."""

import pandas as pd
import pytest

from components.formulas import differenz_erzeugt_verbraucht, umrechnung_in_kwh


def baue_test_df(zeiten, pv_werte, netz_werte):
    """Kleiner Helfer, der einen DataFrame im erwarteten Format baut."""
    return pd.DataFrame(
        {
            "collected_at": zeiten,
            "pv_erzeugung_kw": pv_werte,
            "netz_wert_kw": netz_werte,
        }
    )


def test_konstante_leistung_eine_stunde():
    # 1 kW konstant über genau 1 Stunde muss 1 kWh ergeben
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[2.0, 2.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    # Die letzte Zeile ist NaN (kein nächster Punkt), .sum() ignoriert das
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(1.0)
    assert ergebnis["kwh_verbraucht"].sum() == pytest.approx(2.0)


def test_steigende_leistung_trapezregel():
    # 0 kW -> 2 kW über 1 Stunde: Mittelwert 1 kW -> 1 kWh
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[0.0, 2.0],
        netz_werte=[0.0, 0.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(1.0)


def test_delta_h_wird_richtig_berechnet():
    # Zwei Messpunkte 30 Minuten auseinander -> delta_h = 0.5
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T08:30:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[1.0, 1.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["delta_h"].iloc[0] == pytest.approx(0.5)


def test_differenz_erzeugt_verbraucht_ergibt_defizit():
    # Erzeugung 1 kWh, Verbrauch 2 kWh -> Bilanz -1 kWh (Defizit)
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[2.0, 2.0],
    )
    bilanz = differenz_erzeugt_verbraucht(df)
    # Nur ein Tag in den Daten -> ein Eintrag in der Series
    assert len(bilanz) == 1
    assert bilanz.iloc[0] == pytest.approx(-1.0)
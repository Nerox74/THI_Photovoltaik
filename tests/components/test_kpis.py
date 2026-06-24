"""Unittests für kpis.py: Hilfsfunktion _summe_kwh."""

import pandas as pd

from components.kpis import _summe_kwh


def baue_test_df():
    """Erstellt einen DataFrame mit zwei Messpunkten von heute."""
    jetzt = pd.Timestamp.now(tz="UTC")
    return pd.DataFrame(
        {
            "collected_at": [
                jetzt - pd.Timedelta(hours=1),
                jetzt - pd.Timedelta(hours=2),
            ],
            "kwh_erzeugt": [5.0, 3.0],
            "kwh_verbraucht": [2.0, 1.0],
        }
    )


def test_summe_kwh_erzeugt_addiert_richtig():
    df = baue_test_df()
    ergebnis = _summe_kwh(df, "kwh_erzeugt", "Tag")
    # 5.0 + 3.0 = 8.0
    assert ergebnis == 8.0


def test_summe_kwh_verbraucht_addiert_richtig():
    df = baue_test_df()
    ergebnis = _summe_kwh(df, "kwh_verbraucht", "Tag")
    # 2.0 + 1.0 = 3.0
    assert ergebnis == 3.0


def test_summe_kwh_gibt_null_zurueck_wenn_keine_werte_im_zeitraum():
    # Werte liegen 400 Tage in der Vergangenheit → "Tag" findet nichts
    vor_einem_jahr = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=400)
    df = pd.DataFrame(
        {
            "collected_at": [vor_einem_jahr],
            "kwh_erzeugt": [100.0],
            "kwh_verbraucht": [50.0],
        }
    )
    ergebnis = _summe_kwh(df, "kwh_erzeugt", "Tag")
    assert ergebnis == 0.0


def test_summe_kwh_monat_schliesst_tageswerte_ein():
    # Werte von heute müssen auch im Monatszeitraum gezählt werden
    df = baue_test_df()
    ergebnis = _summe_kwh(df, "kwh_erzeugt", "Monat")
    assert ergebnis == 8.0
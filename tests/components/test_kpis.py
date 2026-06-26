"""Unittests für kpis.py: Hilfsfunktionen _summe_kwh und _kpi_card."""

import pandas as pd

from components.kpis import _auslastung_bar, _kpi_card, _mini_stat, _summe_kwh

# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────


def baue_test_df(stunden_versatz: list[int] | None = None) -> pd.DataFrame:
    """Erstellt einen DataFrame mit Messpunkten relativ zu jetzt.

    Args:
        stunden_versatz: Liste von Stunden-Offsets (negativ = Vergangenheit).
                         Standard: [-1, -2] (eine und zwei Stunden in der Vergangenheit).
    """
    if stunden_versatz is None:
        stunden_versatz = [-1, -2]
    jetzt = pd.Timestamp.now(tz="UTC")
    return pd.DataFrame(
        {
            "collected_at": [jetzt + pd.Timedelta(hours=h) for h in stunden_versatz],
            "kwh_erzeugt": [5.0, 3.0][: len(stunden_versatz)],
            "kwh_verbraucht": [2.0, 1.0][: len(stunden_versatz)],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests: _summe_kwh
# ─────────────────────────────────────────────────────────────────────────────


def test_summe_kwh_erzeugt_addiert_richtig():
    df = baue_test_df()
    ergebnis = _summe_kwh(df, "kwh_erzeugt", "Tag")
    assert ergebnis == 8.0


def test_summe_kwh_verbraucht_addiert_richtig():
    df = baue_test_df()
    ergebnis = _summe_kwh(df, "kwh_verbraucht", "Tag")
    assert ergebnis == 3.0


def test_summe_kwh_gibt_null_zurueck_wenn_keine_werte_im_zeitraum():
    """Werte 400 Tage in der Vergangenheit → außerhalb jedes Zeitraums."""
    vor_langem = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=400)
    df = pd.DataFrame(
        {
            "collected_at": [vor_langem],
            "kwh_erzeugt": [100.0],
            "kwh_verbraucht": [50.0],
        }
    )
    assert _summe_kwh(df, "kwh_erzeugt", "Tag") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Woche") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Monat") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Jahr") == 0.0


def test_summe_kwh_monat_schliesst_tageswerte_ein():
    """Heutige Werte müssen auch im Monatszeitraum auftauchen."""
    df = baue_test_df()
    assert _summe_kwh(df, "kwh_erzeugt", "Monat") == 8.0


def test_summe_kwh_woche_schliesst_tageswerte_ein():
    df = baue_test_df()
    assert _summe_kwh(df, "kwh_erzeugt", "Woche") == 8.0


def test_summe_kwh_jahr_schliesst_tageswerte_ein():
    df = baue_test_df()
    assert _summe_kwh(df, "kwh_erzeugt", "Jahr") == 8.0


def test_summe_kwh_wert_von_vor_8_tagen_nicht_in_woche():
    """Wert von vor 8 Tagen darf nicht im 7-Tage-Fenster auftauchen."""
    jetzt = pd.Timestamp.now(tz="UTC")
    df = pd.DataFrame(
        {
            "collected_at": [jetzt - pd.Timedelta(days=8)],
            "kwh_erzeugt": [42.0],
            "kwh_verbraucht": [10.0],
        }
    )
    assert _summe_kwh(df, "kwh_erzeugt", "Woche") == 0.0


def test_summe_kwh_leerer_dataframe_gibt_null():
    df = pd.DataFrame(columns=["collected_at", "kwh_erzeugt", "kwh_verbraucht"])
    # Leerer DataFrame → .sum() sollte 0.0 zurückgeben
    result = _summe_kwh(df, "kwh_erzeugt", "Tag")
    assert result == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Tests: _kpi_card (HTML-Ausgabe)
# ─────────────────────────────────────────────────────────────────────────────


def test_kpi_card_enthaelt_titel():
    html = _kpi_card("⚡", "Heute erzeugt", "5.0 kWh", "Stand jetzt")
    assert "Heute erzeugt" in html


def test_kpi_card_enthaelt_wert():
    html = _kpi_card("⚡", "Heute erzeugt", "5.0 kWh", "Stand jetzt")
    assert "5.0 kWh" in html


def test_kpi_card_enthaelt_untertitel():
    html = _kpi_card("⚡", "Heute erzeugt", "5.0 kWh", "Stand jetzt")
    assert "Stand jetzt" in html


def test_kpi_card_wert_farbe_wird_uebernommen():
    html = _kpi_card("⚡", "Test", "1.0", "sub", wert_farbe="#2ecc71")
    assert "#2ecc71" in html


def test_kpi_card_html_ist_vollstaendiger_div():
    """Der HTML-Block muss genau einen öffnenden und schließenden div haben."""
    html = _kpi_card("⚡", "Test", "0", "sub")
    assert html.count("<div") == html.count("</div")


# ─────────────────────────────────────────────────────────────────────────────
# Tests: _auslastung_bar
# ─────────────────────────────────────────────────────────────────────────────


def test_auslastung_bar_enthaelt_text():
    html = _auslastung_bar(50.0, "50.0 %")
    assert "50.0 %" in html


def test_auslastung_bar_gruen_bei_hoher_auslastung():
    """≥ 60 % → grüne Balkenfarbe."""
    import config

    html = _auslastung_bar(80.0, "80.0 %")
    assert config.FARBE_UEBERSCHUSS in html


def test_auslastung_bar_rot_bei_niedriger_auslastung():
    """< 25 % → rote Balkenfarbe."""
    import config

    html = _auslastung_bar(10.0, "10.0 %")
    assert config.FARBE_DEFIZIT in html


def test_auslastung_bar_null_laesst_keinen_balken_erscheinen():
    """0 % Auslastung → Balkenbreite 0.0%."""
    html = _auslastung_bar(0.0, "—")
    assert "width:0.0%" in html


def test_kpi_card_hat_min_height():
    """Alle Kacheln müssen min-height gesetzt haben (für gleichmäßige Höhe)."""
    html = _kpi_card("⚡", "Test", "1.0", "sub")
    assert "min-height" in html


def test_auslastung_bar_hat_min_height():
    html = _auslastung_bar(50.0, "50.0 %")
    assert "min-height" in html


# ─────────────────────────────────────────────────────────────────────────────
# Tests: _mini_stat
# ─────────────────────────────────────────────────────────────────────────────


def test_mini_stat_enthaelt_label():
    html = _mini_stat("🌿", "CO₂ eingespart", "42 kg")
    assert "CO₂ eingespart" in html


def test_mini_stat_enthaelt_wert():
    html = _mini_stat("🌿", "CO₂ eingespart", "42 kg")
    assert "42 kg" in html


def test_mini_stat_farbe_wird_uebernommen():
    html = _mini_stat("⏳", "Prognose", "~8 Jahre", "#f39c12")
    assert "#f39c12" in html


def test_mini_stat_html_vollstaendig():
    html = _mini_stat("⏳", "Test", "Wert")
    assert html.count("<div") == html.count("</div")

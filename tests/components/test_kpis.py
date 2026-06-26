"""Unittests für kpis.py: Hilfs- und HTML-Funktionen."""

import pandas as pd

from components.kpis import (
    _auslastung_bar,
    _bilanz_spalte,
    _kpi_card,
    _mini_stat,
    _momentan_block,
    _summe_kwh,
    show_energiebilanz,
    show_momentan,
)


def baue_test_df(stunden_versatz: list[int] | None = None) -> pd.DataFrame:
    """Erstellt einen DataFrame mit Messpunkten relativ zu jetzt."""
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


def baue_bilanz_dict() -> dict:
    return {"erzeugt": 12.0, "verbraucht": 8.0, "eigen": 6.0, "netz": 2.0, "quote": 75.0}


# ── _summe_kwh ───────────────────────────────────────────────────────────────


def test_summe_kwh_erzeugt_addiert_richtig():
    assert _summe_kwh(baue_test_df(), "kwh_erzeugt", "Tag") == 8.0


def test_summe_kwh_verbraucht_addiert_richtig():
    assert _summe_kwh(baue_test_df(), "kwh_verbraucht", "Tag") == 3.0


def test_summe_kwh_gibt_null_zurueck_wenn_keine_werte_im_zeitraum():
    vor_langem = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=400)
    df = pd.DataFrame(
        {"collected_at": [vor_langem], "kwh_erzeugt": [100.0], "kwh_verbraucht": [50.0]}
    )
    assert _summe_kwh(df, "kwh_erzeugt", "Tag") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Woche") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Monat") == 0.0
    assert _summe_kwh(df, "kwh_erzeugt", "Jahr") == 0.0


def test_summe_kwh_wert_von_vor_8_tagen_nicht_in_woche():
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
    assert _summe_kwh(df, "kwh_erzeugt", "Tag") == 0.0


# ── _kpi_card ────────────────────────────────────────────────────────────────


def test_kpi_card_enthaelt_titel_wert_untertitel():
    html = _kpi_card("⚡", "Heute erzeugt", "5.0 kWh", "Stand jetzt")
    assert "Heute erzeugt" in html
    assert "5.0 kWh" in html
    assert "Stand jetzt" in html


def test_kpi_card_wert_farbe_wird_uebernommen():
    html = _kpi_card("⚡", "Test", "1.0", "sub", wert_farbe="#2ecc71")
    assert "#2ecc71" in html


def test_kpi_card_html_ist_vollstaendiger_div():
    html = _kpi_card("⚡", "Test", "0", "sub")
    assert html.count("<div") == html.count("</div")


def test_kpi_card_hat_min_height():
    assert "min-height" in _kpi_card("⚡", "Test", "1.0", "sub")


# ── _auslastung_bar ──────────────────────────────────────────────────────────


def test_auslastung_bar_enthaelt_text():
    assert "50.0 %" in _auslastung_bar(50.0, "50.0 %")


def test_auslastung_bar_gruen_bei_hoher_auslastung():
    import config

    assert config.FARBE_UEBERSCHUSS in _auslastung_bar(80.0, "80.0 %")


def test_auslastung_bar_rot_bei_niedriger_auslastung():
    import config

    assert config.FARBE_DEFIZIT in _auslastung_bar(10.0, "10.0 %")


def test_auslastung_bar_null_laesst_keinen_balken_erscheinen():
    assert "width:0.0%" in _auslastung_bar(0.0, "—")


# ── _mini_stat ───────────────────────────────────────────────────────────────


def test_mini_stat_enthaelt_label_und_wert():
    html = _mini_stat("🌿", "CO₂ eingespart", "42 kg")
    assert "CO₂ eingespart" in html
    assert "42 kg" in html


def test_mini_stat_farbe_wird_uebernommen():
    assert "#f39c12" in _mini_stat("⏳", "Prognose", "~8 Jahre", "#f39c12")


# ── _momentan_block (NEU) ────────────────────────────────────────────────────


def test_momentan_block_enthaelt_label_und_wert():
    html = _momentan_block("⚡", "Momentanerzeugung", "2.50 kW", "#2ecc71")
    assert "Momentanerzeugung" in html
    assert "2.50 kW" in html


def test_momentan_block_html_vollstaendig():
    html = _momentan_block("🏠", "Test", "1 kW", "white")
    assert html.count("<div") == html.count("</div")


# ── _bilanz_spalte (NEU) ─────────────────────────────────────────────────────


def test_bilanz_spalte_enthaelt_titel_und_werte():
    html = _bilanz_spalte("Heute", baue_bilanz_dict())
    assert "Heute" in html
    assert "12.0 kWh" in html
    assert "8.0 kWh" in html


def test_bilanz_spalte_zeigt_pv_quote():
    assert "75%" in _bilanz_spalte("Heute", baue_bilanz_dict())


def test_bilanz_spalte_html_vollstaendig():
    html = _bilanz_spalte("Test", baue_bilanz_dict())
    assert html.count("<div") == html.count("</div")


def test_bilanz_spalte_null_werte_kein_crash():
    leer = {"erzeugt": 0.0, "verbraucht": 0.0, "eigen": 0.0, "netz": 0.0, "quote": 0.0}
    assert "0.0 kWh" in _bilanz_spalte("Leer", leer)


# ── Render-Funktionen sind aufrufbar ─────────────────────────────────────────


def test_show_momentan_ist_aufrufbar():
    assert callable(show_momentan)


def test_show_energiebilanz_ist_aufrufbar():
    assert callable(show_energiebilanz)
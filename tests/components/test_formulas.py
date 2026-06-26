"""Unittests für die Berechnungen in formulas.py."""

import pandas as pd
import pytest

from components.formulas import (
    differenz_erzeugt_verbraucht,
    summen_zeitraum,
    umrechnung_in_kwh,
)


def baue_test_df(zeiten, pv_werte, netz_werte):
    """Kleiner Helfer, der einen DataFrame im erwarteten Format baut."""
    return pd.DataFrame(
        {
            "collected_at": zeiten,
            "pv_erzeugung_kw": pv_werte,
            "netz_wert_kw": netz_werte,
        }
    )


def baue_heute_df(pv=2.0, netz=4.0):
    """Zwei Messpunkte am heutigen Mittag (für die Zeitraum-Aggregation)."""
    mittag = pd.Timestamp.now(tz="Europe/Berlin").normalize() + pd.Timedelta(hours=12)
    return baue_test_df(
        [mittag.tz_convert("UTC"), (mittag + pd.Timedelta(hours=1)).tz_convert("UTC")],
        pv_werte=[pv, pv],
        netz_werte=[netz, netz],
    )


# ── umrechnung_in_kwh: Trapezregel ───────────────────────────────────────────


def test_konstante_leistung_eine_stunde():
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[2.0, 2.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(1.0)
    assert ergebnis["kwh_verbraucht"].sum() == pytest.approx(2.0)


def test_steigende_leistung_trapezregel():
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[0.0, 2.0],
        netz_werte=[0.0, 0.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(1.0)


def test_delta_h_wird_richtig_berechnet():
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T08:30:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[1.0, 1.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["delta_h"].iloc[0] == pytest.approx(0.5)


def test_datenluecke_wird_nicht_mitintegriert():
    """Ein Abstand > MAX_LUECKE_H trägt 0 kWh bei (delta_h auf 0 gesetzt)."""
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T20:00:00+00:00"],  # 12 h Lücke
        pv_werte=[2.0, 2.0],
        netz_werte=[2.0, 2.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(0.0)


# ── umrechnung_in_kwh: Eigenverbrauch (NEU) ──────────────────────────────────


def test_eigenverbrauch_ist_min_von_erzeugung_und_verbrauch():
    # Erzeugung 1 kW, Verbrauch 3 kW über 1 h → Eigenverbrauch = min = 1 kWh
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[3.0, 3.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_pv_eigen"].sum() == pytest.approx(1.0)


def test_eigenverbrauch_gedeckelt_durch_verbrauch():
    # Erzeugung 4 kW, Verbrauch 1 kW → nur 1 kWh selbst verbraucht (Rest = Einspeisung)
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[4.0, 4.0],
        netz_werte=[1.0, 1.0],
    )
    ergebnis = umrechnung_in_kwh(df)
    assert ergebnis["kwh_erzeugt"].sum() == pytest.approx(4.0)
    assert ergebnis["kwh_pv_eigen"].sum() == pytest.approx(1.0)


# ── summen_zeitraum (NEU) ────────────────────────────────────────────────────


def test_summen_zeitraum_tag_rechnet_korrekt():
    df_kwh = umrechnung_in_kwh(baue_heute_df(pv=2.0, netz=4.0))
    s = summen_zeitraum(df_kwh, "Tag")
    assert s["erzeugt"] == pytest.approx(2.0)     # (2+2)/2 × 1 h
    assert s["verbraucht"] == pytest.approx(4.0)
    assert s["eigen"] == pytest.approx(2.0)        # min(2, 4) = 2
    assert s["netz"] == pytest.approx(2.0)         # 4 − 2
    assert s["quote"] == pytest.approx(50.0)       # 2 / 4 × 100


def test_summen_zeitraum_monat_und_jahr_enthalten_heute():
    """Bei ausschließlich heutigen Daten sind Tag = Monat = Jahr."""
    df_kwh = umrechnung_in_kwh(baue_heute_df(pv=2.0, netz=4.0))
    for zeitraum in ["Monat", "Jahr"]:
        s = summen_zeitraum(df_kwh, zeitraum)
        assert s["erzeugt"] == pytest.approx(2.0)
        assert s["verbraucht"] == pytest.approx(4.0)


def test_summen_zeitraum_quote_null_ohne_verbrauch():
    df_kwh = umrechnung_in_kwh(baue_heute_df(pv=2.0, netz=0.0))
    s = summen_zeitraum(df_kwh, "Tag")
    assert s["verbraucht"] == pytest.approx(0.0)
    assert s["quote"] == 0.0


def test_summen_zeitraum_alte_daten_ergeben_null():
    vor_langem = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=400)
    df = baue_test_df(
        [vor_langem, vor_langem + pd.Timedelta(hours=1)],
        pv_werte=[5.0, 5.0],
        netz_werte=[5.0, 5.0],
    )
    df_kwh = umrechnung_in_kwh(df)
    for zeitraum in ["Tag", "Monat", "Jahr"]:
        s = summen_zeitraum(df_kwh, zeitraum)
        assert s["erzeugt"] == 0.0
        assert s["verbraucht"] == 0.0


def test_summen_zeitraum_unbekannter_zeitraum_wirft_fehler():
    df_kwh = umrechnung_in_kwh(baue_heute_df())
    with pytest.raises(ValueError):
        summen_zeitraum(df_kwh, "Quartal")


# ── differenz_erzeugt_verbraucht ─────────────────────────────────────────────


def test_differenz_erzeugt_verbraucht_ergibt_defizit():
    df = baue_test_df(
        ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
        pv_werte=[1.0, 1.0],
        netz_werte=[2.0, 2.0],
    )
    bilanz = differenz_erzeugt_verbraucht(df)
    assert len(bilanz) == 1
    assert bilanz.iloc[0] == pytest.approx(-1.0)
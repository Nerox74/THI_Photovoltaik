"""Unittests für charts.py (Tagesverlauf + 3-Monats-Kalender)."""

import matplotlib

matplotlib.use("Agg")  # kein Bildschirm nötig, muss vor plt-Import stehen

import matplotlib.pyplot as plt
import pandas as pd

from components.charts import (
    create_chart_tagesverlauf,
    create_pie_pv_quote,
    draw_calendar_3monate,
)

def baue_heute_df(pv=2.0, netz=4.0):
    """Zwei Messpunkte am heutigen Mittag (robust gegen die Mitternachts-Grenze)."""
    mittag = pd.Timestamp.now(tz="Europe/Berlin").normalize() + pd.Timedelta(hours=12)
    return pd.DataFrame(
        {
            "collected_at": [
                mittag.tz_convert("UTC"),
                (mittag + pd.Timedelta(hours=1)).tz_convert("UTC"),
            ],
            "pv_erzeugung_kw": [pv, pv],
            "netz_wert_kw": [netz, netz],
        }
    )


def baue_leeren_df():
    return pd.DataFrame(columns=["collected_at", "pv_erzeugung_kw", "netz_wert_kw"])


def baue_test_series():
    """Series mit Tagesbilanz-Werten für den Kalender."""
    return pd.Series(
        [1.5, -0.5, 2.0],
        index=pd.to_datetime(["2026-06-17", "2026-06-18", "2026-06-19"]),
        name="bilanz_kwh",
    )


# ── Tagesverlauf ─────────────────────────────────────────────────────────────


def test_tagesverlauf_gibt_figure_zurueck():
    fig = create_chart_tagesverlauf(baue_heute_df())
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_tagesverlauf_hat_zwei_linien():
    """Eine Linie Erzeugung + eine Linie Verbrauch = 2."""
    fig = create_chart_tagesverlauf(baue_heute_df())
    assert len(fig.axes[0].lines) == 2
    plt.close(fig)


def test_tagesverlauf_achsenbeschriftung():
    fig = create_chart_tagesverlauf(baue_heute_df())
    ax = fig.axes[0]
    assert ax.get_xlabel() == "Uhrzeit"
    assert "kW" in ax.get_ylabel()
    plt.close(fig)


def test_tagesverlauf_titel():
    fig = create_chart_tagesverlauf(baue_heute_df())
    assert "Tagesverlauf" in fig.axes[0].get_title()
    plt.close(fig)


def test_tagesverlauf_ohne_heutige_daten_gibt_platzhalter():
    """Daten von gestern → Platzhalter-Figur ohne Linien, kein Crash."""
    # Gestern um 10:00 Berlin als FESTER Anker – so rutscht auch "gestern + 1h"
    # nie über Mitternacht in den heutigen Tag (sonst zeitabhängig/flaky).
    gestern_vormittag = (
        pd.Timestamp.now(tz="Europe/Berlin").normalize()
        - pd.Timedelta(days=1)
        + pd.Timedelta(hours=10)
    )
    df = pd.DataFrame(
        {
            "collected_at": [
                gestern_vormittag.tz_convert("UTC"),
                (gestern_vormittag + pd.Timedelta(hours=1)).tz_convert("UTC"),
            ],
            "pv_erzeugung_kw": [1.0, 1.0],
            "netz_wert_kw": [2.0, 2.0],
        }
    )
    fig = create_chart_tagesverlauf(df)
    assert isinstance(fig, plt.Figure)
    assert len(fig.axes[0].lines) == 0

def test_tagesverlauf_leerer_df_gibt_figure_zurueck():
    fig = create_chart_tagesverlauf(baue_leeren_df())
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── 3-Monats-Kalender ────────────────────────────────────────────────────────


def test_kalender_gibt_figure_zurueck():
    fig = draw_calendar_3monate(baue_test_series(), unit="kWh")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_kalender_hat_vier_achsen():
    """3 Monats-Subplots + 1 Colorbar-Achse = 4."""
    fig = draw_calendar_3monate(baue_test_series(), unit="kWh")
    assert len(fig.axes) == 4
    plt.close(fig)


def test_kalender_leere_series_gibt_figure_zurueck():
    leer = pd.Series([], dtype=float)
    leer.index = pd.DatetimeIndex([])
    fig = draw_calendar_3monate(leer, unit="kWh")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_pie_pv_quote_zeigt_zwei_segmente():
    """Mit Eigen- und Netzanteil entstehen genau zwei Tortenstücke."""
    summen = {"eigen": 3.0, "netz": 1.0, "quote": 75.0}
    fig = create_pie_pv_quote(summen, "Heute")
    assert isinstance(fig, plt.Figure)
    # Ein Pie erzeugt pro Segment ein Wedge-Patch
    assert len(fig.axes[0].patches) == 2


def test_pie_pv_quote_ohne_daten_gibt_platzhalter():
    """Ohne Verbrauch (eigen + netz = 0) kommt die Platzhalter-Figur ohne Segmente."""
    summen = {"eigen": 0.0, "netz": 0.0, "quote": 0.0}
    fig = create_pie_pv_quote(summen, "Heute")
    assert isinstance(fig, plt.Figure)
    assert len(fig.axes[0].patches) == 0
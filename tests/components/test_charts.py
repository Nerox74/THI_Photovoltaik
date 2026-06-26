"""Unittests für charts.py."""

import matplotlib

matplotlib.use("Agg")  # kein Bildschirm nötig, muss vor plt-Import stehen

import matplotlib.pyplot as plt
import pandas as pd

from components.charts import (
    create_chart_balkendiagramm,
    create_chart_kurvendiagramm,
    draw_calendar_3monate,
)


def baue_test_df():
    """Hilfsfunktion: DataFrame mit Rohdaten im erwarteten Format."""
    return pd.DataFrame(
        {
            "collected_at": pd.to_datetime(
                ["2026-06-19T08:00:00+00:00", "2026-06-19T09:00:00+00:00"],
                utc=True,
            ),
            "pv_erzeugung_kw": [1.0, 2.0],
            "netz_wert_kw": [3.0, 3.0],
        }
    )


def baue_test_series():
    """Hilfsfunktion: Series mit Tagesbilanz-Werten für den Kalender."""
    return pd.Series(
        [1.5, -0.5, 2.0],
        index=pd.to_datetime(["2026-06-17", "2026-06-18", "2026-06-19"]),
        name="bilanz_kwh",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Typ-Checks: alle Chart-Funktionen müssen ein plt.Figure zurückgeben
# ─────────────────────────────────────────────────────────────────────────────


def test_balkendiagramm_gibt_figure_zurueck():
    fig = create_chart_balkendiagramm(baue_test_df())
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_kurvendiagramm_gibt_figure_zurueck():
    fig = create_chart_kurvendiagramm(baue_test_df())
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_calendar_3monate_gibt_figure_zurueck():
    fig = draw_calendar_3monate(baue_test_series(), unit="kWh")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Balkendiagramm
# ─────────────────────────────────────────────────────────────────────────────


def test_balkendiagramm_achsenbeschriftung():
    fig = create_chart_balkendiagramm(baue_test_df())
    ax = fig.axes[0]
    assert ax.get_xlabel() == "Uhrzeit"
    assert "Bilanz" in ax.get_ylabel()
    plt.close(fig)


def test_balkendiagramm_hat_24_balken():
    """Pro Stunde ein Balken → genau 24 Stück."""
    fig = create_chart_balkendiagramm(baue_test_df())
    ax = fig.axes[0]
    assert len(ax.patches) == 24
    plt.close(fig)


def test_balkendiagramm_titel_enthaelt_tage_info():
    """Der Titel soll die Anzahl der Tage enthalten."""
    fig = create_chart_balkendiagramm(baue_test_df())
    ax = fig.axes[0]
    assert "Tag" in ax.get_title() or "Tage" in ax.get_title()
    plt.close(fig)


def test_balkendiagramm_leerer_df_gibt_figure_zurueck():
    """Auch mit leerem DataFrame darf kein Crash passieren."""
    leer = pd.DataFrame(columns=["collected_at", "pv_erzeugung_kw", "netz_wert_kw"])
    fig = create_chart_balkendiagramm(leer)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Kurvendiagramm
# ─────────────────────────────────────────────────────────────────────────────


def test_kurvendiagramm_titel_korrekt():
    fig = create_chart_kurvendiagramm(baue_test_df())
    ax = fig.axes[0]
    titel = ax.get_title()
    assert "Erzeugung" in titel
    assert "Verbrauch" in titel
    plt.close(fig)


def test_kurvendiagramm_hat_zwei_linien():
    """Eine Linie Erzeugung + eine Linie Verbrauch = 2."""
    fig = create_chart_kurvendiagramm(baue_test_df())
    ax = fig.axes[0]
    assert len(ax.lines) == 2
    plt.close(fig)


def test_kurvendiagramm_leerer_df_gibt_figure_zurueck():
    leer = pd.DataFrame(columns=["collected_at", "pv_erzeugung_kw", "netz_wert_kw"])
    fig = create_chart_kurvendiagramm(leer)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 3-Monats-Kalender
# ─────────────────────────────────────────────────────────────────────────────


def test_draw_calendar_3monate_hat_vier_achsen():
    """3 Monats-Subplots + 1 Colorbar-Achse = 4."""
    fig = draw_calendar_3monate(baue_test_series(), unit="kWh")
    assert len(fig.axes) == 4
    plt.close(fig)


def test_draw_calendar_3monate_leere_series_gibt_figure_zurueck():
    """Auch ohne Datenpunkte darf kein Crash passieren."""
    leer = pd.Series([], dtype=float)
    leer.index = pd.DatetimeIndex([])
    fig = draw_calendar_3monate(leer, unit="kWh")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

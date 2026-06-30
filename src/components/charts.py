"""Erstellt die Charts zur Visualisierung der PV-Stromerzeugung.

- create_chart_tagesverlauf : Zeitverlauf Erzeugung & Verbrauch des AKTUELLEN Tages
- draw_calendar_3monate     : Tägliche Bilanz der letzten 3 Monate (Heatmap-Kalender)
"""

import calendar
import logging

import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

import config

logger = logging.getLogger(__name__)

MONTH_NAMES_DE = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]


def _leere_figur(text: str):
    """Platzhalter-Figur, wenn (noch) keine Daten vorliegen."""
    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor=config.CHART_BG)
    ax.set_facecolor(config.PANEL_BG)
    ax.text(
        0.5,
        0.5,
        text,
        ha="center",
        va="center",
        color=config.TEXT_GEDIMMT,
        fontsize=11,
        transform=ax.transAxes,
    )
    ax.axis("off")
    return fig

def _mit_luecken_brechen(x, y, max_luecke_h):
    """Bricht die Linie an Datenlücken: fügt einen NaN-Punkt ein, wo der Abstand
    zweier Messpunkte größer als max_luecke_h (Stunden) ist. matplotlib zeichnet
    über NaN keine Linie -> keine falsche Interpolation über messfreie Zeiträume.
    """
    x = list(x)
    y = list(y)
    aus_x, aus_y = [], []
    for i in range(len(x)):
        aus_x.append(x[i])
        aus_y.append(y[i])
        if i < len(x) - 1:
            luecke_h = (x[i + 1] - x[i]).total_seconds() / 3600
            if luecke_h > max_luecke_h:
                aus_x.append(x[i] + (x[i + 1] - x[i]) / 2)
                aus_y.append(float("nan"))  # Trennpunkt -> Linie bricht hier
    return aus_x, aus_y

def create_chart_tagesverlauf(df: pd.DataFrame):
    """Zeitverlauf von Erzeugung und Verbrauch (Leistung in kW) für den heutigen Tag."""
    df = df.copy()
    df["collected_at"] = pd.to_datetime(df["collected_at"], format="ISO8601", utc=True)
    df["lokal"] = df["collected_at"].dt.tz_convert("Europe/Berlin")

    heute = pd.Timestamp.now(tz="Europe/Berlin").normalize()
    df_heute = df.loc[df["lokal"] >= heute].sort_values("lokal")

    if df_heute.empty:
        logger.warning("Tagesverlauf: keine Daten für heute")
        return _leere_figur("Noch keine Messdaten für heute")

    x = df_heute["lokal"].dt.tz_localize(None)  # naive Lokalzeit für die x-Achse

    # Linien an Datenlücken (> MAX_LUECKE_H) unterbrechen, statt zu interpolieren
    x_b, y_erz = _mit_luecken_brechen(x, df_heute["pv_erzeugung_kw"], config.MAX_LUECKE_H)
    _, y_verb = _mit_luecken_brechen(x, df_heute["netz_wert_kw"], config.MAX_LUECKE_H)

    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor=config.CHART_BG)
    ax.set_facecolor(config.PANEL_BG)
    ax.yaxis.grid(True, color="#2a3045", linewidth=0.5, linestyle="--", zorder=0)
    ax.set_axisbelow(True)

    ax.fill_between(x_b, y_erz, alpha=0.20, color=config.FARBE_UEBERSCHUSS, zorder=1)
    ax.fill_between(x_b, y_verb, alpha=0.15, color=config.FARBE_DEFIZIT, zorder=1)
    ax.plot(
        x_b,
        y_erz,
        color=config.FARBE_UEBERSCHUSS,
        linewidth=2.0,
        marker="o",
        markersize=2.5,
        label="Erzeugung (kW)",
        zorder=3,
    )
    ax.plot(
        x_b,
        y_verb,
        color=config.FARBE_DEFIZIT,
        linewidth=2.0,
        marker="o",
        markersize=2.5,
        label="Verbrauch (kW)",
        zorder=3,
    )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", colors=config.TEXT_GEDIMMT, labelsize=7, length=0)
    ax.set_xlabel("Uhrzeit", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_ylabel("Leistung (kW)", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_title(
        "Tagesverlauf heute: Erzeugung & Verbrauch",
        color="white",
        fontsize=9,
        fontweight="bold",
        pad=10,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(
        facecolor=config.PANEL_BG,
        edgecolor="none",
        labelcolor="white",
        fontsize=7,
        loc="upper right",
        framealpha=0.85,
    )

    plt.tight_layout(pad=1.2)
    return fig


def draw_calendar_3monate(data: pd.Series, unit: str):
    """Zeichnet die letzten 3 Monate nebeneinander als eine breite Kalender-Grafik."""
    heute = pd.Timestamp.now()
    monate = []
    for i in range(2, -1, -1):
        m = (heute.month - i - 1) % 12 + 1
        y = heute.year if heute.month - i > 0 else heute.year - 1
        monate.append((y, m))

    alle_werte = []
    for y, m in monate:
        d = data[(data.index.year == y) & (data.index.month == m)]
        alle_werte.extend(d.dropna().tolist())

    vmax = max(abs(min(alle_werte)), abs(max(alle_werte))) if alle_werte else 1.0
    vmax = vmax or 1.0
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    cmap = plt.cm.RdYlGn

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), facecolor=config.CHART_BG)
    fig.subplots_adjust(top=0.88, bottom=0.14, left=0.02, right=0.98, wspace=0.08)
    fig.suptitle(
        "Tägliche Bilanz – Letzte 3 Monate (Erzeugung − Verbrauch)",
        fontsize=11,
        color="white",
        fontweight="bold",
    )

    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    for ax, (year, month) in zip(axes, monate):
        ax.set_facecolor(config.PANEL_BG)
        ax.set_title(
            f"{MONTH_NAMES_DE[month - 1]} {year}",
            color="white",
            fontsize=9,
            fontweight="bold",
            pad=6,
        )

        monat_data = data[(data.index.year == year) & (data.index.month == month)]
        if monat_data.empty:
            logger.debug("Kalender: %s %d ohne Daten", MONTH_NAMES_DE[month - 1], year)

        first_weekday = calendar.monthrange(year, month)[0]
        num_days = calendar.monthrange(year, month)[1]

        for d, label in enumerate(day_labels):
            ax.text(
                d + 0.5,
                6.6,
                label,
                ha="center",
                va="center",
                color=config.TEXT_GEDIMMT,
                fontsize=6,
                fontweight="bold",
            )

        row, col = 0, first_weekday
        for day in range(1, num_days + 1):
            date = pd.Timestamp(year=year, month=month, day=day)
            value = monat_data.get(date, np.nan)

            if pd.isna(value):
                cell_color, text_color = config.LEER_TAG_BG, config.TEXT_SCHWACH
            else:
                rgba = cmap(norm(value))
                cell_color = rgba
                brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                text_color = "black" if brightness > 0.5 else "white"

            rect = mpatches.FancyBboxPatch(
                (col + 0.05, 5 - row + 0.05),
                0.9,
                0.85,
                boxstyle="round,pad=0.05",
                facecolor=cell_color,
                edgecolor=config.CHART_BG,
                linewidth=0.8,
            )
            ax.add_patch(rect)
            ax.text(
                col + 0.5,
                5 - row + 0.55,
                str(day),
                ha="center",
                va="center",
                color=text_color,
                fontsize=6,
                fontweight="bold",
            )
            if not pd.isna(value):
                ax.text(
                    col + 0.5,
                    5 - row + 0.18,
                    f"{value:+.0f}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=4.5,
                )

            col += 1
            if col > 6:
                col, row = 0, row + 1

        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")

    cbar_ax = fig.add_axes([0.15, 0.03, 0.7, 0.025])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(
        f"Bilanz ({unit})   ← Verbrauchsüberschuss  |  Erzeugungsüberschuss →",
        color="white",
        fontsize=8,
    )
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=7)

    return fig

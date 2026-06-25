"""Erstellt die Charts zur Visualisierung der PV-Stromerzeugung."""

import calendar
import logging

import matplotlib.cm as cm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

import config
from components.formulas import umrechnung_in_kwh

logger = logging.getLogger(__name__)

MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def create_chart_balkendiagramm(df: pd.DataFrame):
    """Balkendiagramm: durchschnittliche Tagesbilanz (Erzeugung − Verbrauch) pro Stunde.

    Teilt die Gesamtsumme durch die Anzahl der Tage, damit die Y-Achse
    einen sinnvollen „typischen Tag" zeigt – statt kumulierten Werten
    über den gesamten Messzeitraum.
    """
    df = umrechnung_in_kwh(df)
    if df.empty:
        logger.warning("Balkendiagramm: keine Daten vorhanden")
        return plt.figure()

    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour
    anzahl_tage = max(df["collected_at"].dt.date.nunique(), 1)

    gruppen = df.groupby("stunde")[["kwh_erzeugt", "kwh_verbraucht"]].sum()
    stunden_bilanz = (
        (gruppen["kwh_erzeugt"] - gruppen["kwh_verbraucht"]) / anzahl_tage
    ).reindex(range(24), fill_value=0)

    farben = [
        config.FARBE_UEBERSCHUSS if v >= 0 else config.FARBE_DEFIZIT
        for v in stunden_bilanz
    ]

    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor=config.CHART_BG)
    ax.set_facecolor(config.PANEL_BG)

    # Dezente horizontale Gitterlinien
    ax.yaxis.grid(True, color="rgba(255,255,255,0.06)" if False else "#2a3045",
                  linewidth=0.5, linestyle="--", zorder=0)
    ax.set_axisbelow(True)

    ax.bar(
        stunden_bilanz.index, stunden_bilanz.values,
        color=farben, edgecolor="none", linewidth=0, width=0.75,
        alpha=0.92, zorder=2,
    )
    ax.axhline(0, color=config.TEXT_GEDIMMT, linewidth=0.8, linestyle="-", zorder=3)

    # Nur Max-Überschuss und Max-Defizit annotieren (kein Clutter)
    val_max = stunden_bilanz.max()
    val_min = stunden_bilanz.min()
    y_range = max(abs(val_max), abs(val_min)) or 1
    pad = y_range * 0.06

    for stunde, val in [(stunden_bilanz.idxmax(), val_max),
                        (stunden_bilanz.idxmin(), val_min)]:
        if abs(val) < 0.001:
            continue
        ax.annotate(
            f"{val:+.1f} kWh",
            xy=(stunde, val),
            xytext=(stunde, val + pad * (1 if val >= 0 else -1)),
            ha="center",
            va="bottom" if val >= 0 else "top",
            color="white", fontsize=6.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc=config.PANEL_BG,
                      ec="none", alpha=0.75),
        )

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)], color=config.TEXT_GEDIMMT,
                       fontsize=6)
    ax.tick_params(axis="y", colors=config.TEXT_GEDIMMT, labelsize=6.5)
    ax.tick_params(axis="both", length=0)
    ax.set_xlabel("Uhrzeit", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_ylabel("Ø Bilanz (kWh)", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_title(
        f"Ø Tagesbilanz pro Stunde  (über {anzahl_tage} {'Tag' if anzahl_tage == 1 else 'Tage'})",
        color="white", fontsize=9, fontweight="bold", pad=10,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    legende = [
        mpatches.Patch(color=config.FARBE_UEBERSCHUSS, label="Überschuss"),
        mpatches.Patch(color=config.FARBE_DEFIZIT, label="Defizit"),
    ]
    ax.legend(
        handles=legende,
        facecolor=config.PANEL_BG, edgecolor="none",
        labelcolor="white", fontsize=7,
        loc="upper right", framealpha=0.85,
    )

    plt.tight_layout(pad=1.2)
    return fig


def create_chart_kurvendiagramm(df: pd.DataFrame):
    """Kurvendiagramm: durchschnittlicher Tagesverlauf Erzeugung & Verbrauch.

    Zeigt den typischen Verlauf eines Tages (Mittelwert über alle gemessenen Tage),
    nicht die kumulierten Gesamtwerte.
    """
    df = umrechnung_in_kwh(df)
    if df.empty:
        logger.warning("Kurvendiagramm: keine Daten vorhanden")
        return plt.figure()

    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour
    anzahl_tage = max(df["collected_at"].dt.date.nunique(), 1)

    stunden = (
        df.groupby("stunde")[["kwh_erzeugt", "kwh_verbraucht"]]
        .sum()
        .div(anzahl_tage)
        .reindex(range(24), fill_value=0)
    )

    idx_max_erz  = stunden["kwh_erzeugt"].idxmax()
    max_erz      = stunden["kwh_erzeugt"].max()
    y_max        = max(max_erz, stunden["kwh_verbraucht"].max()) or 1

    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor=config.CHART_BG)
    ax.set_facecolor(config.PANEL_BG)

    # Dezente Gitterlinien
    ax.yaxis.grid(True, color="#2a3045", linewidth=0.5, linestyle="--", zorder=0)
    ax.set_axisbelow(True)

    x = stunden.index

    # Fläche unter der Kurve (gut sichtbar, aber nicht dominant)
    ax.fill_between(x, stunden["kwh_erzeugt"],
                    alpha=0.20, color=config.FARBE_UEBERSCHUSS, zorder=1)
    ax.fill_between(x, stunden["kwh_verbraucht"],
                    alpha=0.15, color=config.FARBE_DEFIZIT, zorder=1)

    # Linien
    ax.plot(
        x, stunden["kwh_erzeugt"],
        color=config.FARBE_UEBERSCHUSS, linewidth=2.0,
        marker="o", markersize=2.5, label="Ø Erzeugung (kWh)", zorder=3,
    )
    ax.plot(
        x, stunden["kwh_verbraucht"],
        color=config.FARBE_DEFIZIT, linewidth=2.0,
        marker="o", markersize=2.5, label="Ø Verbrauch (kWh)", zorder=3,
    )

    # Nur Erzeugungsmaximum annotieren (sauberste Information)
    if max_erz > 0:
        # Text links positionieren wenn Peak nahe am rechten Rand
        x_off = -2.0 if idx_max_erz > 18 else 1.2
        ax.annotate(
            f"Peak {max_erz:.1f} kWh",
            xy=(idx_max_erz, max_erz),
            xytext=(idx_max_erz + x_off, max_erz + y_max * 0.10),
            color=config.FARBE_UEBERSCHUSS, fontsize=7, fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color=config.FARBE_UEBERSCHUSS,
                            lw=0.9, mutation_scale=8),
            bbox=dict(boxstyle="round,pad=0.2", fc=config.PANEL_BG,
                      ec="none", alpha=0.8),
        )

    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(bottom=0)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)], color=config.TEXT_GEDIMMT,
                       fontsize=6)
    ax.tick_params(axis="y", colors=config.TEXT_GEDIMMT, labelsize=6.5)
    ax.tick_params(axis="both", length=0)
    ax.set_xlabel("Uhrzeit", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_ylabel("Ø kWh", color=config.TEXT_GEDIMMT, fontsize=8, labelpad=6)
    ax.set_title(
        f"Ø Tagesverlauf: Erzeugung & Verbrauch  (über {anzahl_tage} "
        f"{'Tag' if anzahl_tage == 1 else 'Tage'})",
        color="white", fontsize=9, fontweight="bold", pad=10,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(
        facecolor=config.PANEL_BG, edgecolor="none",
        labelcolor="white", fontsize=7,
        loc="upper right", framealpha=0.85,
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

    # Gemeinsame Normierung über alle 3 Monate
    alle_werte = []
    for y, m in monate:
        d = data[(data.index.year == y) & (data.index.month == m)]
        alle_werte.extend(d.dropna().tolist())

    vmax = max(abs(min(alle_werte)), abs(max(alle_werte))) if alle_werte else 1.0
    vmax = vmax or 1.0
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    cmap = plt.cm.RdYlGn

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), facecolor=config.CHART_BG)
    # Platz für Titel oben und Colorbar unten reservieren
    fig.subplots_adjust(top=0.88, bottom=0.14, left=0.02, right=0.98, wspace=0.08)
    fig.suptitle(
        "Tägliche Bilanz – Letzte 3 Monate (Erzeugung − Verbrauch)",
        fontsize=11, color="white", fontweight="bold",
    )

    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    for ax, (year, month) in zip(axes, monate):
        ax.set_facecolor(config.PANEL_BG)
        ax.set_title(
            f"{MONTH_NAMES_DE[month - 1]} {year}",
            color="white", fontsize=9, fontweight="bold", pad=6,
        )

        monat_data = data[(data.index.year == year) & (data.index.month == month)]
        if monat_data.empty:
            logger.debug("Kalender: %s %d ohne Daten", MONTH_NAMES_DE[month - 1], year)

        first_weekday = calendar.monthrange(year, month)[0]
        num_days = calendar.monthrange(year, month)[1]

        for d, label in enumerate(day_labels):
            ax.text(
                d + 0.5, 6.6, label,
                ha="center", va="center",
                color=config.TEXT_GEDIMMT, fontsize=6, fontweight="bold",
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
                (col + 0.05, 5 - row + 0.05), 0.9, 0.85,
                boxstyle="round,pad=0.05",
                facecolor=cell_color, edgecolor=config.CHART_BG, linewidth=0.8,
            )
            ax.add_patch(rect)
            ax.text(
                col + 0.5, 5 - row + 0.55, str(day),
                ha="center", va="center",
                color=text_color, fontsize=6, fontweight="bold",
            )
            if not pd.isna(value):
                ax.text(
                    col + 0.5, 5 - row + 0.18, f"{value:+.0f}",
                    ha="center", va="center",
                    color=text_color, fontsize=4.5,
                )

            col += 1
            if col > 6:
                col, row = 0, row + 1

        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")

    # Colorbar innerhalb der Figurenränder (kein negatives y)
    cbar_ax = fig.add_axes([0.15, 0.03, 0.7, 0.025])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(
        f"Bilanz ({unit})   ← Verbrauchsüberschuss  |  Erzeugungsüberschuss →",
        color="white", fontsize=8,
    )
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=7)

    return fig

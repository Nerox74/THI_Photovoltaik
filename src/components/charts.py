"""
Hier werden die Charts erstellt, in welchen die Stromerzeugung der Photovoltaik visualisiert wird.
"""
from components.formulas import umrechnung_in_kwh, differenz_erzeugt_verbraucht

import numpy as np
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm
import calendar
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATEI_PFAD = "cleaned_data.csv"
YEAR = 2026
TITLE = f"PV-Anlage {YEAR} – Tägliche Bilanz (Erzeugung − Verbrauch)"
UNIT = "kWh"

MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]


def draw_calendar(data: pd.Series, year: int, month: int, unit: str):
    """
    Zeichnet einen Monatskalender für den gewählten Monat.
    Positiv (+) → grün, Negativ (−) → rot, Kein Wert → dunkel.
    """
    month_name = MONTH_NAMES_DE[month - 1]
    title = f"PV-Anlage {year} – {month_name} – Tägliche Bilanz (Erzeugung − Verbrauch)"

    monat_data = data[(data.index.year == year) & (data.index.month == month)]
    vmax = max(abs(monat_data.min()), abs(monat_data.max())) if not monat_data.empty else 1.0
    vmax = vmax or 1.0

    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    cmap = plt.cm.RdYlGn

    fig, ax = plt.subplots(figsize=(5, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    fig.suptitle(title, fontsize=9, color="white", fontweight="bold", y=0.98)

    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    first_weekday = calendar.monthrange(year, month)[0]
    num_days = calendar.monthrange(year, month)[1]

    for d, label in enumerate(day_labels):
        ax.text(d + 0.5, 6.6, label, ha="center", va="center",
                color="#aaaacc", fontsize=7, fontweight="bold")

    row, col = 0, first_weekday
    for day in range(1, num_days + 1):
        date  = pd.Timestamp(year=year, month=month, day=day)
        value = monat_data.get(date, np.nan)

        if pd.isna(value):
            color, text_color = "#2a2a4a", "#666688"
        else:
            rgba       = cmap(norm(value))
            color      = rgba
            brightness = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
            text_color = "black" if brightness > 0.5 else "white"

        rect = mpatches.FancyBboxPatch(
            (col+0.05, 5-row+0.05), 0.9, 0.85,
            boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="#1a1a2e", linewidth=1.0
        )
        ax.add_patch(rect)
        ax.text(col+0.5, 5-row+0.55, str(day),
                ha="center", va="center", color=text_color, fontsize=7, fontweight="bold")
        if not pd.isna(value):
            ax.text(col+0.5, 5-row+0.18, f"{value:+.1f}",
                    ha="center", va="center", color=text_color, fontsize=5)

        col += 1
        if col > 6:
            col, row = 0, row+1

    ax.set_xlim(0, 7)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    cbar_ax = fig.add_axes([0.1, 0.02, 0.8, 0.025])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(f"Bilanz ({unit})", color="white", fontsize=7)
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=6)

    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    return fig


def create_chart_balkendiagramm(df: pd.DataFrame):
    """
    Balkendiagramm: kumulierte Differenz Erzeugung − Verbrauch pro Stunde.
    Positiv → grün, Negativ → rot.
    """
    df = umrechnung_in_kwh(df)
    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour

    stunden_bilanz = df.groupby("stunde").apply(
        lambda g: g["kwh_erzeugt"].sum() - g["kwh_verbraucht"].sum()
    ).reindex(range(24), fill_value=0)

    farben = ["#2ecc71" if v >= 0 else "#e74c3c" for v in stunden_bilanz]

    fig, ax = plt.subplots(figsize=(7, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    balken = ax.bar(stunden_bilanz.index, stunden_bilanz.values,
                    color=farben, edgecolor="#1a1a2e", linewidth=0.6, width=0.7)
    ax.axhline(0, color="#aaaacc", linewidth=0.6, linestyle="--")

    for bar, val in zip(balken, stunden_bilanz.values):
        if val != 0:
            y_pos = val + (0.001 if val >= 0 else -0.001)
            ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                    f"{val:+.2f}", ha="center",
                    va="bottom" if val >= 0 else "top",
                    color="white", fontsize=5)

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)],
                       rotation=0, color="white", fontsize=6)
    ax.tick_params(axis="y", colors="white", labelsize=6)
    ax.set_xlabel("Uhrzeit", color="white", fontsize=8)
    ax.set_ylabel("Bilanz (kWh)", color="white", fontsize=8)
    ax.set_title("Kumulierte Differenz: Erzeugung − Verbrauch pro Stunde",
                 color="white", fontsize=9, fontweight="bold", pad=8)

    for spine in ax.spines.values():
        spine.set_edgecolor("#aaaacc")

    legende = [
        mpatches.Patch(color="#2ecc71", label="Überschuss"),
        mpatches.Patch(color="#e74c3c", label="Defizit"),
    ]
    ax.legend(handles=legende, facecolor="#16213e", edgecolor="#aaaacc",
              labelcolor="white", fontsize=7)

    plt.tight_layout()
    return fig


def create_chart_kurvendiagramm(df: pd.DataFrame):
    """
    Kurvendiagramm: täglicher Verlauf Erzeugung & Verbrauch mit Min/Max-Markierung.
    """
    df = umrechnung_in_kwh(df)
    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour

    stunden = df.groupby("stunde").agg(
        kwh_erzeugt   =("kwh_erzeugt",    "sum"),
        kwh_verbraucht=("kwh_verbraucht",  "sum"),
    ).reindex(range(24), fill_value=0)

    min_erz  = stunden["kwh_erzeugt"].min()
    max_erz  = stunden["kwh_erzeugt"].max()
    min_verb = stunden["kwh_verbraucht"].min()
    max_verb = stunden["kwh_verbraucht"].max()
    idx_min_erz  = stunden["kwh_erzeugt"].idxmin()
    idx_max_erz  = stunden["kwh_erzeugt"].idxmax()
    idx_min_verb = stunden["kwh_verbraucht"].idxmin()
    idx_max_verb = stunden["kwh_verbraucht"].idxmax()

    fig, ax = plt.subplots(figsize=(7, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    x = stunden.index

    ax.plot(x, stunden["kwh_erzeugt"],    color="#2ecc71", linewidth=1.5,
            marker="o", markersize=2.5, label="Erzeugung (kWh)")
    ax.plot(x, stunden["kwh_verbraucht"], color="#e74c3c", linewidth=1.5,
            marker="o", markersize=2.5, label="Verbrauch (kWh)")
    ax.fill_between(x, stunden["kwh_erzeugt"],    alpha=0.12, color="#2ecc71")
    ax.fill_between(x, stunden["kwh_verbraucht"], alpha=0.12, color="#e74c3c")

    for xy, label, color in [
        ((idx_min_erz,  min_erz),  f"Min {min_erz:.2f}",  "#2ecc71"),
        ((idx_max_erz,  max_erz),  f"Max {max_erz:.2f}",  "#2ecc71"),
        ((idx_min_verb, min_verb), f"Min {min_verb:.2f}", "#e74c3c"),
        ((idx_max_verb, max_verb), f"Max {max_verb:.2f}", "#e74c3c"),
    ]:
        ax.annotate(label, xy=xy,
                    xytext=(xy[0]+0.5, xy[1]+0.005),
                    color=color, fontsize=6,
                    arrowprops=dict(arrowstyle="->", color=color, lw=0.8))

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)],
                       rotation=0, color="white", fontsize=6)
    ax.tick_params(axis="y", colors="white", labelsize=6)
    ax.set_xlabel("Uhrzeit", color="white", fontsize=8)
    ax.set_ylabel("kWh", color="white", fontsize=8)
    ax.set_title("Täglicher Verlauf: Erzeugung & Verbrauch",
                 color="white", fontsize=9, fontweight="bold", pad=8)

    for spine in ax.spines.values():
        spine.set_edgecolor("#aaaacc")

    ax.legend(facecolor="#16213e", edgecolor="#aaaacc",
              labelcolor="white", fontsize=7)

    plt.tight_layout()
    return fig


def show_charts(df: pd.DataFrame, month: int) -> None:
    """Rendert alle Grafiken zusammen."""
    data = differenz_erzeugt_verbraucht(df)
    draw_calendar(data, YEAR, month, UNIT)
    create_chart_balkendiagramm(df)
    create_chart_kurvendiagramm(df)


def draw_calendar_3monate(data: pd.Series, unit: str):
    """
    Zeichnet die letzten 3 Monate nebeneinander als eine breite Kalender-Grafik.
    Aktueller Monat + die 2 vorherigen Monate.
    """
    heute = pd.Timestamp.now()
    monate = []
    for i in range(2, -1, -1):  # [vor 2, vor 1, aktuell]
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

    fig, axes = plt.subplots(1, 3, figsize=(16, 4), facecolor="#1a1a2e")
    fig.suptitle("Tägliche Bilanz – Letzte 3 Monate (Erzeugung − Verbrauch)",
                 fontsize=11, color="white", fontweight="bold", y=1.01)

    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    for ax, (year, month) in zip(axes, monate):
        ax.set_facecolor("#16213e")
        ax.set_title(f"{MONTH_NAMES_DE[month-1]} {year}",
                     color="white", fontsize=9, fontweight="bold", pad=6)

        monat_data = data[(data.index.year == year) & (data.index.month == month)]
        first_weekday = calendar.monthrange(year, month)[0]
        num_days = calendar.monthrange(year, month)[1]

        for d, label in enumerate(day_labels):
            ax.text(d + 0.5, 6.6, label, ha="center", va="center",
                    color="#aaaacc", fontsize=6, fontweight="bold")

        row, col = 0, first_weekday
        for day in range(1, num_days + 1):
            date  = pd.Timestamp(year=year, month=month, day=day)
            value = monat_data.get(date, np.nan)

            if pd.isna(value):
                color, text_color = "#2a2a4a", "#666688"
            else:
                rgba       = cmap(norm(value))
                color      = rgba
                brightness = 0.299*rgba[0] + 0.587*rgba[1] + 0.114*rgba[2]
                text_color = "black" if brightness > 0.5 else "white"

            rect = mpatches.FancyBboxPatch(
                (col+0.05, 5-row+0.05), 0.9, 0.85,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor="#1a1a2e", linewidth=0.8
            )
            ax.add_patch(rect)
            ax.text(col+0.5, 5-row+0.55, str(day),
                    ha="center", va="center", color=text_color, fontsize=6, fontweight="bold")
            if not pd.isna(value):
                ax.text(col+0.5, 5-row+0.18, f"{value:+.0f}",
                        ha="center", va="center", color=text_color, fontsize=4.5)

            col += 1
            if col > 6:
                col, row = 0, row+1

        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")

    # Gemeinsame Colorbar
    cbar_ax = fig.add_axes([0.15, -0.04, 0.7, 0.025])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(f"Bilanz ({unit})   ← Verbrauchsüberschuss  |  Erzeugungsüberschuss →",
                   color="white", fontsize=8)
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=7)

    plt.tight_layout()
    return fig
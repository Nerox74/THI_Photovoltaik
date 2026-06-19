"""
Hier werden die Charts erstellt, in welchen die Stromerzeugung der Photovoltaik visuallisert wird"

"""
from THI_Photovoltaik.src.components import formulas

# Imports, ebenso Formeln die gebraucht werden

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm
import calendar


def draw_calendar(data: pd.Series, year: int, title: str, unit: str):
    """
    Diese Kalendergrafik zeigt farblich gekennzeichnet die kumulierten Differenzen zwischen Verbrauch und Erzeugung pro Tag.
    Ein (negativer) Überschuss an Verbrauch wird in rot gekennzeichnet, ein (positiver) Überschuss wird in grün gekennzeichnet.
    """

    vmax = max(abs(data.min()), abs(data.max()))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    cmap = plt.cm.RdYlGn

    fig, axes = plt.subplots(3, 4, figsize=(20, 12), facecolor="#1a1a2e")
    fig.suptitle(title, fontsize=18, color="white", fontweight="bold", y=0.98)

    month_names_de = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    for month_idx, ax in enumerate(axes.flat):
        month = month_idx + 1
        ax.set_facecolor("#16213e")

        first_weekday = calendar.monthrange(year, month)[0]
        num_days = calendar.monthrange(year, month)[1]

        ax.set_title(month_names_de[month_idx], color="white", fontsize=12, fontweight="bold", pad=8)

        for d, label in enumerate(day_labels):
            ax.text(d + 0.5, 6.6, label, ha="center", va="center",
                    color="#aaaacc", fontsize=8, fontweight="bold")

        row = 0
        col = first_weekday

        for day in range(1, num_days + 1):
            date = pd.Timestamp(year=year, month=month, day=day)
            value = data.get(date, np.nan)

            if pd.isna(value):
                color = "#2a2a4a"
                text_color = "#666688"
            else:
                rgba = cmap(norm(value))
                color = rgba
                brightness = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                text_color = "black" if brightness > 0.5 else "white"

            rect = mpatches.FancyBboxPatch(
                (col + 0.05, 5 - row + 0.05), 0.9, 0.85,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor="#1a1a2e", linewidth=1.2
            )
            ax.add_patch(rect)

            ax.text(col + 0.5, 5 - row + 0.55, str(day),
                    ha="center", va="center", color=text_color, fontsize=8, fontweight="bold")

            if not pd.isna(value):
                ax.text(col + 0.5, 5 - row + 0.18, f"{value:+.1f}",
                        ha="center", va="center", color=text_color, fontsize=6)

            col += 1
            if col > 6:
                col = 0
                row += 1

        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")

    cbar_ax = fig.add_axes([0.25, 0.01, 0.5, 0.018])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(
        f"Bilanz ({unit})   ← Verbrauchsüberschuss  |  Erzeugungsüberschuss →",
        color="white", fontsize=10
    )
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=9)

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    plt.savefig("pv_calendar.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print("✅ Gespeichert als 'pv_calendar.png'")
    plt.show()


def create_chart_balkendiagramm() -> None:
    """
    Dieses Balkendiagramm zeigt die kumulierte Differenz der Erzeugung in kWh und des Verbrauchs in kWh pro Stunde.

    """


def create_chart_kurvendiagramm() -> None:
    """
    Dieses Kurvendiagramm zeigt zwei tägliche Verläufe der Erzeugung in kWh und des Verbrauchs in kWh.
    Genutzt werden genutzt um die minimalen und maximalen Werte zu ermitteln.
    """


def show_charts() -> None:
    """
    Diese Funktion rendert alle erstellten Grafiken und führt diese Zusammen.

    """

"""
Hier werden die Charts erstellt, in welchen die Stromerzeugung der Photovoltaik visuallisert wird"

"""
from components.formulas import umrechnung_in_kwh, differenz_erzeugt_verbraucht
# Imports, ebenso Formeln die gebraucht werden

import numpy as np
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm
import calendar
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
DATEI_PFAD = "cleaned_data.csv"  # ← CSV-Pfad hier eintragen
YEAR = 2026
TITLE = f"PV-Anlage {YEAR} – Tägliche Bilanz (Erzeugung − Verbrauch)"
UNIT = "kWh"


def draw_calendar(data: pd.Series, year: int, title: str, unit: str):
    """
    Zeichnet einen Jahreskalender als 12-Monats-Grid.
    Jede Zelle = ein Tag, farbig nach täglicher Bilanz (Erzeugung − Verbrauch).

    Positiv (+) → grün   (Überschuss)
    Negativ (−) → rot    (Defizit)
    Kein Wert   → dunkel (keine Messdaten)
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

        ax.set_title(month_names_de[month_idx], color="white", fontsize=12,
                     fontweight="bold", pad=8)

        # Wochentag-Header
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

            # Zelle
            rect = mpatches.FancyBboxPatch(
                (col + 0.05, 5 - row + 0.05), 0.9, 0.85,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor="#1a1a2e", linewidth=1.2
            )
            ax.add_patch(rect)

            # Tag-Zahl
            ax.text(col + 0.5, 5 - row + 0.55, str(day),
                    ha="center", va="center",
                    color=text_color, fontsize=8, fontweight="bold")

            # Bilanzwert
            if not pd.isna(value):
                ax.text(col + 0.5, 5 - row + 0.18, f"{value:+.1f}",
                        ha="center", va="center",
                        color=text_color, fontsize=6)

            col += 1
            if col > 6:
                col = 0
                row += 1

        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")

    # Colorbar
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
    plt.savefig("pv_calendar.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print("✅ Gespeichert als 'pv_calendar.png'")
    return fig


def create_chart_balkendiagramm(df: pd.DataFrame) -> None:
    """
    Dieses Balkendiagramm zeigt die kumulierte Differenz der Erzeugung in kWh
    und des Verbrauchs in kWh pro Stunde.

    Positiv (+) → grün  (mehr erzeugt als verbraucht)
    Negativ (−) → rot   (mehr verbraucht als erzeugt)

    Eingabe (df): roher DataFrame aus der CSV mit Spalten:
        collected_at       → Zeitstempel
        pv_erzeugung_kw    → erzeugte Leistung in kW
        netz_wert_kw       → verbrauchte Leistung in kW
    """
    df = umrechnung_in_kwh(df)

    # Stunde extrahieren
    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour

    # Pro Stunde summieren
    stunden_bilanz = df.groupby("stunde").apply(
        lambda g: g["kwh_erzeugt"].sum() - g["kwh_verbraucht"].sum()
    )

    # Alle 24 Stunden sicherstellen (fehlende = 0)
    stunden_bilanz = stunden_bilanz.reindex(range(24), fill_value=0)

    # Farben: grün = Überschuss, rot = Defizit
    farben = ["#2ecc71" if v >= 0 else "#e74c3c" for v in stunden_bilanz]

    # ── Plot ──
    fig, ax = plt.subplots(figsize=(14, 6), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    balken = ax.bar(stunden_bilanz.index, stunden_bilanz.values,
                    color=farben, edgecolor="#1a1a2e", linewidth=0.8, width=0.7)

    # Nulllinie
    ax.axhline(0, color="#aaaacc", linewidth=0.8, linestyle="--")

    # Werte über/unter den Balken
    for bar, val in zip(balken, stunden_bilanz.values):
        if val != 0:
            y_pos = val + (0.002 if val >= 0 else -0.002)
            va = "bottom" if val >= 0 else "top"
            ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                    f"{val:+.3f}", ha="center", va=va,
                    color="white", fontsize=7)

    # Achsen & Labels
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)],
                       rotation=45, color="white", fontsize=8)
    ax.tick_params(axis="y", colors="white")
    ax.set_xlabel("Uhrzeit", color="white", fontsize=11)
    ax.set_ylabel("Bilanz (kWh)", color="white", fontsize=11)
    ax.set_title("Kumulierte Differenz: Erzeugung − Verbrauch pro Stunde",
                 color="white", fontsize=14, fontweight="bold", pad=12)

    for spine in ax.spines.values():
        spine.set_edgecolor("#aaaacc")

    # Legende
    legende = [
        mpatches.Patch(color="#2ecc71", label="Überschuss (Erzeugung > Verbrauch)"),
        mpatches.Patch(color="#e74c3c", label="Defizit (Verbrauch > Erzeugung)"),
    ]
    ax.legend(handles=legende, facecolor="#16213e", edgecolor="#aaaacc",
              labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig("pv_balkendiagramm.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print("✅ Gespeichert als 'pv_balkendiagramm.png'")
    plt.show()


def create_chart_kurvendiagramm(df: pd.DataFrame) -> None:
    """
    Dieses Kurvendiagramm zeigt zwei tägliche Verläufe der Erzeugung in kWh
    und des Verbrauchs in kWh.
    Genutzt werden genutzt um die minimalen und maximalen Werte zu ermitteln.

    Eingabe (df): roher DataFrame aus der CSV mit Spalten:
        collected_at       → Zeitstempel
        pv_erzeugung_kw    → erzeugte Leistung in kW
        netz_wert_kw       → verbrauchte Leistung in kW
    """
    df = umrechnung_in_kwh(df)

    # Stunde extrahieren & pro Stunde summieren
    df["stunde"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.hour

    stunden = df.groupby("stunde").agg(
        kwh_erzeugt=("kwh_erzeugt", "sum"),
        kwh_verbraucht=("kwh_verbraucht", "sum"),
    ).reindex(range(24), fill_value=0)

    # Min / Max ermitteln
    min_erzeugt = stunden["kwh_erzeugt"].min()
    max_erzeugt = stunden["kwh_erzeugt"].max()
    min_verbraucht = stunden["kwh_verbraucht"].min()
    max_verbraucht = stunden["kwh_verbraucht"].max()

    stunde_min_erzeugt = stunden["kwh_erzeugt"].idxmin()
    stunde_max_erzeugt = stunden["kwh_erzeugt"].idxmax()
    stunde_min_verbraucht = stunden["kwh_verbraucht"].idxmin()
    stunde_max_verbraucht = stunden["kwh_verbraucht"].idxmax()

    # ── Plot ──
    fig, ax = plt.subplots(figsize=(14, 6), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    x = stunden.index

    # Kurven
    ax.plot(x, stunden["kwh_erzeugt"], color="#2ecc71", linewidth=2,
            marker="o", markersize=4, label="Erzeugung (kWh)")
    ax.plot(x, stunden["kwh_verbraucht"], color="#e74c3c", linewidth=2,
            marker="o", markersize=4, label="Verbrauch (kWh)")

    # Fläche unter den Kurven
    ax.fill_between(x, stunden["kwh_erzeugt"], alpha=0.15, color="#2ecc71")
    ax.fill_between(x, stunden["kwh_verbraucht"], alpha=0.15, color="#e74c3c")

    # Min-Punkte markieren
    ax.annotate(f"Min {min_erzeugt:.3f} kWh",
                xy=(stunde_min_erzeugt, min_erzeugt),
                xytext=(stunde_min_erzeugt + 0.5, min_erzeugt + 0.01),
                color="#2ecc71", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#2ecc71"))

    ax.annotate(f"Min {min_verbraucht:.3f} kWh",
                xy=(stunde_min_verbraucht, min_verbraucht),
                xytext=(stunde_min_verbraucht + 0.5, min_verbraucht + 0.01),
                color="#e74c3c", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#e74c3c"))

    # Max-Punkte markieren
    ax.annotate(f"Max {max_erzeugt:.3f} kWh",
                xy=(stunde_max_erzeugt, max_erzeugt),
                xytext=(stunde_max_erzeugt + 0.5, max_erzeugt - 0.01),
                color="#2ecc71", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#2ecc71"))

    ax.annotate(f"Max {max_verbraucht:.3f} kWh",
                xy=(stunde_max_verbraucht, max_verbraucht),
                xytext=(stunde_max_verbraucht + 0.5, max_verbraucht - 0.01),
                color="#e74c3c", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#e74c3c"))

    # Achsen & Labels
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)],
                       rotation=45, color="white", fontsize=8)
    ax.tick_params(axis="y", colors="white")
    ax.set_xlabel("Uhrzeit", color="white", fontsize=11)
    ax.set_ylabel("kWh", color="white", fontsize=11)
    ax.set_title("Täglicher Verlauf: Erzeugung & Verbrauch pro Stunde",
                 color="white", fontsize=14, fontweight="bold", pad=12)

    for spine in ax.spines.values():
        spine.set_edgecolor("#aaaacc")

    ax.legend(facecolor="#16213e", edgecolor="#aaaacc",
              labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig("pv_kurvendiagramm.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print("✅ Gespeichert als 'pv_kurvendiagramm.png'")
    plt.show()


def show_charts(df: pd.DataFrame) -> None:
    """
    Diese Funktion rendert alle erstellten Grafiken und führt diese zusammen.
    """
    data = differenz_erzeugt_verbraucht(df)

    draw_calendar(data, YEAR, TITLE, UNIT)
    create_chart_balkendiagramm(df)
    create_chart_kurvendiagramm(df)
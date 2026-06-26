"""Zentrale Zahlen und Fakten, die im Streamlit-Dashboard angezeigt werden."""

from __future__ import annotations

import logging
import math

import pandas as pd
import streamlit as st

import config
from components import formulas

logger = logging.getLogger(__name__)


def _summe_kwh(df: pd.DataFrame, spalte: str, zeitraum: str) -> float:
    """Summiert eine kWh-Spalte für den angegebenen Zeitraum.

    'Tag' verwendet die Berliner Mitternacht als Grenze (nicht UTC-Mitternacht),
    damit im Sommer (UTC+2) auch Produktion zwischen 00:00 und 02:00 Berliner
    Zeit korrekt dem heutigen Tag zugeordnet wird.
    """
    jetzt = pd.Timestamp.now(tz="UTC")
    jetzt_berlin = jetzt.tz_convert("Europe/Berlin")

    grenzen = {
        "Tag": jetzt_berlin.normalize().tz_convert("UTC"),  # Mitternacht Berlin → UTC
        "Woche": jetzt - pd.Timedelta(days=7),
        "Monat": jetzt - pd.Timedelta(days=30),
        "Jahr": jetzt - pd.Timedelta(days=365),
    }
    maske = df["collected_at"] >= grenzen[zeitraum]
    return float(df.loc[maske, spalte].sum())


_KPI_CARD_HEIGHT = "130px"  # Einheitliche Mindesthöhe für alle KPI-Kacheln


def _kpi_card(
    icon: str, titel: str, wert: str, untertitel: str, wert_farbe: str = "white"
) -> str:
    """Rendert eine einzelne KPI-Kachel als HTML-String."""
    return (
        f'<div style="'
        f"background:{config.KPI_BG};"
        f"border-radius:{config.KPI_RADIUS};"
        f"border:1px solid rgba(255,255,255,0.07);"
        f"padding:16px 18px;"
        f"min-height:{_KPI_CARD_HEIGHT};"
        f"box-sizing:border-box;"
        f'">'
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:8px;">'
        f"{icon} {titel}"
        f"</div>"
        f'<div style="font-size:26px;font-weight:500;color:{wert_farbe};line-height:1.1;">'
        f"{wert}"
        f"</div>"
        f'<div style="font-size:11px;color:{config.TEXT_SCHWACH};margin-top:6px;">'
        f"{untertitel}"
        f"</div>"
        f"</div>"
    )


def _auslastung_bar(auslastung: float, text: str) -> str:
    """Rendert die Auslastungskachel mit einer farbcodierten Progressbar."""
    if auslastung >= 60:
        bar_farbe = config.FARBE_UEBERSCHUSS  # grün
    elif auslastung >= 25:
        bar_farbe = "#f39c12"  # orange
    else:
        bar_farbe = config.FARBE_DEFIZIT  # rot

    return (
        f'<div style="'
        f"background:{config.KPI_BG};"
        f"border-radius:{config.KPI_RADIUS};"
        f"border:1px solid rgba(255,255,255,0.07);"
        f"padding:16px 18px;"
        f"min-height:{_KPI_CARD_HEIGHT};"
        f"box-sizing:border-box;"
        f'">'
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:8px;">'
        f"📊 Auslastung heute"
        f"</div>"
        f'<div style="font-size:26px;font-weight:500;color:white;line-height:1.1;">'
        f"{text}"
        f"</div>"
        f'<div style="'
        f"height:6px;background:rgba(255,255,255,0.1);"
        f"border-radius:3px;margin-top:14px;"
        f'">'
        f'<div style="'
        f"height:6px;width:{auslastung:.1f}%;"
        f"background:{bar_farbe};"
        f"border-radius:3px;"
        f"transition:width 0.4s ease;"
        f'"></div>'
        f"</div>"
        f'<div style="font-size:10px;color:{config.TEXT_SCHWACH};margin-top:5px;">'
        f"von {config.MAX_TAGESERZEUGUNG_KWH:.0f} kWh Referenz"
        f"</div>"
        f"</div>"
    )


def _mini_stat(icon: str, label: str, wert: str, farbe: str = "white") -> str:
    """Kleine Stat-Box für die rechte Seite der Amortisierungs-Kachel."""
    return (
        f'<div style="'
        f"background:rgba(255,255,255,0.04);"
        f"border-radius:8px;"
        f"padding:12px 14px;"
        f"flex:1;min-width:130px;"
        f'">'
        f'<div style="font-size:10px;color:{config.TEXT_GEDIMMT};margin-bottom:5px;">'
        f"{icon} {label}"
        f"</div>"
        f'<div style="font-size:20px;font-weight:600;color:{farbe};line-height:1.15;">'
        f"{wert}"
        f"</div>"
        f"</div>"
    )


def _show_amortisierung(
    amortisierung: float,
    eingespart: float,
    kwh_gesamt: float = 0.0,
    kwh_woche: float = 0.0,
) -> None:
    """Zeigt die Amortisierungs-Kachel mit SVG-Halbkreis-Gauge, CO₂-Einsparung
    und Amortisierungsprognose.

    Der Gauge nutzt viewBox="0 0 200 115", Mittelpunkt (100, 105), Radius 80.
    Sehne = 2 × 80 = 160 px → Start (20, 105), Ende (180, 105).
    Bogenlänge (Halbkreis) = π × 80 ≈ 251.33 px.
    """
    radius = 80
    cx, cy = 100, 105
    x_start = cx - radius  # 20
    x_end = cx + radius  # 180
    umfang = math.pi * radius  # ≈ 251.33
    pct = min(max(amortisierung, 0.0), 100.0)
    offset = umfang * (1.0 - pct / 100.0)

    if amortisierung >= 75:
        bogen_farbe = config.FARBE_UEBERSCHUSS
    elif amortisierung >= 40:
        bogen_farbe = "#f39c12"
    else:
        bogen_farbe = config.THI_BLAU

    if pct < 1:
        sub_label = "gerade gestartet"
    elif pct < 50:
        sub_label = "auf dem Weg"
    else:
        sub_label = "mehr als die Hälfte"

    arc_path = f"M {x_start} {cy} A {radius} {radius} 0 0 1 {x_end} {cy}"

    # ── CO₂-Einsparung ───────────────────────────────────────────────────────
    co2_kg = kwh_gesamt * config.CO2_FAKTOR_KG_PRO_KWH
    if co2_kg >= 1000:
        co2_str = f"{co2_kg / 1000:.2f} t"
    else:
        co2_str = f"{co2_kg:.1f} kg"

    # ── Amortisierungsprognose ────────────────────────────────────────────────
    verbleibend_eur = config.ANSCHAFFUNGSKOSTEN_PV_ANLAGE * (1.0 - pct / 100.0)
    woechentlich = kwh_woche * config.STROMPREIS  # € pro Woche
    if woechentlich > 0 and pct < 100:
        wochen_noch = verbleibend_eur / woechentlich
        jahre_noch = wochen_noch / 52.18
        if jahre_noch < 1:
            monate_noch = math.ceil(wochen_noch / 4.33)
            prognose_str = f"~{monate_noch} Mon."
        else:
            prognose_str = f"~{jahre_noch:.1f} Jahre"
    elif pct >= 100:
        prognose_str = "✓ amortisiert"
    else:
        prognose_str = "keine Daten"

    st.markdown(
        f'<div style="'
        f"background:{config.KPI_BG};"
        f"border-radius:{config.KPI_RADIUS};"
        f"border:1px solid rgba(255,255,255,0.07);"
        f"padding:18px 24px;"
        f"margin-top:12px;"
        f'">'
        # Titelzeile
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:14px;">'
        f"📈 Amortisierung der PV-Anlage"
        f"</div>"
        # Hauptzeile: Gauge | Geld-Stats | Zusatz-Stats
        f'<div style="display:flex;align-items:center;gap:32px;flex-wrap:wrap;">'
        # ── SVG-Gauge ─────────────────────────────────────────────────────────
        f'<svg viewBox="0 0 200 115" width="210" style="flex-shrink:0;">'
        f'<path d="{arc_path}" fill="none"'
        f' stroke="rgba(255,255,255,0.08)" stroke-width="14" stroke-linecap="round"/>'
        f'<path d="{arc_path}" fill="none"'
        f' stroke="{bogen_farbe}" stroke-width="14" stroke-linecap="round"'
        f' stroke-dasharray="{umfang:.4f}" stroke-dashoffset="{offset:.4f}"/>'
        f'<circle cx="{x_start}" cy="{cy}" r="5" fill="rgba(255,255,255,0.15)"/>'
        f'<text x="{cx}" y="{cy - 16}" text-anchor="middle"'
        f' font-size="28" font-weight="700" fill="white">{pct:.1f}%</text>'
        f'<text x="{cx}" y="{cy - 1}" text-anchor="middle"'
        f' font-size="9" fill="{config.TEXT_GEDIMMT}">{sub_label}</text>'
        f'<text x="{x_start - 2}" y="{cy + 14}" text-anchor="middle"'
        f' font-size="8" fill="{config.TEXT_SCHWACH}">0%</text>'
        f'<text x="{x_end + 2}" y="{cy + 14}" text-anchor="middle"'
        f' font-size="8" fill="{config.TEXT_SCHWACH}">100%</text>'
        f"</svg>"
        # ── Geld-Stats ────────────────────────────────────────────────────────
        f'<div style="flex-shrink:0;">'
        f'<div style="font-size:12px;color:{config.TEXT_GEDIMMT};margin-bottom:4px;">'
        f"Bereits eingespart"
        f"</div>"
        f'<div style="font-size:28px;font-weight:600;color:{bogen_farbe};line-height:1.1;">'
        f"{eingespart:,.0f} €"
        f"</div>"
        f'<div style="height:1px;background:rgba(255,255,255,0.07);margin:10px 0;"></div>'
        f'<div style="font-size:11px;color:{config.TEXT_SCHWACH};">'
        f"Anschaffung: {config.ANSCHAFFUNGSKOSTEN_PV_ANLAGE:,.0f} €"
        f"</div>"
        f'<div style="font-size:11px;color:{config.TEXT_SCHWACH};margin-top:3px;">'
        f"Strompreis: {config.STROMPREIS:.2f} €/kWh"
        f"</div>"
        f"</div>"
        # ── Zusatz-Stats (CO₂ + Prognose) ────────────────────────────────────
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;flex:1;">'
        + _mini_stat("🌿", "CO₂ eingespart", co2_str, config.FARBE_UEBERSCHUSS)
        + _mini_stat("⏳", "Noch bis Amortisierung", prognose_str, "#f39c12")
        + "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def show_kpis(df: pd.DataFrame, kwh_gesamt_alltime: float | None = None) -> None:
    """Zeigt 4 KPI-Kacheln (Heute, Woche, Ersparnis, Auslastung) + Amortisierung.

    Args:
        df: Rohdaten-DataFrame (Rohwerte aus der Datenbank).
        kwh_gesamt_alltime: Gesamte kWh über die komplette Historie
                            (aus DataStorage.gesamt_kwh_erzeugt).
                            Falls None, Fallback auf lokale Rohdaten.
    """
    df_kwh = formulas.umrechnung_in_kwh(df)

    # Hat der heutige Tag bereits Messdaten?
    maske_heute = df_kwh["collected_at"] >= (
        pd.Timestamp.now(tz="UTC")
        .tz_convert("Europe/Berlin")
        .normalize()
        .tz_convert("UTC")
    )
    hat_daten_heute = bool(maske_heute.any())

    kwh_heute = _summe_kwh(df_kwh, "kwh_erzeugt", "Tag")
    kwh_woche = _summe_kwh(df_kwh, "kwh_erzeugt", "Woche")
    auslastung = min(100.0, kwh_heute / config.MAX_TAGESERZEUGUNG_KWH * 100)

    kwh_gesamt = (
        kwh_gesamt_alltime
        if kwh_gesamt_alltime is not None
        else float(df_kwh["kwh_erzeugt"].sum())
    )

    eingespart = kwh_gesamt * config.STROMPREIS
    amortisierung = min(100.0, eingespart / config.ANSCHAFFUNGSKOSTEN_PV_ANLAGE * 100)
    ersparnis_tag = kwh_heute * config.STROMPREIS

    # Anzeige-Strings: "—" wenn noch keine Tagesdaten vorliegen
    if hat_daten_heute:
        txt_heute = f"{kwh_heute:.1f} kWh"
        txt_heute_sub = "Stand jetzt"
        txt_ersparnis = f"{ersparnis_tag:.2f} €"
        txt_ersp_sub = f"{kwh_heute:.1f} kWh × {config.STROMPREIS:.2f} €/kWh"
        txt_auslastung = f"{auslastung:.1f} %"
        bar_auslastung = auslastung
        erz_farbe = config.FARBE_UEBERSCHUSS if kwh_heute > 0 else "white"
    else:
        txt_heute = "—"
        txt_heute_sub = "noch keine Daten heute"
        txt_ersparnis = "—"
        txt_ersp_sub = "noch keine Daten heute"
        txt_auslastung = "—"
        bar_auslastung = 0.0
        erz_farbe = "white"

    logger.debug(
        "KPIs: heute=%.2f kWh | woche=%.2f kWh | ersparnis=%.2f € "
        "| auslastung=%.1f %% | amortisierung=%.1f %%",
        kwh_heute,
        kwh_woche,
        ersparnis_tag,
        auslastung,
        amortisierung,
    )

    # ── 4 KPI-Kacheln ────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            _kpi_card("⚡", "Heute erzeugt", txt_heute, txt_heute_sub, erz_farbe),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            _kpi_card(
                "📅",
                "Diese Woche",
                f"{kwh_woche:.1f} kWh",
                "letzte 7 Tage",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            _kpi_card(
                "💰",
                "Ersparnis heute",
                txt_ersparnis,
                txt_ersp_sub,
                (
                    config.FARBE_UEBERSCHUSS
                    if hat_daten_heute and ersparnis_tag > 0
                    else "white"
                ),
            ),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            _auslastung_bar(bar_auslastung, txt_auslastung),
            unsafe_allow_html=True,
        )

    # ── Amortisierungs-Gauge (volle Breite) ──────────────────────────────────
    _show_amortisierung(amortisierung, eingespart, kwh_gesamt, kwh_woche)

"""Zentrale Zahlen und Fakten, die im Streamlit-Dashboard angezeigt werden."""

from __future__ import annotations

import logging
import math

import pandas as pd
import streamlit as st

import config
from components import charts, formulas

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

    co2_kg = kwh_gesamt * config.CO2_FAKTOR_KG_PRO_KWH
    if co2_kg >= 1000:
        co2_str = f"{co2_kg / 1000:.2f} t"
    else:
        co2_str = f"{co2_kg:.1f} kg"

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
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:14px;">'
        f"📈 Amortisierung der PV-Anlage"
        f"</div>"
        f'<div style="display:flex;align-items:center;gap:32px;flex-wrap:wrap;">'
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
    df_kwh, _ = formulas.umrechnung_in_kwh(df)

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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            _kpi_card("⚡", "Heute erzeugt", txt_heute, txt_heute_sub, erz_farbe),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _kpi_card("📅", "Diese Woche", f"{kwh_woche:.1f} kWh", "letzte 7 Tage"),
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

    _show_amortisierung(amortisierung, eingespart, kwh_gesamt, kwh_woche)


# ═════════════════════════════════════════════════════════════════════════════
# NEU: geforderte Pflicht-Metriken (Momentanwerte + Tag/Monat/Jahr)
# ═════════════════════════════════════════════════════════════════════════════

_PULSE_CSS = """
<style>
@keyframes pv-pulse {
  0%   { transform: scale(0.9); opacity: 1; }
  70%  { transform: scale(1.7); opacity: 0; }
  100% { transform: scale(0.9); opacity: 0; }
}
.pv-live-dot { position:relative; display:inline-block; width:9px; height:9px;
  border-radius:50%; background:#2ecc71; margin-right:7px; }
.pv-live-dot::after { content:''; position:absolute; left:0; top:0; width:9px;
  height:9px; border-radius:50%; background:#2ecc71; animation:pv-pulse 1.8s infinite; }
.pv-stale-dot { display:inline-block; width:9px; height:9px;
  border-radius:50%; background:#666688; margin-right:7px; }
</style>
"""


def _momentan_block(icon: str, label: str, wert: str, farbe: str) -> str:
    return (
        f'<div style="flex:1;min-width:150px;text-align:center;">'
        f'<div style="font-size:12px;color:{config.TEXT_GEDIMMT};margin-bottom:6px;">{icon} {label}</div>'
        f'<div style="font-size:34px;font-weight:600;color:{farbe};line-height:1;">{wert}</div>'
        f"</div>"
    )


def show_momentan(df: pd.DataFrame) -> None:
    """Live-Strip: Momentanerzeugung, -verbrauch und aktuelle Netto-Leistung.

    Zeigt "LIVE" nur, solange der letzte Messwert nicht älter als
    config.DATENFRISCHE_SEKUNDEN ist. Danach wird auf "KEINE AKTUELLEN DATEN"
    umgeschaltet, statt den alten Wert unkommentiert als aktuell auszugeben
    (siehe formulas.daten_frische).
    """
    df = df.copy()
    df["collected_at"] = pd.to_datetime(df["collected_at"], format="ISO8601", utc=True)
    letzte = df.sort_values("collected_at").iloc[-1]

    mom_erz = float(letzte["pv_erzeugung_kw"])
    mom_verb = float(letzte["netz_wert_kw"])
    netto = mom_erz - mom_verb
    letzter_ts = letzte["collected_at"]
    stand = letzter_ts.tz_convert("Europe/Berlin").strftime("%H:%M")

    frische = formulas.daten_frische(letzter_ts)

    if netto >= 0:
        netto_label, netto_farbe, netto_wert = (
            "Einspeisung",
            config.FARBE_UEBERSCHUSS,
            f"{netto:.2f} kW",
        )
    else:
        netto_label, netto_farbe, netto_wert = (
            "Netzbezug",
            config.FARBE_DEFIZIT,
            f"{abs(netto):.2f} kW",
        )

    logger.debug(
        "Momentan: Erzeugung=%.2f kW | Verbrauch=%.2f kW | Netto=%.2f kW | frisch=%s (%s)",
        mom_erz,
        mom_verb,
        netto,
        frische["ist_frisch"],
        frische["alter_text"],
    )

    if frische["ist_frisch"]:
        status_dot = '<span class="pv-live-dot"></span>'
        status_text = "LIVE"
        status_farbe = config.THI_HELLBLAU
        stand_zeile = f"Stand {stand} Uhr"
        werte_farbe_erz, werte_farbe_verb = config.FARBE_UEBERSCHUSS, config.FARBE_DEFIZIT
    else:
        status_dot = '<span class="pv-stale-dot"></span>'
        status_text = "KEINE AKTUELLEN DATEN"
        status_farbe = config.TEXT_SCHWACH
        stand_zeile = f"Letzter Wert {stand} Uhr ({frische['alter_text']})"
        werte_farbe_erz = werte_farbe_verb = config.TEXT_SCHWACH
        netto_farbe = config.TEXT_SCHWACH

    st.markdown(_PULSE_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{config.PANEL_BG} 0%,{config.KPI_BG} 100%);'
        f"border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:18px 26px;"
        f'display:flex;align-items:center;gap:24px;flex-wrap:wrap;">'
        f'<div style="flex-shrink:0;">'
        f'<div style="font-size:12px;color:{status_farbe};font-weight:600;letter-spacing:0.5px;">'
        f"{status_dot}{status_text}</div>"
        f'<div style="font-size:11px;color:{config.TEXT_SCHWACH};margin-top:4px;">{stand_zeile}</div>'
        f"</div>"
        f'<div style="width:1px;height:46px;background:rgba(255,255,255,0.1);"></div>'
        + _momentan_block("⚡", "Momentanerzeugung", f"{mom_erz:.2f} kW", werte_farbe_erz)
        + _momentan_block(
            "🏠", "Momentanverbrauch", f"{mom_verb:.2f} kW", werte_farbe_verb
        )
        + _momentan_block("🔁", netto_label, netto_wert, netto_farbe)
        + "</div>",
        unsafe_allow_html=True,
    )


def _bilanz_spalte(titel: str, s: dict) -> str:
    """Eine Spalte der Energiebilanz: Erzeugung & Verbrauch mit Vergleichsbalken."""
    erz, verb = s["erzeugt"], s["verbraucht"]
    bezug = max(erz, verb) or 1.0
    erz_breite = min(100.0, erz / bezug * 100.0)
    verb_breite = min(100.0, verb / bezug * 100.0)

    return (
        f'<div style="flex:1;min-width:210px;background:rgba(255,255,255,0.03);'
        f'border-radius:10px;padding:16px 18px;">'
        f'<div style="font-size:13px;color:white;font-weight:600;margin-bottom:14px;">{titel}</div>'
        # Erzeugung
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:3px;">☀️ Erzeugung</div>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
        f'<div style="flex:1;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;">'
        f'<div style="height:8px;width:{erz_breite:.1f}%;background:{config.FARBE_UEBERSCHUSS};border-radius:4px;"></div>'
        f"</div>"
        f'<div style="font-size:14px;font-weight:600;color:{config.FARBE_UEBERSCHUSS};min-width:80px;text-align:right;">{erz:.1f} kWh</div>'
        f"</div>"
        # Verbrauch
        f'<div style="font-size:11px;color:{config.TEXT_GEDIMMT};margin-bottom:3px;">🔌 Verbrauch</div>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
        f'<div style="flex:1;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;">'
        f'<div style="height:8px;width:{verb_breite:.1f}%;background:{config.FARBE_DEFIZIT};border-radius:4px;"></div>'
        f"</div>"
        f'<div style="font-size:14px;font-weight:600;color:{config.FARBE_DEFIZIT};min-width:80px;text-align:right;">{verb:.1f} kWh</div>'
        f"</div>"
        # PV-Quote
        f'<div style="font-size:11px;color:{config.TEXT_SCHWACH};border-top:1px solid rgba(255,255,255,0.06);padding-top:10px;">'
        f'🌱 {s["quote"]:.0f}% des Verbrauchs aus PV gedeckt</div>'
        f"</div>"
    )


def show_energiebilanz(df: pd.DataFrame, db) -> None:
    """Erzeugung & Verbrauch für Tag / Monat / Jahr im direkten Vergleich (mit PV-Quote).

    Tag & Monat aus den Live-Rohdaten (innerhalb der Retention, sekundengenau);
    Jahr aus der dauerhaften Tagesbilanz, damit es das 90-Tage-Pruning überlebt.
    """
    df_kwh, _ = formulas.umrechnung_in_kwh(df)
    tag = formulas.summen_zeitraum(df_kwh, "Tag")
    monat = formulas.summen_zeitraum(df_kwh, "Monat")
    jahr_start = pd.Timestamp.now(tz=config.ZEITZONE).strftime("%Y-01-01")
    jahr = db.summen_seit(jahr_start)

    logger.debug(
        "Energiebilanz: Tag=%.1f/%.1f | Monat=%.1f/%.1f | Jahr=%.1f/%.1f kWh (Erz/Verb)",
        tag["erzeugt"],
        tag["verbraucht"],
        monat["erzeugt"],
        monat["verbraucht"],
        jahr["erzeugt"],
        jahr["verbraucht"],
    )

    st.markdown(
        f'<div style="background:{config.KPI_BG};border:1px solid rgba(255,255,255,0.07);'
        f'border-radius:{config.KPI_RADIUS};padding:18px 22px;">'
        f'<div style="font-size:13px;color:{config.TEXT_GEDIMMT};margin-bottom:16px;">'
        f"📊 Energiebilanz – Erzeugung &amp; Verbrauch</div>"
        f'<div style="display:flex;gap:14px;flex-wrap:wrap;">'
        + _bilanz_spalte("Heute", tag)
        + _bilanz_spalte("Dieser Monat", monat)
        + _bilanz_spalte("Dieses Jahr", jahr)
        + "</div></div>",
        unsafe_allow_html=True,
    )
    # ── Tortendiagramme: PV-Quote (Eigenverbrauch vs. Netzbezug) je Zeitraum ──
    st.markdown(
        f'<div style="font-size:13px;color:{config.TEXT_GEDIMMT};'
        f'margin:18px 0 4px 0;">📊 PV-Quote – Anteil Eigenverbrauch am Verbrauch</div>',
        unsafe_allow_html=True,
    )
    spalten = st.columns(3)
    for spalte, (titel, summen) in zip(
        spalten, [("Heute", tag), ("Dieser Monat", monat), ("Dieses Jahr", jahr)]
    ):
        with spalte:
            st.pyplot(charts.create_pie_pv_quote(summen, titel))

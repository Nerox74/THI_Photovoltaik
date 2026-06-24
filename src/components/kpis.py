"""Zentrale Zahlen und Fakten, die im Streamlit-Dashboard angezeigt werden."""

import logging
import math

import pandas as pd
import streamlit as st

from THI_Photovoltaik import config
from components import formulas

logger = logging.getLogger(__name__)


def _summe_kwh(df: pd.DataFrame, spalte: str, zeitraum: str) -> float:
    jetzt = pd.Timestamp.now(tz="UTC")
    grenzen = {
        "Tag":   jetzt.normalize(),
        "Woche": jetzt - pd.Timedelta(days=7),
        "Monat": jetzt - pd.Timedelta(days=30),
        "Jahr":  jetzt - pd.Timedelta(days=365),
    }
    maske = df["collected_at"] >= grenzen[zeitraum]
    return float(df.loc[maske, spalte].sum())


def _show_amortisierung(amortisierung: float) -> None:
    umfang = math.pi * 55
    offset = umfang * (1 - min(amortisierung, 100) / 100)
    st.markdown(
        f'<div style="background:{config.KPI_BG}; border-radius:{config.KPI_RADIUS}; padding:14px 18px; margin-top:10px;">'
        f'<div style="font-size:11px; color:{config.TEXT_GEDIMMT}; margin-bottom:6px;">📈 Amortisierung der PV-Anlage</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<svg viewBox="0 0 160 80" width="100%" style="display:block; margin:6px auto 0; max-width:400px;">'
        '<path d="M 15 72 A 55 55 0 0 1 145 72" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="10" stroke-linecap="round"/>'
        f'<path d="M 15 72 A 55 55 0 0 1 145 72" fill="none" stroke="{config.THI_BLAU}" stroke-width="10" stroke-linecap="round" stroke-dasharray="{umfang:.2f}" stroke-dashoffset="{offset:.2f}"/>'
        f'<text x="80" y="66" text-anchor="middle" font-size="20" font-weight="500" fill="white">{amortisierung:.1f}%</text>'
        f'<text x="80" y="78" text-anchor="middle" font-size="9" fill="{config.TEXT_GEDIMMT}">von 100%</text>'
        '</svg>'
        '</div>',
        unsafe_allow_html=True,
    )


def show_kpis(df: pd.DataFrame) -> None:
    df_kwh = formulas.umrechnung_in_kwh(df)

    # Gibt es überhaupt eine Messung von heute? (Sonst zeigen wir "—" statt 0)
    maske_heute = df_kwh["collected_at"] >= pd.Timestamp.now(tz="UTC").normalize()
    hat_daten_heute = bool(maske_heute.any())

    kwh_heute     = _summe_kwh(df_kwh, "kwh_erzeugt", "Tag")
    kwh_woche     = _summe_kwh(df_kwh, "kwh_erzeugt", "Woche")
    auslastung    = min(100.0, kwh_heute / config.MAX_TAGESERZEUGUNG_KWH * 100)
    kwh_gesamt    = float(df_kwh["kwh_erzeugt"].sum())
    eingespart    = kwh_gesamt * config.STROMPREIS
    amortisierung = min(100.0, eingespart / config.ANSCHAFFUNGSKOSTEN_PV_ANLAGE * 100)
    ersparnis_tag = kwh_heute * config.STROMPREIS

    # Anzeige-Strings: bei fehlenden Tagesdaten "—" statt irreführender Null
    if hat_daten_heute:
        txt_heute      = f"{kwh_heute:.1f} kWh"
        txt_heute_sub  = "Stand jetzt"
        txt_ersparnis  = f"{ersparnis_tag:.2f} €"
        txt_ersp_sub   = f"{kwh_heute:.1f} kWh × {config.STROMPREIS} €"
        txt_auslastung = f"{auslastung:.1f} %"
        breite_auslast = auslastung
    else:
        txt_heute      = "—"
        txt_heute_sub  = "keine Daten heute"
        txt_ersparnis  = "—"
        txt_ersp_sub   = "keine Daten heute"
        txt_auslastung = "—"
        breite_auslast = 0.0

    logger.debug(
        "KPIs: heute=%.1f kWh (Daten heute: %s), Woche=%.1f kWh, Ersparnis=%.2f €, "
        "Auslastung=%.1f %%, Amortisierung=%.1f %%",
        kwh_heute, hat_daten_heute, kwh_woche, ersparnis_tag, auslastung, amortisierung,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f'<div style="background:{config.KPI_BG}; border-radius:{config.KPI_RADIUS}; padding:14px 18px;">'
            f'<div style="font-size:11px; color:{config.TEXT_GEDIMMT}; margin-bottom:6px;">⚡ Heute erzeugt</div>'
            f'<div style="font-size:26px; font-weight:500; color:white;">{txt_heute}</div>'
            f'<div style="font-size:11px; color:{config.TEXT_SCHWACH}; margin-top:4px;">{txt_heute_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div style="background:{config.KPI_BG}; border-radius:{config.KPI_RADIUS}; padding:14px 18px;">'
            f'<div style="font-size:11px; color:{config.TEXT_GEDIMMT}; margin-bottom:6px;">💰 Ersparnis (Tag)</div>'
            f'<div style="font-size:26px; font-weight:500; color:white;">{txt_ersparnis}</div>'
            f'<div style="font-size:11px; color:{config.TEXT_SCHWACH}; margin-top:4px;">{txt_ersp_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div style="background:{config.KPI_BG}; border-radius:{config.KPI_RADIUS}; padding:14px 18px;">'
            f'<div style="font-size:11px; color:{config.TEXT_GEDIMMT}; margin-bottom:6px;">📊 Auslastung heute</div>'
            f'<div style="font-size:26px; font-weight:500; color:white;">{txt_auslastung}</div>'
            f'<div style="height:6px; background:rgba(255,255,255,0.1); border-radius:3px; margin-top:10px;">'
            f'<div style="height:6px; width:{breite_auslast:.1f}%; background:{config.THI_BLAU}; border-radius:3px;"></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    _show_amortisierung(amortisierung)
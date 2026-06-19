
"""Zentrale Zahlen und Fakten, die im Streamlit-Dashboard angezeigt werden."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from THI_Photovoltaik.src.components import formulas

# cleaned_data.csv liegt in src/ -> von components/ aus eine Ebene hoch
CSV_PATH = Path(__file__).resolve().parent.parent / "cleaned_data.csv"

# Platzhalter – echte Anlagenwerte noch recherchieren
MAX_TAGESERZEUGUNG_KWH: float = 50.0
def _lade_kwh_daten() -> pd.DataFrame:
    """Lädt cleaned_data.csv und ergänzt die kWh-Spalten via formulas."""
    df = pd.read_csv(CSV_PATH)
    return formulas.umrechnung_in_kwh(df)  # fügt kwh_erzeugt / kwh_verbraucht hinzu


def _summe_kwh(df: pd.DataFrame, spalte: str, zeitraum: str) -> float:
    """Summiert eine kWh-Spalte über einen Zeitraum (bezogen auf jetzt)."""
    jetzt = pd.Timestamp.now(tz="UTC")
    grenzen = {
        "Tag": jetzt.normalize(),
        "Woche": jetzt - pd.Timedelta(days=7),
        "Monat": jetzt - pd.Timedelta(days=30),
        "Jahr": jetzt - pd.Timedelta(days=365),
    }
    maske = df["collected_at"] >= grenzen[zeitraum]
    return float(df.loc[maske, spalte].sum())


def tagesumme_erzeugter_strom() -> None:
    """Kumuliert erzeugte kWh des heutigen Tages, als Kennzahl-Box."""
    df = _lade_kwh_daten()
    kwh_heute = _summe_kwh(df, "kwh_erzeugt", "Tag")
    st.metric(label="Heute erzeugt", value=f"{kwh_heute:.1f} kWh")


def ersparnis_durch_pv() -> None:
    """Eingespartes Geld, Zeitraum per Dropdown wählbar."""
    zeitraum = st.selectbox("Zeitraum", ["Tag", "Woche", "Monat", "Jahr"])
    df = _lade_kwh_daten()
    kwh = _summe_kwh(df, "kwh_erzeugt", zeitraum)

    if kwh == 0:
        st.info(f"Für '{zeitraum}' liegen noch keine Daten vor.")
        return

    ersparnis = kwh * formulas.STROMPREIS
    st.metric(label=f"Ersparnis ({zeitraum})", value=f"{ersparnis:,.2f} €")


def auslastung_pv() -> None:
    """Tacho/Gauge: heutige Erzeugung relativ zum Tagesmaximum."""
    df = _lade_kwh_daten()
    kwh_heute = _summe_kwh(df, "kwh_erzeugt", "Tag")
    prozent = min(100.0, kwh_heute / MAX_TAGESERZEUGUNG_KWH * 100)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prozent,
        number={"suffix": " %"},
        gauge={"axis": {"range": [0, 100]}},
        title={"text": "Auslastung heute"},
    ))
    st.plotly_chart(fig, use_container_width=True)


def amortisierung_pv() -> None:
    """Fortschrittsbalken: zu wie viel % hat sich die Anlage amortisiert."""
    df = _lade_kwh_daten()
    kwh_gesamt = float(df["kwh_erzeugt"].sum())  # gesamter Zeitraum
    eingespart = kwh_gesamt * formulas.STROMPREIS
    prozent = min(100.0, eingespart / formulas.ANSCHAFFUNGSKOSTEN_PV_ANLAGE * 100)

    st.progress(prozent / 100, text=f"Amortisiert: {prozent:.1f} %")


def show_kpis() -> None:
    """Rendert alle KPIs in Spalten/Boxen im Streamlit-Dashboard."""
    spalte1, spalte2 = st.columns(2)
    with spalte1:
        tagesumme_erzeugter_strom()
        ersparnis_durch_pv()
    with spalte2:
        auslastung_pv()
        amortisierung_pv()


"""Hier wird das Dashboard erzeugt. Es werden alle anderen Python Files hier importiert und verwendet, um
das Dashboard über Streamlit zu erzeugen."""

# Imports
from pathlib import Path

import pandas as pd
import streamlit as st

from components.charts import (
    draw_calendar,
    create_chart_balkendiagramm,
    create_chart_kurvendiagramm,
    show_charts,
    YEAR,
    TITLE,
    UNIT,
)
from components.formulas import differenz_erzeugt_verbraucht
from components.header import show_header
from components.kpis import show_kpis

# CSV liegt in src/ → von main.py aus im selben Ordner
CSV_PATH = Path(__file__).resolve().parent / "cleaned_data.csv"


def streamlit_app() -> None:
    """
    Hier wird die Streamlit App final erstellt. Die einzelnen Komponenten, die erstellt worden sind,
    werden hier verwendet und zu einem Konstrukt zusammengebaut. Also alle components werden hier zum
    finalen Dashboard zusammengebaut.
    """
    st.set_page_config(
        page_title="PV Dashboard – THI",
        page_icon="☀️",
        layout="wide",
    )

    # ── Header ──────────────────────────────────────────
    show_header()

    # ── Daten laden ─────────────────────────────────────
    df = pd.read_csv(CSV_PATH)

    # ── KPIs ────────────────────────────────────────────
    st.subheader("Kennzahlen")
    show_kpis()

    st.divider()

    # ── Kalender ────────────────────────────────────────
    st.subheader("Tägliche Bilanz (Kalender)")
    data = differenz_erzeugt_verbraucht(df)
    fig_kalender = draw_calendar(data, YEAR, TITLE, UNIT)
    st.pyplot(fig_kalender)

    st.divider()

    # ── Balkendiagramm ──────────────────────────────────
    st.subheader("Kumulierte Differenz pro Stunde")
    fig_balken = create_chart_balkendiagramm(df)
    st.pyplot(fig_balken)

    st.divider()

    # ── Kurvendiagramm ──────────────────────────────────
    st.subheader("Täglicher Verlauf: Erzeugung & Verbrauch")
    fig_kurve = create_chart_kurvendiagramm(df)
    st.pyplot(fig_kurve)


if __name__ == "__main__":
    streamlit_app()
"""Hier wird das Dashboard erzeugt. Es werden alle anderen Python Files hier importiert und verwendet, um
das Dashboard über Streamlit zu erzeugen."""

from pathlib import Path

import pandas as pd
import streamlit as st

from components.charts import (
    draw_calendar_3monate,
    create_chart_balkendiagramm,
    create_chart_kurvendiagramm,
    YEAR,
    UNIT,
)
from components.formulas import differenz_erzeugt_verbraucht
from components.header import show_header
from components.kpis import show_kpis

CSV_PATH = Path(__file__).resolve().parent / "cleaned_data.csv"


def streamlit_app() -> None:
    """
    Hier wird die Streamlit App final erstellt. Die einzelnen Komponenten, die erstellt worden sind,
    werden hier verwendet und zu einem Konstrukt zusammengebaut.
    """
    st.set_page_config(
        page_title="PV Dashboard – THI",
        page_icon="☀️",
        layout="wide",
    )

    # ── Header ──────────────────────────────────────────
    show_header()

    # ── Daten laden ─────────────────────────────────────
    df   = pd.read_csv(CSV_PATH)
    data = differenz_erzeugt_verbraucht(df)

    # ── KPIs ────────────────────────────────────────────
    show_kpis(df)

    st.divider()

    # ── Zeile 1: Balken + Kurve nebeneinander ───────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.pyplot(create_chart_balkendiagramm(df))
    with col_r:
        st.pyplot(create_chart_kurvendiagramm(df))

    st.divider()

    # ── Zeile 2: 3-Monats-Kalender volle Breite ─────────
    st.pyplot(draw_calendar_3monate(data, UNIT))


if __name__ == "__main__":
    streamlit_app()
"""Hier wird das Dashboard erzeugt. Es werden alle anderen Python-Files hier importiert
und verwendet, um das Dashboard über Streamlit zu erzeugen."""

import logging

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from THI_Photovoltaik import config
from logging_setup import setup_logging
from components.charts import (
    draw_calendar_3monate,
    create_chart_balkendiagramm,
    create_chart_kurvendiagramm,
)
from components.formulas import differenz_erzeugt_verbraucht
from components.header import show_header
from components.kpis import show_kpis

CSV_PATH = config.CSV_PATH

setup_logging("projekt.log")
logger = logging.getLogger(__name__)
logger.info("Die App wurde gestartet")


def streamlit_app() -> None:
    """Baut die Streamlit-App aus den einzelnen Komponenten zusammen."""
    st.set_page_config(
        page_title="PV Dashboard – THI",
        page_icon="☀️",
        layout="wide",
    )

    # ── Header ──────────────────────────────────────────
    show_header()

    # ── Daten laden ─────────────────────────────────────
    try:
        df = pd.read_csv(CSV_PATH)
        logger.info("CSV geladen: %d Zeilen", len(df))
    except FileNotFoundError:
        logger.error("cleaned_data.csv nicht gefunden unter %s", CSV_PATH)
        st.error("Keine Daten vorhanden – läuft das Sammel-Skript?")
        st.stop()

    data = differenz_erzeugt_verbraucht(df)

    # ── KPIs ────────────────────────────────────────────
    show_kpis(df)

    st.divider()

    # ── Zeile 1: Balken + Kurve nebeneinander ───────────
    col_l, col_r = st.columns(2)
    with col_l:
        fig_balken = create_chart_balkendiagramm(df)
        st.pyplot(fig_balken)
        plt.close(fig_balken)
    with col_r:
        fig_kurve = create_chart_kurvendiagramm(df)
        st.pyplot(fig_kurve)
        plt.close(fig_kurve)

    st.divider()

    # ── Zeile 2: 3-Monats-Kalender volle Breite ─────────
    fig_kalender = draw_calendar_3monate(data, config.UNIT)
    st.pyplot(fig_kalender)
    plt.close(fig_kalender)


if __name__ == "__main__":
    streamlit_app()
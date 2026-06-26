"""Hier wird das Dashboard erzeugt. Es werden alle anderen Python-Files hier importiert
und verwendet, um das Dashboard über Streamlit zu erzeugen."""

import logging

import matplotlib.pyplot as plt
import streamlit as st

import config
from components.charts import (
    create_chart_balkendiagramm,
    create_chart_kurvendiagramm,
    draw_calendar_3monate,
)
from components.formulas import differenz_erzeugt_verbraucht
from components.header import show_header
from components.kpis import show_kpis
from components.storage import DataStorage
from logging_setup import setup_logging

# setup_logging nur einmal aufrufen – nicht bei jedem Streamlit-Rerun
if not logging.getLogger().handlers:
    setup_logging(config.LOG_FILE)

logger = logging.getLogger(__name__)
logger.info("Die App wurde gestartet")


@st.fragment(run_every=60)
def show_dashboard_content() -> None:
    """Lädt Daten und rendert KPIs + alle Charts als Einheit (jede Minute neu)."""
    db = DataStorage()
    df = db.load_raw_df()

    if df.empty:
        logger.error("Keine Rohdaten in der Datenbank")
        st.error("Keine Daten vorhanden – läuft das Sammel-Skript?")
        st.stop()

    logger.info("Datenbank geladen: %d Rohzeilen", len(df))

    data = differenz_erzeugt_verbraucht(df)

    # ── KPIs ────────────────────────────────────────────────────────────────
    show_kpis(df, db.gesamt_kwh_erzeugt())

    st.divider()

    # ── Alle Figuren zuerst berechnen, dann gemeinsam anzeigen ──────────────
    fig_balken = create_chart_balkendiagramm(df)
    fig_kurve = create_chart_kurvendiagramm(df)
    fig_kalender = draw_calendar_3monate(data, config.UNIT)

    col_l, col_r = st.columns(2)
    with col_l:
        st.pyplot(fig_balken)
    with col_r:
        st.pyplot(fig_kurve)

    plt.close(fig_balken)
    plt.close(fig_kurve)

    st.divider()

    st.pyplot(fig_kalender)
    plt.close(fig_kalender)


def streamlit_app() -> None:
    """Baut die Streamlit-App aus den einzelnen Komponenten zusammen."""
    st.set_page_config(
        page_title="PV Dashboard – THI",
        page_icon="☀️",
        layout="wide",
    )

    # ── Header (refresht jede Minute: Wetter + Uhrzeit) ─────────────────────
    show_header()

    # ── Daten, KPIs und Charts (alle zusammen als Fragment) ─────────────────
    show_dashboard_content()


if __name__ == "__main__":
    streamlit_app()

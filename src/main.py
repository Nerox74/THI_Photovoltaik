"""Hier wird das Dashboard erzeugt. Es importiert die übrigen Module und baut über
Streamlit die Weboberfläche zusammen."""

import logging

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import components.formulas as formulas
import config
from components.charts import create_chart_tagesverlauf, draw_calendar_3monate
from components.formulas import daten_frische, differenz_erzeugt_verbraucht
from components.header import show_header
from components.kpis import show_energiebilanz, show_kpis, show_momentan
from components.storage import DataStorage
from logging_setup import setup_logging

# setup_logging nur einmal aufrufen – nicht bei jedem Streamlit-Rerun
if not logging.getLogger().handlers:
    setup_logging(config.LOG_FILE)

logger = logging.getLogger(__name__)
logger.info("Die App wurde gestartet")
logger.info("Dashboard erreichbar unter: http://localhost:8502")


@st.fragment(run_every=60)
def show_dashboard_content() -> None:
    """Lädt Daten und rendert Live-Strip, KPIs, Energiebilanz und Charts."""
    db = DataStorage()
    df = db.load_raw_df()

    if df.empty:
        logger.error("Keine Rohdaten in der Datenbank")
        st.error("Keine Daten vorhanden – läuft das Sammel-Skript?")
        st.stop()

    logger.info("Datenbank geladen: %d Rohzeilen", len(df))

    letzter_ts = pd.to_datetime(df["collected_at"], format="ISO8601", utc=True).max()
    frische = daten_frische(letzter_ts)
    if not frische["ist_frisch"]:
        logger.warning(
            "Letzter Messwert ist veraltet (%s) – läuft der Collector noch?",
            frische["alter_text"],
        )
        st.warning(
            f"⚠️ Keine aktuellen Daten – der letzte Messwert ist {frische['alter_text']}. "
            "Läuft das Sammel-Skript (Collector) noch?"
        )

    data = differenz_erzeugt_verbraucht(df)  # Tagesbilanz-Serie für den Kalender

    # ── Live-Status (Momentanwerte) ─────────────────────────────────────────
    show_momentan(df)

    st.divider()

    # ── KPI-Kacheln + Amortisierung ─────────────────────────────────────────
    show_kpis(df, db.gesamt_kwh_erzeugt())

    st.divider()

    # ── Energiebilanz Tag / Monat / Jahr ────────────────────────────────────
    show_energiebilanz(df, db)

    st.divider()

    # ── Zeitverlauf des aktuellen Tages ─────────────────────────────────────
    df_kwh, luecken_heute = formulas.umrechnung_in_kwh(df)
    fig_verlauf = create_chart_tagesverlauf(df, luecken_heute)
    st.pyplot(fig_verlauf)
    plt.close(fig_verlauf)

    st.divider()

    # ── 3-Monats-Kalender (tägliche Bilanz) ─────────────────────────────────
    fig_kalender = draw_calendar_3monate(data, config.UNIT)
    st.pyplot(fig_kalender)
    plt.close(fig_kalender)


def streamlit_app() -> None:
    """Baut die Streamlit-App aus den einzelnen Komponenten zusammen."""
    st.set_page_config(
        page_title="PV Dashboard – THI",
        page_icon="☀️",
        layout="wide",
    )
    show_header()
    show_dashboard_content()


if __name__ == "__main__":
    streamlit_app()

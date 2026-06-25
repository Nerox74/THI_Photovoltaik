"""Header der Streamlit-App: aktuelles Wetter, Temperatur, Datum/Uhrzeit und Standort."""

import datetime
import logging

import openmeteo_requests
import requests_cache
import streamlit as st
from retry_requests import retry

import config

# Open-Meteo-Client mit Cache und Retry
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

logger = logging.getLogger(__name__)


def get_weather_data() -> tuple[float, str, str]:
    """
    Holt die aktuellen Wetterdaten für den konfigurierten Standort von Open-Meteo.
    Returns: (Temperatur °C, Wetterbeschreibung, Icon)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": config.STANDORT_LAT,
        "longitude": config.STANDORT_LON,
        "current": ["temperature_2m", "weather_code"],
        "timezone": "Europe/Berlin",
        "forecast_days": 1,
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        current = response.Current()
        temp = round(current.Variables(0).Value(), 1)
        weather_code = int(current.Variables(1).Value())

        if weather_code == 0:
            weather_desc, icon = "Sonnig", "☀️"
        elif weather_code in [1, 2, 3]:
            weather_desc, icon = "Leicht bewölkt", "⛅"
        elif weather_code in [45, 48]:
            weather_desc, icon = "Nebelig", "🌫️"
        elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            weather_desc, icon = "Regen", "🌧️"
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            weather_desc, icon = "Schnee", "❄️"
        elif weather_code in [95, 96, 99]:
            weather_desc, icon = "Gewitter", "⛈️"
        else:
            weather_desc, icon = "Bewölkt", "☁️"

        logger.debug("Wetter: %s, %.1f °C", weather_desc, temp)
        return temp, weather_desc, icon

    except Exception as e:
        logger.error("Fehler beim Laden der Wetterdaten von der Open-Meteo-API: %s", e)
        return 20.0, "Keine Daten", "⚠️"


def get_date_and_time() -> tuple[str, str]:
    """Aktuelles Datum und Uhrzeit als Strings. Returns: (date, time)."""
    now = datetime.datetime.now()
    return now.strftime("%d.%m.%Y"), now.strftime("%H:%M")


@st.fragment(run_every=config.HEADER_REFRESH_S)
def show_header() -> None:
    """Erstellt den Header im THI-Design mit Wetter, Uhrzeit, Datum und Standort."""
    temp, weather_desc, icon = get_weather_data()
    date_str, time_str = get_date_and_time()

    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <div style="
                background: {config.THI_DUNKELBLAU};
                border-radius: 12px 12px 0 0;
                padding: 16px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 26px; color: {config.THI_HELLBLAU};">⚡</span>
                    <div>
                        <div style="font-size: 17px; font-weight: 500; color: white; margin: 0;">PV Dashboard</div>
                        <div style="font-size: 12px; color: {config.THI_BLAUGRAU}; margin: 0;">THI · {config.STANDORT_NAME}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: {config.THI_BLAUGRAU};">Aktuelles Wetter</div>
                        <div style="font-size: 14px; color: white; font-weight: 500;">{icon} {weather_desc} · {temp} °C</div>
                    </div>
                    <div style="width: 1px; height: 32px; background: rgba(255,255,255,0.2);"></div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: {config.THI_BLAUGRAU};">Datum</div>
                        <div style="font-size: 14px; color: white; font-weight: 500;">{date_str}</div>
                    </div>
                </div>
            </div>
            <div style="
                background: {config.THI_BLAU};
                border-radius: 0 0 12px 12px;
                padding: 6px 24px;
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            ">
                <span style="font-size: 12px; font-weight: 500; color: {config.THI_BLAUGRAU_HELL};">📍 Standort: {config.STANDORT_NAME}</span>
                <span style="font-size: 12px; font-weight: 500; color: {config.THI_BLAUGRAU_HELL};">🕒 {time_str} Uhr</span>
                <span style="font-size: 12px; font-weight: 500; color: {config.THI_BLAUGRAU_HELL};">🔄 Aktualisierung alle 60 Sekunden.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
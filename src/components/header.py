"""Hier wird der Header der Streamlit App erstellt. In diesem wird das aktuelle Wetter und die Temperatur dargestellt,
je nach Wetter anders Symbol, plus der Ort in welchem man sich gerade befindet also Ingolstadt, da dort Photovoltaik ist
"""

# Imports
import datetime
import openmeteo_requests
import requests_cache
import streamlit as st
from retry_requests import retry

import logging

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


logger = logging.getLogger(__name__)

def get_weather_data() -> tuple[float, str, str]:
    """
    Holt die aktuellen Wetterdaten für Ingolstadt von der Open Meteo API
    Returns: tuple:(Temperatur in Grad Celsius, Wetterbeschreibung, Icon)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 48.76361,
        "longitude": 11.42611,
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

        return temp, weather_desc, icon

    except Exception:
        return 20.0, "Keine Daten", "⚠️"


def get_date_and_time() -> tuple[str, str]:
    """
    Hier wird das aktuelle Datum und die aktuelle Uhrzeit herausgefunden.
    Returns: date(str), time(str)
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")
    return date_str, time_str


@st.fragment(run_every=900)
def show_header() -> None:
    """
    Erstellt den Header im THI-Design (Dunkelblau #003366 + THI-Blau #005A9B)
    mit Wetter, Uhrzeit, Datum und Standort.
    """
    temp, weather_desc, icon = get_weather_data()
    date_str, time_str = get_date_and_time()

    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <div style="
                background: #003366;
                border-radius: 12px 12px 0 0;
                padding: 16px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 26px; color: #5EB3F0;">⚡</span>
                    <div>
                        <div style="font-size: 17px; font-weight: 500; color: white; margin: 0;">PV Dashboard</div>
                        <div style="font-size: 12px; color: #99B8D4; margin: 0;">THI · Ingolstadt</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: #99B8D4;">Aktuelles Wetter</div>
                        <div style="font-size: 14px; color: white; font-weight: 500;">{icon} {weather_desc} · {temp} °C</div>
                    </div>
                    <div style="width: 1px; height: 32px; background: rgba(255,255,255,0.2);"></div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: #99B8D4;">Datum</div>
                        <div style="font-size: 14px; color: white; font-weight: 500;">{date_str}</div>
                    </div>
                </div>
            </div>
            <div style="
                background: #005A9B;
                border-radius: 0 0 12px 12px;
                padding: 6px 24px;
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            ">
                <span style="font-size: 12px; font-weight: 500; color: #B8D4EE;">📍 Standort: Ingolstadt</span>
                <span style="font-size: 12px; font-weight: 500; color: #B8D4EE;">🕒 {time_str} Uhr</span>
                <span style="font-size: 12px; font-weight: 500; color: #B8D4EE;">🔄 Aktualisierung alle 15 Min.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
"""Hier wird der Header der Streamlit App erstellt. In diesem wird das aktuelle Wetter und die Temperatur dargestellt,
je nach Wetter anders Symbol, plus der Ort in welchem man sich gerade befindet also Ingolstadt, da dort Photovoltaik ist
"""

# Imports
# Verbindung mit API
import datetime
import openmeteo_requests
import requests_cache
import streamlit as st
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below




def get_weather_data() -> tuple[float,str, str]:
    """
    Holt die aktuellen Wetterdaten für Ingolstadt von der Open Mateo API

    Returns: tuple:(Temperatur in Grad Celsius, Wetterbeschreibung)
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
        responses = openmeteo.weather_api(url, params = params)
        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        current = response.Current()

        temp = round(current.Variables(0).Value(), 1)
        weather_code = int(current.Variables(1).Value())

        print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation: {response.Elevation()} m asl")
        print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

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

    except Exception as e:
        # Fallback, falls die API mal streikt
        return 20.0, "Keine Daten", "⚠️"




def get_date_and_time() -> tuple[str, str]:
    """

    Hier wird das akutelle Datum und die aktuelle Uhrzeit herausgefunden.

    Returns: date(str), time(str)

    """
    now = datetime.datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%H")
    return date_str, time_str

#Dadurch wird der Header alle 900 Sekunden neu geladen

@st.fragment(run_every=900)
def show_header() -> None:
    """Erstellt den Header im THI-Farbschema (Blau/Anthrazit) mit kompakter,

    links-mittiger Anordnung aller Wetter- und Ortsdaten.
    """
    temp, weather_desc, icon = get_weather_data()
    date_str, time_str = get_date_and_time()

    # THI Corporate Design Styles (Blau: #005A9B, Dunkelgrau: #333333)
    st.markdown(
        """
        <style>
        .thi-banner {
            background-color: #005A9B;
            color: white;
            padding: 15px 20px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .thi-title {
            font-size: 24px;
            font-weight: bold;
            margin: 0;
            padding-bottom: 5px;
        }
        .thi-info-bar {
            font-size: 16px;
            color: #E6F0FA;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .thi-info-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header-Inhalt im THI-Style rendern
    st.markdown(
        f"""
        <div class="thi-banner">
            <div class="thi-title">Photovoltaik Dashboard</div>
            <div class="thi-info-bar">
                <div class="thi-info-item">📍 <b>Ingolstadt (PV-Anlage)</b></div>
                <div class="thi-info-item">🕒 {time_str} Uhr</div>
                <div class="thi-info-item">{icon} {weather_desc}</div>
                <div class="thi-info-item">🌡️ <b>{temp} °C</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dezenter Hinweis zur letzten Aktualisierung darunter
    st.caption(
        f"Letzte Aktualisierung der Wetterdaten: {date_str} um {time_str} Uhr (wird alle 15 Min. automatisch aktualisiert)"
    )


# --- APP STARTEN ---
show_header()

# Weiterer App-Inhalt
st.write("Hier folgen die Photovoltaik-Messdaten und Auswertungen...")
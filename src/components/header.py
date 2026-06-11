"""Hier wird der Header der Streamlit App erstellt. In diesem wird das aktuelle Wetter und die Temperatur dargestellt,
je nach Wetter anders Symbol, plus der Ort in welchem man sich gerade befindet also Ingolstadt, da dort Photovoltaik ist
"""

# Imports
# mateo evtl.


# Verbindung mit API


def api_connection() -> dict:
    """
    Stellt eine Verbindung zur Wetter-Api her.
    """


def get_weather_data() -> tuple[str, int]:
    """

    Aktuelle Temperatur und das aktuelle Wetter über die Wetter-Api herausfinden, in Ingolstadt--> sonnig, regen usw.

    Returns: Int(Temperatur) und String(Wetter)

    """


def get_date_and_time() -> tuple[str, str]:
    """

    Hier wird das akutelle Datum und die aktuelle Uhrzeit herausgefunden.

    Returns: date(str), time(str)


    """


def show_header() -> None:
    """


    Erstellt den Header für die Streamlit-App. In diesem Header wird der Ort der PV-Anlage:
    Ingolstadt, die aktuelle Uhrzeit sowie Temperatur und auch das Wetter angezeigt (sonnig, regen, usw.).
    Als Überschrift wird der Name der APP Angezeigt: Photovoltaik Dashboard


    """

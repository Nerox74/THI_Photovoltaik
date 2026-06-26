"""Unittests für header.py."""

import components.header as header_modul
from components.header import get_date_and_time, get_weather_data


def test_get_date_and_time_gibt_zwei_strings_zurueck():
    datum, uhrzeit = get_date_and_time()
    assert isinstance(datum, str)
    assert isinstance(uhrzeit, str)


def test_datum_hat_format_dd_mm_yyyy():
    datum, _ = get_date_and_time()
    # Format: DD.MM.YYYY → 10 Zeichen, Punkte an Stelle 2 und 5
    assert len(datum) == 10
    assert datum[2] == "."
    assert datum[5] == "."


def test_uhrzeit_hat_format_hh_mm():
    _, uhrzeit = get_date_and_time()
    # Format: HH:MM → 5 Zeichen, Doppelpunkt an Stelle 2
    assert len(uhrzeit) == 5
    assert uhrzeit[2] == ":"


def test_get_weather_data_fallback_wenn_api_nicht_erreichbar(monkeypatch):
    """Wenn die Wetter-API ausfällt, muss der Fallback zurückgegeben werden."""

    def fake_api_fehler(*args, **kwargs):
        raise Exception("API nicht erreichbar")

    monkeypatch.setattr(header_modul.openmeteo, "weather_api", fake_api_fehler)

    temp, beschreibung, icon = get_weather_data()
    assert temp == 20.0
    assert beschreibung == "Keine Daten"
    assert icon == "⚠️"

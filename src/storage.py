"""Speichert die bereinigten PV-Daten persistent,
damit historische Werte für Charts und KPIs verfügbar bleiben."""

import data_cleaning

class DataStorage:
    """Verwaltet das Speichern und Laden der bereinigten PV-Daten."""

    def __init__(self) -> None:
        pass

    def save_data(self, daten: dict) -> None:
        """Speichert bereinigte Daten (kWh, Zeit) in die Storage-Datei."""

    def load_data(self, von: str, bis: str) -> dict:
        """Lädt historische Daten für einen Zeitraum aus dem Storage."""
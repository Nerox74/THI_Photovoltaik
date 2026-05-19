"""Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien"""

# Imports

import logging

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# Überlegen wie live Daten geholt werden können --> ist immer live
def verbindung_prometheus():
    """
    Stellt eine Verbindung zum Prometheus Server her, sodass die Daten von diesem abgerufen werden können.

    Args:

    Params:

    Returns:
        PV-Anlagen Daten
    """

def daten_laden():
    """
    Nachdem die Verbindung mit Prometheus hergestellt worden ist, können jetzt die Daten geladen werden

    Args:

    Params:

    Returns:
    """



#bevor wir die Realen Daten haben, liegen hier die Simulierten Daten vor

def generate_simple_pv_data():
    """
    Hier werden die PV-Daten simliert


    Returns:
        df : pandas df, mit den Daten in der Form KwH der Uhrzeit zu welcher diese erzeugt worden sind.
            Die Column - Header lauten: "Zeit" und "Erzeugung_kWh"
    """

    # Startzeitpunkt (z. B. heute um 00:00 Uhr)
    start_time = datetime(2026, 5, 19, 0, 0)

    # 96 Schritte für 24 Stunden (alle 15 Minuten)
    times = [start_time + timedelta(minutes=15 * i) for i in range(96)]

    # Sinuswelle für den Tagesverlauf der Sonne generieren
    x = np.linspace(0, np.pi, 96)
    curve = np.sin(x)

    # Werte unter 0 (Nacht) abschneiden
    curve = np.where(curve < 0, 0, curve)

    # Umrechnung in kWh für diesen 15-Minuten-Intervall
    # (Simuliert eine PV-Anlage, die mittags ca. 1.25 kWh pro Viertelstunde erzeugt)
    kwh_values = curve * 1.25

    # Runden auf 3 Nachkommastellen für saubere Daten
    kwh_values = np.round(kwh_values, 3)

    # DataFrame erstellen
    df = pd.DataFrame({
        "Zeit": times,
        "Erzeugung_kWh": kwh_values
    })

    return df


# Simulation ausführen und anzeigen
df_simulation = generate_simple_pv_data()
print(df_simulation.to_string(index=False))

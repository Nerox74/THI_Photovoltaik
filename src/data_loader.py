""" Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien"""

# Imports

import logging
import pandas as pd





#Überlegen wie live Daten geholt werden können --> ist immer live
def verbindung_prometheus():

    """
    Stellt eine Verbindung zum Prometheus Server her, sodass die Daten von diesem abgerufen werden können.

    Args:

    Params:

    Returns:
        PV-Anlagen Daten
    """
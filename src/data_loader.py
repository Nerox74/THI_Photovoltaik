"""Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien"""

# Imports


# Überlegen wie live Daten geholt werden können --> ist immer live


def prometheus_connection() -> None:
    """
    Stellt eine Verbindung zum Prometheus Server her, sodass die Daten von diesem abgerufen werden können.

    """


def data_loader() -> dict:
    """
    Nachdem die Verbindung mit Prometheus hergestellt worden ist, können jetzt die Daten geladen werden
    """


def data_cleaner(daten:dict) -> dict:
    """
    Bekommt die Daten vom Data Loader und bringt diese in das Format, mit welchem wir auch schlussendlich Arbeiten wollen.
    Format welches hier ausgegeben werden soll: (KWh, Zeit)

    """

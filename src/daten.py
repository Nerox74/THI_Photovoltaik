"""Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien"""

# Imports


# Überlegen wie live Daten geholt werden können --> ist immer live



class PrometheusDatenbeschaffung:

    def __init__(self, api: str, token: str) -> None:
        self.api = api
        self.token = token


    def prometheus_connection(self) -> None:
        """
        Stellt eine Verbindung zum Prometheus Server her, sodass die Daten von diesem abgerufen werden können.

        """


    def data_loader(self) -> dict:
        """
        Nachdem die Verbindung mit Prometheus hergestellt worden ist, können jetzt die Daten geladen werden
        """


    def data_cleaner(self,daten: dict) -> dict:
        """
        Bekommt die Daten vom Data Loader und bringt diese in das Format, mit welchem wir auch schlussendlich Arbeiten wollen.
        Format welches hier ausgegeben werden soll: (KWh, Zeit)

         """

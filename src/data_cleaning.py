"""Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien, bereinigt die Daten und speichert die bereinigten Daten in cleaned_data.csv"""
from streamlit.runtime.credentials import Credentials

# Imports
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib3

#Wenn nicht funktioniert OPC Server -> exponentielle Wartezeit

#Ordner in welchem env File liegt --> 1 Ornder über src
env_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=env_path)

#Jetzt kann über environ auf das File zugegriffen werden
URL = os.environ.get("JUPYTER_HUB_URL")
API_KEY= os.environ.get("API_KEY")


# Unterdrückt die "InsecureRequestWarning" (weil wir mit verify=False arbeiten)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {"X-API-Key": API_KEY.strip(), "Accept": "application/json"}

response = requests.get(URL, headers=headers, verify=False)
data = response.json()
#print("Status:", response.status_code)
print(response.json())


# Daten auseinander nehmen und in einzelteile zerlegen
# Daten Formatieren und richtig machen
# Daten speichern

# iterativ alle 7 Sekunden, wenn daten nicht veränderlich oder keine neuen Datne dann 14 Sekunden noch einmal schauen
# Wenn wieder nicht neu dann 28 Sekunden dann immer so weiter exponentiell

from datetime import datetime
uhrzeit = datetime.fromisoformat(data['collected_at']).strftime("%H:%M")

# 2. Summe der PV-Erzeugung (generation) in kW
summe_generation_w = sum(item['value'] for item in data['data'] if item['type'] == 'generation')
summe_generation_kw = round(summe_generation_w / 1000, 2)

# 3. Summe des Verbrauchs/Einspeisung (consumption) in kW
summe_einspeisung_w = sum(item['value'] for item in data['data'] if item['type'] == 'consumption')
summe_einspeisung_kw = round(summe_einspeisung_w / 1000, 2)

# Ergebnis für dein Dashboard
print(f"Uhrzeit: {uhrzeit}")
print(f"PV-Erzeugung: {summe_generation_kw} kW")
print(f"Netz-Wert: {summe_einspeisung_kw} kW")

class Datenbeschaffung:

    def __init__(self, api: str, token: str) -> None:
        self.api = api
        self.token = token


    def api_connection(self) -> None:
        """
        Stellt eine Verbindung zum Prometheus Server her, sodass die Daten von diesem abgerufen werden können.

        """
        pass


    def data_loader(self) -> dict:
        """
        Nachdem die Verbindung mit Prometheus hergestellt worden ist, können jetzt die Daten geladen werden
        """
        pass


    def data_cleaner(self,daten: dict) -> dict:
        """
        Bekommt die Daten vom Data Loader und bringt diese in das Format, mit welchem wir auch schlussendlich Arbeiten wollen.
        Format welches hier ausgegeben werden soll: (KWh, Zeit)

         """
        pass

"""Stellt eine Verbindung zu Prometheus her und holt von dort die CSV-Dateien, bereinigt die Daten und speichert die bereinigten Daten in cleaned_data.csv"""
from streamlit.runtime.credentials import Credentials

# Imports
import csv
import requests
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import urllib3
from datetime import datetime
from dotenv import load_dotenv
import logging


logger = logging.getLogger(__name__)


INTERVALL_SEKUNDEN = 5
#Maximal wird 2 Stunden auf neue Daten gewartet, länger nicht
MAX_WAIT_TIME = 7200


#Ordner in welchem env File liegt --> 1 Ornder über src
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

#Jetzt kann über environ auf das File zugegriffen werden
URL = os.environ.get("JUPYTER_HUB_URL")
API_KEY= os.environ.get("API_KEY")

CSV_PATH = Path(__file__).resolve().parent / "cleaned_data.csv"

# Unterdrückt die "InsecureRequestWarning" (weil wir mit verify=False arbeiten)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {"X-API-Key": API_KEY.strip(), "Accept": "application/json"}


def daten_abrufen() -> dict:
    """Ruft die aktuellen Rohdaten vom Server ab."""
    response = requests.get(URL, headers=HEADERS, verify=False, timeout=30)
    response.raise_for_status()
    return response.json()

#Datenbeispiel vom Server
#{"collected_at":"2026-06-19T09:39:23.998841+02:00","data":[{"path":"BT A Süd/F/G/H/J > Devices > GU03 Einspeisung > Datapoints > InstantaneousValues > Ptot","type":"consumption","value":309974.25},{"path":"BT A Süd/F/G/H/J > Devices > 5Q2 PV-Anlage > Datapoints > InstantaneousValues > Ptot","type":"generation","value":139447.546875},{"path":"BT A Süd/F/G/H/J > Devices > GU17_PV > Datapoints > InstantaneousValues > Ptot","type":"generation","value":11087.197265625},{"path":"BT A Süd/F/G/H/J > Devices > PV-BT-A_F > Datapoints > InstantaneousValues > Ptot","type":"generation","value":47684.484375}],"age_seconds":0.383447}

def daten_bereinigen(data: dict) -> dict:
    """Bringt die Rohdaten in das Zielformat: (Zeit, PV-Erzeugung kW, Netz-Wert kW)."""

    collected_at = data["collected_at"]
    uhrzeit = datetime.fromisoformat(collected_at).strftime("%H:%M")

    summe_generation_w = sum(
        item["value"] for item in data["data"] if item["type"] == "generation"
    )
    summe_einspeisung_w = sum(
        item["value"] for item in data["data"] if item["type"] == "consumption"
    )

    return {
        "collected_at": collected_at,
        "uhrzeit": uhrzeit,
        "pv_erzeugung_kw": round(summe_generation_w / 1000, 2),
        "netz_wert_kw": round(summe_einspeisung_w / 1000, 2),
    }


def zeile_speichern(zeile: dict) -> None:
    """Hängt eine bereinigte Zeile an cleaned_data.csv an (Header wird einmalig geschrieben)."""
    feldnamen = ["collected_at", "uhrzeit", "pv_erzeugung_kw", "netz_wert_kw"]
    datei_existiert = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=feldnamen)
        if not datei_existiert:
            writer.writeheader()
        writer.writerow(zeile)


def automatische_abfrage() -> None:
    """Fragt den Server alle 5 Sekunden ab und schreibt die Daten in cleaned_data.csv."""
    letzter_zeitstempel = None
    aktuelle_wartezeit = INTERVALL_SEKUNDEN

    # Wenn alle nächste 5min alle Daten genauso sind, dann

    while True:
        try:
            rohdaten = daten_abrufen()
            zeile = daten_bereinigen(rohdaten)

            # Doppelte Datensätze überspringen (gleicher collected_at) -> dann Zeit, wenn kleiner als 2 Stunden, dann Zeit verdoppeln also 5 auf 10 min usw.
            if zeile["collected_at"] != letzter_zeitstempel:
                zeile_speichern(zeile)
                letzter_zeitstempel = zeile["collected_at"]
                print(
                    f"[{zeile['uhrzeit']}] gespeichert -> "
                    f"PV: {zeile['pv_erzeugung_kw']} kW | Netz: {zeile['netz_wert_kw']} kW"
                )

                aktuelle_wartezeit = INTERVALL_SEKUNDEN

            else:
                aktuelle_wartezeit = min(
                    aktuelle_wartezeit * 2, MAX_WAIT_TIME
                )

                print(
                    f"[{zeile['uhrzeit']}] keine neuen Daten – übersprungen. "
                    f"Nächster Versuch in {aktuelle_wartezeit / 60:.1f} Minuten."
                )

        except Exception as fehler:
            aktuelle_wartezeit = min(
                aktuelle_wartezeit * 2, MAX_WAIT_TIME
            )
            print(f"Fehler beim Abruf: {fehler}")

        time.sleep(aktuelle_wartezeit)


if __name__ == "__main__":
    automatische_abfrage()
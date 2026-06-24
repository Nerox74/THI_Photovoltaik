"""Stellt eine Verbindung zu Prometheus her, holt die Rohdaten, bereinigt sie und
hängt die bereinigten Zeilen an cleaned_data.csv an."""

import csv
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

from THI_Photovoltaik import config

logger = logging.getLogger(__name__)

# .env liegt einen Ordner über src/
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

URL = os.environ.get("JUPYTER_HUB_URL")
API_KEY = os.environ.get("API_KEY")

CSV_PATH = config.CSV_PATH

# Unterdrückt die InsecureRequestWarning (wir arbeiten mit verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if not API_KEY:
    logger.warning("API_KEY nicht gesetzt – ist die .env vorhanden und befüllt?")
HEADERS = {"X-API-Key": (API_KEY or "").strip(), "Accept": "application/json"}


def daten_abrufen() -> dict:
    """Ruft die aktuellen Rohdaten vom Server ab."""
    response = requests.get(URL, headers=HEADERS, verify=False, timeout=30)
    response.raise_for_status()
    logger.info("Daten von Server wurden heruntergeladen")
    return response.json()


def daten_bereinigen(data: dict) -> dict:
    """Bringt die Rohdaten in das Zielformat: (Zeit, PV-Erzeugung kW, Netz-Wert kW)."""
    collected_at = data["collected_at"]
    uhrzeit = datetime.fromisoformat(collected_at).strftime("%H:%M")

    summe_generation_w = sum(
        item["value"] for item in data["data"] if item["type"] == "generation"
    )
    summe_verbrauch_w = sum(
        item["value"] for item in data["data"] if item["type"] == "consumption"
    )

    return {
        "collected_at": collected_at,
        "uhrzeit": uhrzeit,
        "pv_erzeugung_kw": round(summe_generation_w / 1000, 2),
        "netz_wert_kw": round(summe_verbrauch_w / 1000, 2),
    }


def zeile_speichern(zeile: dict) -> None:
    """Hängt eine bereinigte Zeile an cleaned_data.csv an (Header einmalig)."""
    feldnamen = ["collected_at", "uhrzeit", "pv_erzeugung_kw", "netz_wert_kw"]
    datei_existiert = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=feldnamen)
        if not datei_existiert:
            writer.writeheader()
        writer.writerow(zeile)


def automatische_abfrage() -> None:
    """Fragt den Server zyklisch ab und schreibt neue Daten in cleaned_data.csv.

    Bei unveränderten oder fehlerhaften Antworten wird die Wartezeit verdoppelt
    (exponentielles Backoff, gedeckelt durch config.MAX_WAIT_TIME).
    """
    logger.info(
        "Starte Abfrage: URL=%s, Intervall=%ds, Max-Wartezeit=%ds",
        URL, config.INTERVALL_SEKUNDEN, config.MAX_WAIT_TIME,
    )
    letzter_zeitstempel = None
    aktuelle_wartezeit = config.INTERVALL_SEKUNDEN

    while True:
        try:
            rohdaten = daten_abrufen()
            zeile = daten_bereinigen(rohdaten)

            if zeile["collected_at"] != letzter_zeitstempel:
                zeile_speichern(zeile)
                letzter_zeitstempel = zeile["collected_at"]
                logger.info(
                    "[%s] gespeichert -> PV: %s kW | Netz: %s kW",
                    zeile["uhrzeit"], zeile["pv_erzeugung_kw"], zeile["netz_wert_kw"],
                )
                aktuelle_wartezeit = config.INTERVALL_SEKUNDEN
            else:
                aktuelle_wartezeit = min(aktuelle_wartezeit * 2, config.MAX_WAIT_TIME)
                logger.info(
                    "[%s] keine neuen Daten – übersprungen. Nächster Versuch in %.1f Min.",
                    zeile["uhrzeit"], aktuelle_wartezeit / 60,
                )

        except Exception as fehler:
            logger.error("Fehler beim Abruf (Server evtl. abgestürzt): %s", fehler)
            aktuelle_wartezeit = min(aktuelle_wartezeit * 2, config.MAX_WAIT_TIME)

        time.sleep(aktuelle_wartezeit)


if __name__ == "__main__":
    automatische_abfrage()
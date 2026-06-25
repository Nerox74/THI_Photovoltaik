"""Stellt eine Verbindung zu Prometheus her, holt die Rohdaten, bereinigt sie und
schreibt die bereinigten Zeilen in die SQLite-Datenbank."""

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

import config
from components.storage import DataStorage

logger = logging.getLogger(__name__)

# .env liegt einen Ordner über src/
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

URL = os.environ.get("JUPYTER_HUB_URL")
API_KEY = os.environ.get("API_KEY")

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


def automatische_abfrage() -> None:
    """Fragt den Server zyklisch ab und schreibt neue Daten in die Datenbank.

    Bei unveränderten oder fehlerhaften Antworten wird die Wartezeit verdoppelt
    (exponentielles Backoff, gedeckelt durch config.MAX_WAIT_TIME).

    Einmal pro Stunde: Tagesbilanz auffrischen + alte Rohdaten löschen (Retention).
    """
    db = DataStorage()
    logger.info(
        "Starte Abfrage: URL=%s, Intervall=%ds, Max-Wartezeit=%ds",
        URL, config.INTERVALL_SEKUNDEN, config.MAX_WAIT_TIME,
    )
    aktuelle_wartezeit = config.INTERVALL_SEKUNDEN
    letzte_wartung = time.monotonic()

    while True:
        try:
            rohdaten = daten_abrufen()
            zeile = daten_bereinigen(rohdaten)

            # insert_row gibt True zurück, wenn die Zeile neu war (PRIMARY KEY nicht doppelt)
            if db.insert_row(zeile):
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

            # Einmal pro Stunde: Tagesbilanz auffrischen + alte Rohdaten löschen
            if time.monotonic() - letzte_wartung >= 3600:
                db.prune()  # rollt erst auf, dann Retention (90 Tage)
                letzte_wartung = time.monotonic()

        except Exception as fehler:
            logger.error("Fehler beim Abruf (Server evtl. abgestürzt): %s", fehler)
            aktuelle_wartezeit = min(aktuelle_wartezeit * 2, config.MAX_WAIT_TIME)

        time.sleep(aktuelle_wartezeit)


if __name__ == "__main__":
    automatische_abfrage()
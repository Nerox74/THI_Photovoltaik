"""Zentrale Konfiguration: alle Magic Numbers, Pfade und Farben an einem Ort.

WICHTIG: Hier stehen KEINE Secrets (API-Key, URL) – die kommen aus der .env.
Diese Datei darf und soll ins Git (sie ist Teil der Dokumentation)."""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PFADE
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)


# CSV_PATH = DATA_DIR / "cleaned_data.csv"


DB_PATH = DATA_DIR / "pv_data.db"
LOG_FILE = DATA_DIR / "projekt.log"

# ─────────────────────────────────────────────────────────────────────────────
# ZEIT
# ─────────────────────────────────────────────────────────────────────────────
ZEITZONE = "Europe/Berlin"  # Rohdaten kommen in UTC; Tagesgrenzen/Anzeige lokal

# ─────────────────────────────────────────────────────────────────────────────
# DATENSAMMLUNG (Collector / data_module.py)
# ─────────────────────────────────────────────────────────────────────────────
INTERVALL_SEKUNDEN = 5
MAX_WAIT_TIME = 7200
REQUEST_TIMEOUT = 30

# ─────────────────────────────────────────────────────────────────────────────
# SPEICHERUNG / RETENTION (storage.py)
# ─────────────────────────────────────────────────────────────────────────────
RETENTION_TAGE = 90  # So lange bleiben Rohwerte in der DB; danach nur Tagesbilanz.

# ─────────────────────────────────────────────────────────────────────────────
# BERECHNUNG (formulas.py / kpis.py)
# ─────────────────────────────────────────────────────────────────────────────
MAX_LUECKE_H = 1 / 60  # Intervalle > 1,5 h gelten als Datenlücke (Collector war aus)
STROMPREIS = 0.39
ANSCHAFFUNGSKOSTEN_PV_ANLAGE = 15_000.0
MAX_TAGESERZEUGUNG_KWH = 400.0  # Referenz für Auslastung; bester gemessener Tag ~388 kWh
CO2_FAKTOR_KG_PRO_KWH = 0.38  # Deutscher Strommix 2024 (ca. 380 g CO₂/kWh)

# ─────────────────────────────────────────────────────────────────────────────
# STANDORT & WETTER (header.py)
# ─────────────────────────────────────────────────────────────────────────────
STANDORT_NAME = "Ingolstadt"
STANDORT_LAT = 48.76361
STANDORT_LON = 11.42611
WETTER_CACHE_SEKUNDEN = 3600
WETTER_RETRIES = 5
HEADER_REFRESH_S = 60

# ─────────────────────────────────────────────────────────────────────────────
# THI CORPORATE COLORS (offizielle Hausfarben der TH Ingolstadt)
# ─────────────────────────────────────────────────────────────────────────────
THI_BLAU = "#005A9B"
THI_DUNKELBLAU = "#003366"
THI_HELLBLAU = "#5EB3F0"
THI_BLAUGRAU = "#99B8D4"
THI_BLAUGRAU_HELL = "#B8D4EE"

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD / CHART-FARBEN (Dark Theme)
# ─────────────────────────────────────────────────────────────────────────────
CHART_BG = "#1a1a2e"  # Figur-Hintergrund
PANEL_BG = "#16213e"  # Achsen-/Panel-Hintergrund
LEER_TAG_BG = "#2a2a4a"  # leere Kalenderzelle
KPI_BG = "#1e2130"  # KPI-Kachel-Hintergrund
KPI_RADIUS = "10px"

TEXT_HELL = "white"
TEXT_GEDIMMT = "#aaaacc"
TEXT_SCHWACH = "#666688"

FARBE_UEBERSCHUSS = "#2ecc71"  # grün – mehr erzeugt als verbraucht
FARBE_DEFIZIT = "#e74c3c"  # rot  – mehr verbraucht als erzeugt

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS (charts.py)
# ─────────────────────────────────────────────────────────────────────────────
YEAR = 2026
UNIT = "kWh"

MONTH_NAMES_DE = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]

"""Zentrale Konfiguration: alle Magic Numbers, Pfade und Farben an einem Ort.

WICHTIG: Hier stehen KEINE Secrets (API-Key, URL) – die kommen aus der .env.
Diese Datei darf und soll ins Git (sie ist Teil der Dokumentation)."""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PFADE
# ─────────────────────────────────────────────────────────────────────────────
# Projekt-Wurzel = ein Ordner über src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# DATA_DIR kann per Umgebungsvariable überschrieben werden (z. B. in Docker:
# DATA_DIR=/app/data). Lokal landet die CSV sonst direkt in src/.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR / "cleaned_data.csv"
LOG_FILE = PROJECT_ROOT / "projekt.log"

# ─────────────────────────────────────────────────────────────────────────────
# DATENSAMMLUNG (Collector / data_module.py)
# ─────────────────────────────────────────────────────────────────────────────
INTERVALL_SEKUNDEN = 5        # Grund-Abfrageintervall
MAX_WAIT_TIME = 7200          # max. Wartezeit bei Backoff (2 Stunden in Sekunden)
REQUEST_TIMEOUT = 30          # Timeout für den HTTP-Request in Sekunden

# ─────────────────────────────────────────────────────────────────────────────
# BERECHNUNG (formulas.py / kpis.py)
# ─────────────────────────────────────────────────────────────────────────────
MAX_LUECKE_H = 0.5            # Datenlücken > 30 Min werden nicht mitintegriert
STROMPREIS = 0.39            # € pro kWh
ANSCHAFFUNGSKOSTEN_PV_ANLAGE = 15_000.0   # € – für Amortisierungsrechnung
MAX_TAGESERZEUGUNG_KWH = 50.0             # 100 % Auslastung entspricht diesem Wert

# ─────────────────────────────────────────────────────────────────────────────
# STANDORT & WETTER (header.py)
# ─────────────────────────────────────────────────────────────────────────────
STANDORT_NAME = "Ingolstadt"
LATITUDE = 48.76361
LONGITUDE = 11.42611
WETTER_CACHE_SEKUNDEN = 3600     # Wetterdaten 1 h cachen
WETTER_RETRIES = 5
HEADER_REFRESH_SEKUNDEN = 900    # Header alle 15 Min aktualisieren

# ─────────────────────────────────────────────────────────────────────────────
# THI CORPORATE COLORS (offizielle Hausfarben der TH Ingolstadt)
# ─────────────────────────────────────────────────────────────────────────────
THI_BLAU = "#005A9B"          # THI-Primärblau
THI_DUNKELBLAU = "#003366"    # dunkles Blau für Header-Hintergrund
THI_HELLBLAU = "#5EB3F0"      # heller Akzent (Icons, Highlights)
THI_BLAU_TEXT = "#99B8D4"     # gedämpftes Blau für Sekundärtext
THI_BLAU_HELL_TEXT = "#B8D4EE"

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD / CHART-FARBEN (Dark Theme)
# ─────────────────────────────────────────────────────────────────────────────
BG_DUNKEL = "#1a1a2e"         # Figur-Hintergrund
BG_PANEL = "#16213e"          # Achsen-/Panel-Hintergrund
BG_LEER = "#2a2a4a"           # leere Kalenderzelle
KPI_BG = "#1e2130"            # KPI-Kachel-Hintergrund
KPI_RADIUS = "10px"

TEXT_HELL = "white"
TEXT_GEDAEMPFT = "#aaaacc"
TEXT_SCHWACH = "#666688"

FARBE_UEBERSCHUSS = "#2ecc71"  # grün – mehr erzeugt als verbraucht
FARBE_DEFIZIT = "#e74c3c"      # rot  – mehr verbraucht als erzeugt

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS (charts.py)
# ─────────────────────────────────────────────────────────────────────────────
YEAR = 2026
UNIT = "kWh"

MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
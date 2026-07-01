# THI Photovoltaik Dashboard

Ein Streamlit-Dashboard, das Live-Daten einer PV-Anlage von einem JupyterHub-Server abruft, sie in einer SQLite-Datenbank speichert und auf einer Weboberfläche visualisiert.

Das System besteht aus zwei Diensten:
- **Collector**: Fragt den Server zyklisch ab und schreibt neue Messwerte in die Datenbank.
- **Dashboard**: Liest die Datenbank und zeigt KPIs, Diagramme und einen 3-Monats-Kalender an.

---

## Projektstruktur

```
THI_Photovoltaik/
├── src/
│   ├── main.py              # Streamlit-App (Dashboard-Einstiegspunkt)
│   ├── data_module.py       # Collector: Daten abrufen, bereinigen, speichern
│   ├── config.py            # Alle Konfigurationswerte (keine Secrets)
│   ├── logging_setup.py     # Zentrales Logging (Konsole + rotierende Datei)
│   └── components/
│       ├── charts.py        # Matplotlib-Charts (Balken, Kurve, Kalender)
│       ├── formulas.py      # Berechnungen: kWh-Umrechnung, Tagesbilanz
│       ├── header.py        # Header mit Wetter, Uhrzeit und Standort
│       ├── kpis.py          # KPI-Kacheln (Heute, Woche, Ersparnis, Auslastung, Amortisierung)
│       └── storage.py       # SQLite-Datenbankzugriff (Lesen + Schreiben)
├── tests/
│   ├── components/
│   │   ├── test_charts.py
│   │   ├── test_formulas.py
│   │   ├── test_header.py
│   │   ├── test_kpis.py
│   │   └── test_storage.py
│   ├── integration/
│   │   └── test_integration.py
│   ├── test_data_module.py
│   ├── test_logging_setup.py
│   └── test_main.py
├── .env-example             # Vorlage für die .env-Datei
├── docker-compose.yml       # Startet Collector + Dashboard
├── Dockerfile               # Multi-Stage-Build (base → collector / dashboard)
├── pyproject.toml           # Projekt-Metadaten, Ruff, Black, pytest
└── requirements.txt         # Produktions-Abhängigkeiten für Docker
```

---

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert und gestartet
- Zugangsdaten zur JupyterHub-API (API-Key und URL)

---

## Setup & Starten (Docker)

### 1. Repository klonen

```bash
git clone <repository-url>
cd THI_Photovoltaik
```

### 2. `.env`-Datei anlegen

```bash
cp .env-example .env
```

Dann `.env` mit einem Texteditor öffnen und die echten Werte eintragen:

```
API_KEY=dein-api-key-hier
JUPYTER_HUB_URL=https://jupyterhub-wi.rz.fh-ingolstadt.de:8443/data
```

> **Wichtig:** Die `.env`-Datei enthält Secrets und ist in `.gitignore` — sie wird **nicht** ins Git-Repository gepusht.

### 3. Docker-Container bauen und starten

```bash
docker compose up --build
```

Beim ersten Start wird das Image gebaut (ca. 1–2 Minuten). Danach läuft:
- der **Collector** (sammelt alle 5 Sekunden neue Daten)
- das **Dashboard** unter [http://localhost:8501](http://localhost:8501)

### 4. Im Hintergrund laufen lassen (optional)

```bash
docker compose up --build -d
```

Logs anzeigen:
```bash
docker compose logs -f
```

### 5. Stoppen

```bash
docker compose down
```

> Die gesammelten Daten bleiben im Docker-Volume `pv-data` erhalten. Zum vollständigen Löschen: `docker compose down -v`

---

## Lokale Entwicklung (ohne Docker)

### 1. Virtuelle Umgebung erstellen

```bash
python -m venv .venv

# Mac/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 2. Abhängigkeiten installieren

Mit pip:
```bash
pip install -r requirements.txt
```

Mit Poetry (empfohlen für Entwicklung):
```bash
poetry install
# Dev-Dependencies (pytest, ruff, black, pre-commit):
poetry install --with dev
```

### 3. `.env`-Datei anlegen (wie oben beschrieben)

### 4. Collector starten (Terminal 1)

```bash
python src/data_module.py
```

### 5. Dashboard starten (Terminal 2)

```bash
streamlit run src/main.py
```

Dashboard erreichbar unter [http://localhost:8501](http://localhost:8501).

---

## Tests ausführen

```bash
pytest
```

Mit ausführlicher Ausgabe:
```bash
pytest -v --tb=short
```

---

## Konfiguration

Alle technischen Parameter (keine Secrets) sind in `src/config.py` gebündelt:

| Variable | Bedeutung | Standard |
|---|---|---|
| `INTERVALL_SEKUNDEN` | Abfrageintervall des Collectors | 5 s |
| `MAX_WAIT_TIME` | Maximale Wartezeit bei Backoff | 7200 s |
| `HEADER_REFRESH_S` | Automatischer Dashboard-Refresh | 60 s |
| `STROMPREIS` | Preis pro kWh für Ersparnis-KPI | 0,39 € |
| `ANSCHAFFUNGSKOSTEN_PV_ANLAGE` | Basis für Amortisierungsberechnung | 15.000 € |
| `MAX_TAGESERZEUGUNG_KWH` | Referenzwert für Auslastungs-KPI | 50 kWh |
| `RETENTION_TAGE` | Wie lange Rohwerte in der DB bleiben | 90 Tage |

---

## Aufgabenverteilung

```bash
Henning: Makefile, Docker, Ordnerstruktur
Michi: KPIs, Ordnerstruktur
Nils: Logging, SQL, Ordnerstruktur
```




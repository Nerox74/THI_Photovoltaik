# THI Photovoltaik Dashboard

Ein kleines Streamlit-Dashboard, das Live-Daten aus einem Prometheus-Server zieht, die Daten sauber aufbereitet (kWh und Zeitstempel) und auf einer Weboberfläche visualisiert.

Das Projekt ist aktuell noch im Aufbau (Work in Progress).

## Projektstruktur

* `src/main.py`: Der Haupt-Einstiegspunkt. Hier wird die Streamlit-App aus den einzelnen Komponenten zusammengebaut.
* `src/daten.py`: Enthält die Klasse `PrometheusDatenbeschaffung`, die die Verbindung zu Prometheus aufbaut, Daten lädt und bereinigt.
* `src/storage.py`: Enthält die Klasse `DataStorage`, die die bereinigten PV-Daten persistent speichert und historische Daten für Charts und KPIs bereitstellt.
* `src/components/`: Die einzelnen Bausteine des Dashboards:
  * `header.py`: Header der App mit Ort, Datum/Uhrzeit, aktuellem Wetter und Temperatur (Wetter-API).
  * `kpis.py`: Zentrale Kennzahlen wie Tagessumme, Ersparnis, Auslastung und Amortisierung der PV-Anlage.
  * `charts.py`: Visualisierungen (Kalendergrafik, Balkendiagramm, Kurvendiagramm).
  * `formulas.py`: Gemeinsame Berechnungen (z. B. Umrechnung in kWh, Differenz Erzeugung/Verbrauch).
* `src/logging_setup.py`: Zentrales Logging für Konsole und eine rotierende Logdatei, damit wir beim Debuggen sehen, was schiefgeht.
* `src/config.py`: Hier kommen später die API-Keys und Passwörter rein (**Wichtig:** Nicht ins Git pushen!). Eine Vorlage liegt in `src/config-example.py`.
* `tests/`: Unit-Tests für die einzelnen Module.
* `tests_integration/`: Integrationtests für das Zusammenspiel der Module (z. B. Data Loader → Data Cleaner → Berechnungen).

## Installation & Setup

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd THI_Photovoltaik
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**
   ```bash
   python -m venv venv

   # Unter Windows:
   venv\Scripts\activate
   # Unter Mac/Linux:
   source venv/bin/activate
   ```

3. **Abhängigkeiten installieren**
   ```bash
   # Nur zum Ausführen der App:
   pip install -r requirements.txt

   # Für die Entwicklung (inkl. pytest, ruff, black, pre-commit):
   pip install -r requirements.txt
   ```

4. **App starten**
   ```bash
   streamlit run src/main.py
   ```
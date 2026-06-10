# THI Photovoltaik Dashboard

Ein kleines Streamlit-Dashboard, das Live-Daten aus einem Prometheus-Server zieht, die Daten sauber aufbereitet (kWh und Zeitstempel) und auf einer Weboberfläche visualisiert. 

Das Projekt ist aktuell noch im Aufbau (Work in Progress).

## Projektstruktur

* `main.py`: Der Haupt-Einstiegspunkt. Hier wird die Streamlit-App zusammengebaut.
* `daten.py`: Enthält die Klasse `PrometheusDatenbeschaffung`, die die Verbindung zu Prometheus aufbaut, Daten lädt und bereinigt.
* `logging_setup.py`: Zentrales Logging für Konsole und eine rotierende Logdatei, damit wir beim Debuggen sehen, was schiefgeht.
* `config.py`: Hier kommen später die API-Keys und Passwörter rein (**Wichtig:** Nicht ins Git pushen!).
* `tests/`: Ordner mit Unittests für die verschiedenen Module (aktuell noch Dummy-Tests).

## Installation & Setup

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd THI_Photovoltaik

2. **Virtuelle Umgebung erstellen
   python -m venv venv
  # Unter Windows:
  venv\Scripts\activate
  # Unter Mac/Linux:
  source venv/bin/activate

3. **Abhängigkeiten installieren 
   pip install -r requirements.txt

4. **App starten
   streamlit run THI_Photovoltaik.src.main.py

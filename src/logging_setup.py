"""
Zentrales Logging-Setup für die Anwendung.

Konfiguriert das Root-Logging mit zwei Handlern:
- Konsole (stdout) für Live-Ausgaben während der Entwicklung
- Rotierende Logdatei für die persistente Aufzeichnung

Wird einmalig beim Anwendungsstart (z. B. in Entry.py) aufgerufen.
Andere Module holen sich ihren Logger anschließend über
logging.getLogger(__name__) und erben automatisch diese Konfiguration.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_file, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Initialisiert das Root-Logging mit Konsolen- und Datei-Handler.

    Die Konsole erhält ein kompaktes Format (Zeit, Level, Nachricht),
    die Logdatei zusätzlich den Logger-Namen für besseres Debugging.
    Die Datei rotiert automatisch bei 10 MB und behält die letzten
    5 Archive, um unbegrenztes Wachstum zu verhindern.

    Logger einiger lärmender Drittbibliotheken (matplotlib, urllib3,
    numexpr, PIL) werden auf WARNING gesetzt, damit sie das eigene
    Log nicht mit DEBUG-Meldungen überfluten.

    Args:
        log_file: Pfad zur Logdatei. Wird angelegt, falls nicht vorhanden.
        console_level: Mindest-Loglevel für die Konsolenausgabe
                       (Standard: logging.INFO).
        file_level: Mindest-Loglevel für die Logdatei
                    (Standard: logging.DEBUG, also ausführlicher).

    Side Effects:
        - Setzt das Level des Root-Loggers auf das Minimum beider Level.
        - Hängt zwei Handler an den Root-Logger an. Mehrfaches Aufrufen
          würde Handler duplizieren - daher nur einmal beim Start nutzen.
        - Verändert die Log-Level einiger Drittanbieter-Logger global.

    Beispiel:
        setup_logging("logs/app.log")
        setup_logging("logs/app.log", console_level=logging.WARNING)
    """

    fmt_console = "%(asctime)s | %(levelname)-8s | %(message)s"
    fmt_file = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(console_level)
    ch.setFormatter(logging.Formatter(fmt_console, datefmt))

    fh = RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=5)
    fh.setLevel(file_level)
    fh.setFormatter(logging.Formatter(fmt_file, datefmt))

    root = logging.getLogger()
    root.setLevel(min(console_level, file_level))
    root.addHandler(ch)
    root.addHandler(fh)

    for lib in ["matplotlib", "urllib3", "numexpr", "PIL"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

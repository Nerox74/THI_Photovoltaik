import logging
import os

from logging_setup import setup_logging


def test_setup_logging_erstellt_handler(tmp_path):
    # tmp_path ist ein temporärer Ordner, den pytest automatisch anlegt
    log_datei = tmp_path / "test.log"
    setup_logging(log_datei)

    root_logger = logging.getLogger()

    # Nach setup_logging muss der Root-Logger mindestens 2 Handler haben
    # (einen für die Konsole, einen für die Datei)
    assert len(root_logger.handlers) >= 2


def test_setup_logging_erstellt_log_datei(tmp_path):
    log_datei = tmp_path / "test.log"
    setup_logging(log_datei)

    # Die Logdatei muss nach dem Setup existieren
    assert log_datei.exists()
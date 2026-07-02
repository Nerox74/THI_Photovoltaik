"""Gemeinsame Test-Fixtures."""

import config
import pytest


@pytest.fixture(autouse=True)
def _test_luecken_schwelle(monkeypatch):
    """Hebt die Lücken-Schwelle für die Rechen-Tests an.

    Produktiv gilt config.MAX_LUECKE_H = 1/60 (der Collector läuft im Minutentakt,
    ein Abstand > 60 s ist also eine echte Datenlücke). Die Unit-/Integrationstests
    bauen aber bewusst grob (stündlich) getaktete Synthetik-Daten, um mit runden
    Erwartungswerten zu prüfen (z. B. 1 kW über 1 h = 1 kWh). Ohne Anpassung würde
    jeder Stundenschritt als Lücke gelten und die kWh-Integration 0 ergeben.

    Darum setzen wir die Schwelle im Test auf 1,5 h. Die Lücken-Logik selbst wird
    davon unberührt weiterhin geprüft (test_datenluecke_* nutzt eine echte 12-h-Lücke).
    """
    monkeypatch.setattr(config, "MAX_LUECKE_H", 1.5)

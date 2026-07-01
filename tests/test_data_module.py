"""Unittests für data_module.py."""

import data_module
from data_module import daten_abrufen, daten_bereinigen

# Realistisches Beispiel direkt vom Server
BEISPIEL_ROHDATEN = {
    "collected_at": "2026-06-19T09:39:23.998841+02:00",
    "data": [
        {
            "path": "BT A > Devices > GU03 Einspeisung > Datapoints",
            "type": "consumption",
            "value": 309974.25,
        },
        {
            "path": "BT A > Devices > 5Q2 PV-Anlage > Datapoints",
            "type": "generation",
            "value": 139447.546875,
        },
        {
            "path": "BT A > Devices > GU17_PV > Datapoints",
            "type": "generation",
            "value": 11087.197265625,
        },
        {
            "path": "BT A > Devices > PV-BT-A_F > Datapoints",
            "type": "generation",
            "value": 47684.484375,
        },
    ],
    "age_seconds": 0.38,
}


# ─────────────────────────────────────────────────────────────────────────────
# daten_bereinigen
# ─────────────────────────────────────────────────────────────────────────────


def test_daten_bereinigen_pv_erzeugung_wird_summiert_und_in_kw_umgerechnet():
    """Alle 'generation'-Werte werden summiert und von W → kW umgerechnet."""
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    erwartet = round((139447.546875 + 11087.197265625 + 47684.484375) / 1000, 2)
    assert zeile["pv_erzeugung_kw"] == erwartet


def test_daten_bereinigen_netz_wert_wird_in_kw_umgerechnet():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert zeile["netz_wert_kw"] == round(309974.25 / 1000, 2)


def test_daten_bereinigen_uhrzeit_hat_format_hh_mm():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert zeile["uhrzeit"] == "09:39"


def test_daten_bereinigen_hat_alle_pflichtfelder():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert set(zeile.keys()) == {
        "collected_at",
        "uhrzeit",
        "pv_erzeugung_kw",
        "netz_wert_kw",
    }


def test_daten_bereinigen_gibt_dict_zurueck():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert isinstance(zeile, dict)


def test_daten_bereinigen_nur_consumption_typen_in_netz():
    """Nur Einträge mit type='consumption' gehen in netz_wert_kw."""
    rohdaten = {
        "collected_at": "2026-06-19T10:00:00+00:00",
        "data": [
            {"type": "consumption", "value": 2000.0},
            {"type": "generation", "value": 1000.0},
        ],
    }
    zeile = daten_bereinigen(rohdaten)
    assert zeile["netz_wert_kw"] == 2.0  # nur 2000 W → 2.0 kW


def test_daten_bereinigen_ohne_generation_ergibt_null_kw():
    """Wenn keine 'generation'-Einträge vorhanden sind, muss pv_erzeugung_kw = 0 sein."""
    rohdaten = {
        "collected_at": "2026-06-19T10:00:00+00:00",
        "data": [{"type": "consumption", "value": 500.0}],
    }
    zeile = daten_bereinigen(rohdaten)
    assert zeile["pv_erzeugung_kw"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# daten_abrufen (mit Mock, kein echter Server nötig)
# ─────────────────────────────────────────────────────────────────────────────


class FakeResponse:
    """Simuliert eine echte requests-Antwort."""

    def raise_for_status(self):
        pass

    def json(self):
        return BEISPIEL_ROHDATEN


def test_daten_abrufen_gibt_json_zurueck(monkeypatch):
    monkeypatch.setattr(data_module.requests, "get", lambda *a, **k: FakeResponse())
    ergebnis = daten_abrufen()
    assert ergebnis == BEISPIEL_ROHDATEN


def test_daten_abrufen_gibt_dict_zurueck(monkeypatch):
    monkeypatch.setattr(data_module.requests, "get", lambda *a, **k: FakeResponse())
    ergebnis = daten_abrufen()
    assert isinstance(ergebnis, dict)


def test_daten_abrufen_wirft_exception_bei_http_fehler(monkeypatch):
    """Bei einem HTTP-Fehler (raise_for_status) muss eine Exception weitergegeben werden."""

    class BadResponse:
        def raise_for_status(self):
            raise Exception("HTTP 500")

        def json(self):
            return {}

    monkeypatch.setattr(data_module.requests, "get", lambda *a, **k: BadResponse())
    import pytest

    with pytest.raises(Exception):
        daten_abrufen()

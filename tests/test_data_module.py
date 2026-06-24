"""Unittests für data_module.py."""

import data_module
from data_module import daten_bereinigen, zeile_speichern

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


# ── daten_bereinigen ───────────────────────────────────────────────────────────

def test_daten_bereinigen_pv_erzeugung_wird_summiert_und_in_kw_umgerechnet():
    # 139447.55 + 11087.20 + 47684.48 = 198219.23 W → 198.22 kW
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert zeile["pv_erzeugung_kw"] == round((139447.546875 + 11087.197265625 + 47684.484375) / 1000, 2)


def test_daten_bereinigen_netz_wert_wird_in_kw_umgerechnet():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert zeile["netz_wert_kw"] == round(309974.25 / 1000, 2)


def test_daten_bereinigen_uhrzeit_hat_format_hh_mm():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert zeile["uhrzeit"] == "09:39"


def test_daten_bereinigen_hat_alle_felder():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert set(zeile.keys()) == {"collected_at", "uhrzeit", "pv_erzeugung_kw", "netz_wert_kw"}


def test_daten_bereinigen_gibt_dict_zurueck():
    zeile = daten_bereinigen(BEISPIEL_ROHDATEN)
    assert isinstance(zeile, dict)


# ── zeile_speichern ────────────────────────────────────────────────────────────

def test_zeile_speichern_erstellt_datei(tmp_path, monkeypatch):
    # CSV_PATH im Modul auf einen temporären Pfad umleiten
    monkeypatch.setattr(data_module, "CSV_PATH", tmp_path / "test.csv")

    zeile = {
        "collected_at": "2026-06-19T09:39:23+02:00",
        "uhrzeit": "09:39",
        "pv_erzeugung_kw": 198.22,
        "netz_wert_kw": 309.97,
    }
    data_module.zeile_speichern(zeile)
    assert (tmp_path / "test.csv").exists()


def test_zeile_speichern_schreibt_header_in_neue_datei(tmp_path, monkeypatch):
    monkeypatch.setattr(data_module, "CSV_PATH", tmp_path / "test.csv")

    zeile = {
        "collected_at": "2026-06-19T09:39:23+02:00",
        "uhrzeit": "09:39",
        "pv_erzeugung_kw": 198.22,
        "netz_wert_kw": 309.97,
    }
    data_module.zeile_speichern(zeile)
    inhalt = (tmp_path / "test.csv").read_text()
    # Header muss in der ersten Zeile stehen
    assert inhalt.splitlines()[0] == "collected_at,uhrzeit,pv_erzeugung_kw,netz_wert_kw"


def test_zeile_speichern_haengt_an_ohne_doppelten_header(tmp_path, monkeypatch):
    monkeypatch.setattr(data_module, "CSV_PATH", tmp_path / "test.csv")

    zeile = {
        "collected_at": "2026-06-19T09:39:23+02:00",
        "uhrzeit": "09:39",
        "pv_erzeugung_kw": 198.22,
        "netz_wert_kw": 309.97,
    }
    data_module.zeile_speichern(zeile)
    data_module.zeile_speichern(zeile)  # zweites Mal speichern

    zeilen = (tmp_path / "test.csv").read_text().splitlines()
    # 1 Headerzeile + 2 Datenzeilen = 3 Zeilen, KEIN doppelter Header
    assert len(zeilen) == 3
    assert zeilen[0] == "collected_at,uhrzeit,pv_erzeugung_kw,netz_wert_kw"


# ── daten_abrufen (mit Mock, kein echter Server nötig) ────────────────────────

class FakeResponse:
    """Simuliert eine echte requests-Antwort."""
    def raise_for_status(self):
        pass
    def json(self):
        return BEISPIEL_ROHDATEN


def test_daten_abrufen_gibt_json_zurueck(monkeypatch):
    monkeypatch.setattr(data_module.requests, "get", lambda *a, **k: FakeResponse())
    ergebnis = data_module.daten_abrufen()
    assert ergebnis == BEISPIEL_ROHDATEN


def test_daten_abrufen_gibt_dict_zurueck(monkeypatch):
    monkeypatch.setattr(data_module.requests, "get", lambda *a, **k: FakeResponse())
    ergebnis = data_module.daten_abrufen()
    assert isinstance(ergebnis, dict)
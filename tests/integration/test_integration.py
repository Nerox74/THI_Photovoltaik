"""Integrationstests: Datenpipeline von Rohdaten bis zur Tagesbilanz.

Testet das Zusammenspiel der Module:
    data_module.daten_bereinigen
    → components.storage.DataStorage (insert_row, load_raw_df)
    → components.formulas.umrechnung_in_kwh
    → components.formulas.differenz_erzeugt_verbraucht
"""

import pandas as pd
import pytest

from data_module import daten_bereinigen
from components.storage import DataStorage
from components.formulas import umrechnung_in_kwh, differenz_erzeugt_verbraucht


ROHDATEN_ERZEUGUNG = {
    "collected_at": "2026-06-19T10:00:00+00:00",
    "data": [
        {"type": "generation",  "value": 5000.0},   # 5 kW
        {"type": "consumption", "value": 2000.0},   # 2 kW
    ],
}

ROHDATEN_NACHFOLGER = {
    "collected_at": "2026-06-19T11:00:00+00:00",
    "data": [
        {"type": "generation",  "value": 6000.0},   # 6 kW
        {"type": "consumption", "value": 3000.0},   # 3 kW
    ],
}


@pytest.fixture
def temp_db(tmp_path):
    """Erstellt eine isolierte SQLite-Datenbank für jeden Test."""
    return DataStorage(db_path=tmp_path / "test_integration.db")


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Rohdaten → Bereinigung → Speicherung
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_rohdaten_bis_datenbank(temp_db):
    """Daten vom Server werden bereinigt und landen korrekt in der DB."""
    zeile = daten_bereinigen(ROHDATEN_ERZEUGUNG)
    inserted = temp_db.insert_row(zeile)

    assert inserted is True, "Neue Zeile muss erfolgreich eingefügt werden"

    df = temp_db.load_raw_df()
    assert len(df) == 1
    assert df["pv_erzeugung_kw"].iloc[0] == pytest.approx(5.0, abs=0.01)
    assert df["netz_wert_kw"].iloc[0] == pytest.approx(2.0, abs=0.01)


def test_pipeline_doppelter_zeitstempel_wird_ignoriert(temp_db):
    """Derselbe Zeitstempel darf nicht zweimal eingefügt werden (PRIMARY KEY)."""
    zeile = daten_bereinigen(ROHDATEN_ERZEUGUNG)
    first  = temp_db.insert_row(zeile)
    second = temp_db.insert_row(zeile)

    assert first is True
    assert second is False
    assert len(temp_db.load_raw_df()) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Datenbank → kWh-Umrechnung
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_datenbank_zu_kwh(temp_db):
    """Zwei gespeicherte Messpunkte werden korrekt in kWh umgerechnet."""
    for rohdaten in [ROHDATEN_ERZEUGUNG, ROHDATEN_NACHFOLGER]:
        temp_db.insert_row(daten_bereinigen(rohdaten))

    df = temp_db.load_raw_df()
    df_kwh = umrechnung_in_kwh(df)

    # 1 Stunde Abstand, Trapezregel: (5 + 6) / 2 × 1 h = 5.5 kWh
    assert df_kwh["kwh_erzeugt"].sum() == pytest.approx(5.5, abs=0.05)
    # (2 + 3) / 2 × 1 h = 2.5 kWh
    assert df_kwh["kwh_verbraucht"].sum() == pytest.approx(2.5, abs=0.05)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: kWh → Tagesbilanz
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_kwh_zu_tagesbilanz(temp_db):
    """Aus den gespeicherten Rohdaten wird eine korrekte Tagesbilanz berechnet."""
    for rohdaten in [ROHDATEN_ERZEUGUNG, ROHDATEN_NACHFOLGER]:
        temp_db.insert_row(daten_bereinigen(rohdaten))

    df = temp_db.load_raw_df()
    bilanz = differenz_erzeugt_verbraucht(df)

    # Erzeugung 5.5 kWh − Verbrauch 2.5 kWh = +3.0 kWh (Überschuss)
    assert len(bilanz) == 1
    assert bilanz.iloc[0] == pytest.approx(3.0, abs=0.1)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Rollup-Tagesbilanz → Gesamt-kWh überlebt Retention
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_gesamt_kwh_ueberlebt_prune(temp_db):
    """Nach dem Prunen (Löschen alter Rohzeilen) bleibt gesamt_kwh_erzeugt erhalten."""
    for rohdaten in [ROHDATEN_ERZEUGUNG, ROHDATEN_NACHFOLGER]:
        temp_db.insert_row(daten_bereinigen(rohdaten))

    # Rollup ausführen, dann Rohdaten löschen (0-Tage-Retention = alles weg)
    temp_db.rollup_tagesbilanz()
    temp_db.prune(tage=0)

    assert temp_db.load_raw_df().empty, "Rohzeilen müssen nach prune(0) weg sein"
    assert temp_db.gesamt_kwh_erzeugt() == pytest.approx(5.5, abs=0.05)

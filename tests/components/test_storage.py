"""Unittests für components/storage.py (DataStorage)."""

import pytest
import pandas as pd

from components.storage import DataStorage


@pytest.fixture
def db(tmp_path):
    """Isolierte In-Memory-ähnliche SQLite-DB für jeden Test."""
    return DataStorage(db_path=tmp_path / "test.db")


ZEILE_A = {
    "collected_at": "2026-06-19T10:00:00+00:00",
    "pv_erzeugung_kw": 5.0,
    "netz_wert_kw": 2.0,
}

ZEILE_B = {
    "collected_at": "2026-06-19T11:00:00+00:00",
    "pv_erzeugung_kw": 6.0,
    "netz_wert_kw": 3.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# insert_row
# ─────────────────────────────────────────────────────────────────────────────

def test_insert_row_gibt_true_bei_neuer_zeile(db):
    assert db.insert_row(ZEILE_A) is True


def test_insert_row_gibt_false_bei_duplikat(db):
    db.insert_row(ZEILE_A)
    assert db.insert_row(ZEILE_A) is False


def test_insert_row_zeile_ist_in_db(db):
    db.insert_row(ZEILE_A)
    df = db.load_raw_df()
    assert len(df) == 1
    assert df["pv_erzeugung_kw"].iloc[0] == pytest.approx(5.0)


def test_insert_row_mehrere_zeilen(db):
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    assert len(db.load_raw_df()) == 2


# ─────────────────────────────────────────────────────────────────────────────
# load_raw_df
# ─────────────────────────────────────────────────────────────────────────────

def test_load_raw_df_leere_db_gibt_leeren_df(db):
    df = db.load_raw_df()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_load_raw_df_hat_erwartete_spalten(db):
    db.insert_row(ZEILE_A)
    df = db.load_raw_df()
    assert "collected_at" in df.columns
    assert "pv_erzeugung_kw" in df.columns
    assert "netz_wert_kw" in df.columns


def test_load_raw_df_ist_nach_zeitstempel_sortiert(db):
    db.insert_row(ZEILE_B)  # später zuerst einfügen
    db.insert_row(ZEILE_A)
    df = db.load_raw_df()
    # Muss aufsteigend sortiert sein
    assert df["collected_at"].iloc[0] < df["collected_at"].iloc[1]


# ─────────────────────────────────────────────────────────────────────────────
# insert_many
# ─────────────────────────────────────────────────────────────────────────────

def test_insert_many_fuegt_alle_ein(db):
    neu = db.insert_many([ZEILE_A, ZEILE_B])
    assert neu == 2
    assert len(db.load_raw_df()) == 2


def test_insert_many_ignoriert_duplikate(db):
    db.insert_row(ZEILE_A)
    neu = db.insert_many([ZEILE_A, ZEILE_B])
    # ZEILE_A ist Duplikat → nur ZEILE_B wird eingefügt
    assert neu == 1


# ─────────────────────────────────────────────────────────────────────────────
# rollup_tagesbilanz & gesamt_kwh_erzeugt
# ─────────────────────────────────────────────────────────────────────────────

def test_gesamt_kwh_erzeugt_null_bei_leerer_db(db):
    assert db.gesamt_kwh_erzeugt() == 0.0


def test_rollup_tagesbilanz_liefert_anzahl_tage(db):
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    tage = db.rollup_tagesbilanz()
    assert tage == 1  # beide Zeitstempel am selben Tag


def test_gesamt_kwh_erzeugt_nach_rollup(db):
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    db.rollup_tagesbilanz()
    # Trapezregel: (5 + 6) / 2 × 1 h = 5.5 kWh
    assert db.gesamt_kwh_erzeugt() == pytest.approx(5.5, abs=0.1)


# ─────────────────────────────────────────────────────────────────────────────
# prune
# ─────────────────────────────────────────────────────────────────────────────

def test_prune_loescht_rohzeilen(db):
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    geloescht = db.prune(tage=0)   # 0 Tage → alles weg
    assert geloescht == 2
    assert db.load_raw_df().empty


def test_prune_behaelt_tagesbilanz(db):
    """Nach dem Prunen muss gesamt_kwh_erzeugt aus tagesbilanz weiter funktionieren."""
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    db.prune(tage=0)
    assert db.gesamt_kwh_erzeugt() > 0.0

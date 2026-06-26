"""Unittests für components/storage.py (DataStorage)."""

import pandas as pd
import pytest

from components.storage import DataStorage, _to_utc_iso


@pytest.fixture
def db(tmp_path):
    """Isolierte SQLite-DB für jeden Test (eigene Datei je tmp_path)."""
    return DataStorage(db_path=tmp_path / "test.db")


def _zeile(ts, pv=10.0, netz=5.0):
    """Baut eine Messzeile. Default: Erzeugung > Verbrauch."""
    return {"collected_at": ts, "pv_erzeugung_kw": pv, "netz_wert_kw": netz}


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
# Zeitstempel-Normalisierung (Mikrosekunden -> Sekunden, UTC)
# ─────────────────────────────────────────────────────────────────────────────


def test_to_utc_iso_offset_wird_sekundengenau(db):
    assert _to_utc_iso("2026-06-19T08:12:52.457293+00:00") == "2026-06-19T08:12:52+00:00"


def test_to_utc_iso_naiv_als_lokalzeit(db):
    # 00:10 lokal (Sommer, CEST=UTC+2) -> 22:10 UTC am Vortag
    assert _to_utc_iso("2026-06-19T00:10:00") == "2026-06-18T22:10:00+00:00"


def test_normalisierung_macht_dedup_robust(db):
    # Mikrosekunden-Variante wie Alt-Bestand einschmuggeln, dann normalisieren
    with db._connect() as conn:
        conn.execute(
            "INSERT INTO messungen VALUES (?, ?, ?)",
            ("2026-06-19T08:00:00.123456+00:00", 10.0, 5.0),
        )
    assert db.normalize_timestamps() == 1
    # Jetzt wird derselbe Messpunkt als Duplikat erkannt
    assert db.insert_row(_zeile("2026-06-19T08:00:00.999+00:00")) is False


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
    # ZEILE_A ist Duplikat -> nur ZEILE_B wird eingefügt
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
    geloescht = db.prune(tage=0)  # 0 Tage -> alles weg
    assert geloescht == 2
    assert db.load_raw_df().empty


def test_prune_behaelt_tagesbilanz(db):
    """Nach dem Prunen muss gesamt_kwh_erzeugt aus tagesbilanz weiter funktionieren."""
    db.insert_row(ZEILE_A)
    db.insert_row(ZEILE_B)
    db.prune(tage=0)
    assert db.gesamt_kwh_erzeugt() > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# summen_seit & max_tageserzeugung (Dauer-Tabelle, überlebt Pruning)
# ─────────────────────────────────────────────────────────────────────────────


def test_summen_seit_und_eigen(db):
    for ts in ("2026-03-01T09:00:00+00:00", "2026-03-01T10:00:00+00:00"):
        db.insert_row(_zeile(ts, pv=10.0, netz=30.0))
    db.rollup_tagesbilanz()
    s = db.summen_seit("2026-01-01")
    assert s["erzeugt"] > 0
    assert s["verbraucht"] > s["erzeugt"]
    assert abs(s["eigen"] - s["erzeugt"]) < 1e-6  # Erzeugung komplett eigenverbraucht
    assert 0 < s["quote"] <= 100


def test_summen_seit_ueberlebt_prune(db):
    db.insert_row(_zeile("2026-03-01T09:00:00+00:00", pv=10.0, netz=30.0))
    db.insert_row(_zeile("2026-03-01T10:00:00+00:00", pv=10.0, netz=30.0))
    db.prune(tage=0)
    assert db.load_raw_df().empty
    assert db.summen_seit("2026-01-01")["erzeugt"] > 0  # aus tagesbilanz rekonstruiert


def test_max_tageserzeugung(db):
    assert db.max_tageserzeugung() == 0.0
    db.insert_row(_zeile("2026-03-01T09:00:00+00:00", pv=20.0, netz=5.0))
    db.insert_row(_zeile("2026-03-01T09:30:00+00:00", pv=20.0, netz=5.0))
    db.rollup_tagesbilanz()
    assert db.max_tageserzeugung() > 0.0

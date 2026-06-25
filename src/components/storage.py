"""Persistente Speicherung der PV-Daten in einer SQLite-Datenbank.

Zwei Tabellen:
- ``messungen``   : Rohwerte (Source of Truth). Werden nach RETENTION_TAGE gelöscht.
- ``tagesbilanz`` : vorberechnete Tagesaggregate. Bleiben dauerhaft erhalten,
                    damit Gesamt-kWh und Amortisierung das Prunen überleben.

Collector (data_module.py) schreibt Rohzeilen, das Dashboard (main.py) liest.
Geteilt wird die DB-Datei über das Docker-Volume; WAL-Mode erlaubt Lesen
während geschrieben wird.
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pandas as pd

import config
from components import formulas

logger = logging.getLogger(__name__)

# Roh-Rohdaten so lange aufheben; danach bleibt nur die Tagesbilanz.
RETENTION_TAGE = 90

DB_PATH = config.DATA_DIR / "pv_data.db"

_FELDNAMEN = ["collected_at", "pv_erzeugung_kw", "netz_wert_kw"]


def _to_utc_iso(zeitstempel: str) -> str:
    """Normalisiert einen ISO-Zeitstempel (mit beliebigem Offset) auf UTC-ISO.

    So sind String-Vergleiche in SQL DST-sicher (kein Mix aus +01:00/+02:00).
    """
    return (
        pd.Timestamp(zeitstempel)
        .tz_convert("UTC")
        .isoformat()
    )


class DataStorage:
    """Kapselt alle DB-Zugriffe. Beim Erzeugen wird das Schema sichergestellt."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messungen (
                    collected_at    TEXT PRIMARY KEY,
                    pv_erzeugung_kw REAL NOT NULL,
                    netz_wert_kw    REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tagesbilanz (
                    datum          TEXT PRIMARY KEY,
                    kwh_erzeugt    REAL NOT NULL,
                    kwh_verbraucht REAL NOT NULL,
                    bilanz_kwh     REAL NOT NULL,
                    aktualisiert   TEXT NOT NULL
                );
                """
            )
        logger.info("DB-Schema bereit: %s", self.db_path)

    # ── Schreiben (Collector) ────────────────────────────────────────────────
    def insert_row(self, zeile: dict) -> bool:
        """Hängt eine bereinigte Zeile an. Doppelte Zeitstempel werden ignoriert.

        Returns True, wenn die Zeile neu war (eingefügt), sonst False.
        """
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO messungen "
                "(collected_at, pv_erzeugung_kw, netz_wert_kw) VALUES (?, ?, ?)",
                (
                    _to_utc_iso(zeile["collected_at"]),
                    float(zeile["pv_erzeugung_kw"]),
                    float(zeile["netz_wert_kw"]),
                ),
            )
            return cur.rowcount > 0

    def insert_many(self, zeilen: list[dict]) -> int:
        """Fügt mehrere Zeilen ein (für die CSV-Migration). Returns: Anzahl neu."""
        with self._connect() as conn:
            cur = conn.executemany(
                "INSERT OR IGNORE INTO messungen "
                "(collected_at, pv_erzeugung_kw, netz_wert_kw) VALUES (?, ?, ?)",
                [
                    (
                        _to_utc_iso(z["collected_at"]),
                        float(z["pv_erzeugung_kw"]),
                        float(z["netz_wert_kw"]),
                    )
                    for z in zeilen
                ],
            )
            return cur.rowcount

    # ── Lesen (Dashboard) ────────────────────────────────────────────────────
    def load_raw_df(self) -> pd.DataFrame:
        """Liest alle Rohwerte als DataFrame – spaltenkompatibel zur alten CSV.

        Da Rohdaten nur RETENTION_TAGE zurückreichen, ist das bewusst klein.
        """
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT collected_at, pv_erzeugung_kw, netz_wert_kw "
                "FROM messungen ORDER BY collected_at",
                conn,
            )
        return df

    def gesamt_kwh_erzeugt(self) -> float:
        """Gesamte erzeugte kWh über die komplette Historie (aus tagesbilanz).

        Überlebt das Prunen der Rohdaten – Basis für die Amortisierung.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(kwh_erzeugt), 0.0) FROM tagesbilanz"
            ).fetchone()
        return float(row[0])

    # ── Aggregation & Retention ──────────────────────────────────────────────
    def rollup_tagesbilanz(self) -> int:
        """Berechnet die Tagesbilanz aus allen Rohdaten neu und schreibt sie weg.

        Nutzt dieselbe Logik wie das Dashboard (formulas), damit die Zahlen
        identisch sind. Returns: Anzahl aktualisierter Tage.
        """
        df = self.load_raw_df()
        if df.empty:
            return 0

        df_kwh = formulas.umrechnung_in_kwh(df)
        df_kwh["datum"] = (
            df_kwh["collected_at"].dt.tz_convert("Europe/Berlin").dt.date
        )
        summen = df_kwh.groupby("datum")[["kwh_erzeugt", "kwh_verbraucht"]].sum()
        summen["bilanz_kwh"] = summen["kwh_erzeugt"] - summen["kwh_verbraucht"]

        jetzt = datetime.now(timezone.utc).isoformat()
        rows = [
            (str(datum), r.kwh_erzeugt, r.kwh_verbraucht, r.bilanz_kwh, jetzt)
            for datum, r in summen.iterrows()
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO tagesbilanz "
                "(datum, kwh_erzeugt, kwh_verbraucht, bilanz_kwh, aktualisiert) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(datum) DO UPDATE SET "
                "  kwh_erzeugt=excluded.kwh_erzeugt, "
                "  kwh_verbraucht=excluded.kwh_verbraucht, "
                "  bilanz_kwh=excluded.bilanz_kwh, "
                "  aktualisiert=excluded.aktualisiert",
                rows,
            )
        logger.info("Tagesbilanz aktualisiert: %d Tage", len(rows))
        return len(rows)

    def prune(self, tage: int = RETENTION_TAGE) -> int:
        """Löscht Rohwerte älter als ``tage``. Aggregiert vorher zur Sicherheit.

        Reihenfolge ist wichtig: erst rollup (Tage finalisieren), dann löschen.
        Returns: Anzahl gelöschter Rohzeilen.
        """
        self.rollup_tagesbilanz()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=tage)).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM messungen WHERE collected_at < ?", (cutoff,)
            )
            geloescht = cur.rowcount
        if geloescht:
            logger.info("Retention: %d Rohzeilen (<%d Tage) gelöscht", geloescht, tage)
        return geloescht


def migrate_csv(csv_path=config.CSV_PATH, db_path=DB_PATH) -> None:
    """Einmalige Migration: liest die alte cleaned_data.csv in die DB."""
    storage = DataStorage(db_path)
    df = pd.read_csv(csv_path)
    zeilen = df[_FELDNAMEN].to_dict("records")
    neu = storage.insert_many(zeilen)
    tage = storage.rollup_tagesbilanz()
    logger.info("Migration fertig: %d Rohzeilen, %d Tage aggregiert", neu, tage)
    print(f"Migration fertig: {neu} neue Rohzeilen, {tage} Tage aggregiert.")


if __name__ == "__main__":
    from logging_setup import setup_logging

    setup_logging(config.LOG_FILE)
    migrate_csv()
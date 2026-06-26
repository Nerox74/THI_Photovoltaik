"""Persistente Speicherung der PV-Daten in einer SQLite-Datenbank.

ÜBERARBEITETE FASSUNG – Drop-in-Ersatz für storage.py.
Enthält die Korrekturen aus dem Review:

  (1) Retention prunt jetzt auf TAGESGRENZEN (lokale Mitternacht). Ein Tag ist
      dadurch immer entweder vollständig in den Rohdaten oder ganz weg – nie
      halb. Das verhindert, dass ein bereits finalisierter Tageswert beim
      nächsten Rollup durch einen unvollständigen Teilwert überschrieben wird.

  (2) _to_utc_iso ist robust gegen zeitzonenlose ("naive") Zeitstempel:
      ein fehlender Offset wird definiert als LOKALE_ZEITZONE interpretiert,
      statt mit TypeError abzustürzen.

  (3) Zeitstempel werden einheitlich auf Sekunden gerundet als UTC-ISO
      abgelegt; der Retention-Cutoff nutzt denselben Erzeuger. Dadurch sind
      lexikografische SQL-Vergleiche (ORDER BY / WHERE <) eindeutig.

  (Doku) RETENTION_TAGE wird aus config gelesen, falls dort definiert
      (Fallback 90), damit der Wert nicht an zwei Orten driften kann.

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
from datetime import datetime, timezone

import pandas as pd

import config
from components import formulas

logger = logging.getLogger(__name__)

# Lokale Zeitzone, in der Tagesgrenzen gebildet werden (Mitternacht = Tagesanfang).
LOKALE_ZEITZONE = "Europe/Berlin"

# Roh-Rohdaten so lange aufheben; danach bleibt nur die Tagesbilanz.
# Bevorzugt aus config (Single Source of Truth), Fallback 90 Tage.
RETENTION_TAGE = int(getattr(config, "RETENTION_TAGE", 90))

DB_PATH = config.DATA_DIR / "pv_data.db"

_FELDNAMEN = ["collected_at", "pv_erzeugung_kw", "netz_wert_kw"]


def _to_utc_iso(zeitstempel: str) -> str:
    """Normalisiert einen ISO-Zeitstempel auf UTC-ISO (auf Sekunden gerundet).

    - Zeitzonen-behaftete Eingaben (mit Offset) werden nach UTC umgerechnet.
    - "Naive" Eingaben (ohne Offset) werden als LOKALE_ZEITZONE interpretiert,
      statt mit TypeError abzustürzen.
    - Das Ergebnis ist auf Sekunden gerundet, damit alle gespeicherten Werte
      identisch breit sind und String-Vergleiche in SQL eindeutig bleiben.
    """
    ts = pd.Timestamp(zeitstempel)
    if ts.tz is None:
        # Kein Offset geliefert -> als lokale Zeit interpretieren.
        ts = ts.tz_localize(LOKALE_ZEITZONE)
    return ts.tz_convert("UTC").floor("s").isoformat()


def _cutoff_utc_iso(tage: int) -> str:
    """Tagesgrenzen-Cutoff für die Retention.

    Liefert die lokale Mitternacht von 'vor `tage` Tagen' als UTC-ISO.
    Damit löscht DELETE ... < cutoff nur VOLLSTÄNDIG abgelaufene Tage und
    zerschneidet niemals einen Tag in der Mitte.
    """
    grenze_lokal = pd.Timestamp.now(tz=LOKALE_ZEITZONE).normalize() - pd.Timedelta(
        days=tage
    )
    return grenze_lokal.tz_convert("UTC").floor("s").isoformat()


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
            conn.executescript("""
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
                """)
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

        Hinweis: Durch die tagesgenaue Retention (prune) liegen in den Rohdaten
        nur noch vollständige Tage (plus der laufende, noch unvollständige
        heutige Tag). Dadurch ist das vollständige Neuberechnen hier sicher –
        es kann keinen bereits finalisierten Tag durch einen Teilwert ersetzen.
        """
        df = self.load_raw_df()
        if df.empty:
            return 0

        df_kwh = formulas.umrechnung_in_kwh(df)
        df_kwh["datum"] = df_kwh["collected_at"].dt.tz_convert(LOKALE_ZEITZONE).dt.date
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
        """Löscht Rohwerte älter als ``tage`` (auf TAGESGRENZEN).

        Reihenfolge ist wichtig: erst rollup (Tage finalisieren), dann löschen.
        Der Cutoff ist die lokale Mitternacht vor ``tage`` Tagen – es werden
        nur vollständig abgelaufene Tage entfernt, nie ein Tag mittendrin.
        Returns: Anzahl gelöschter Rohzeilen.
        """
        self.rollup_tagesbilanz()
        cutoff = _cutoff_utc_iso(tage)
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM messungen WHERE collected_at < ?", (cutoff,))
            geloescht = cur.rowcount
        if geloescht:
            logger.info("Retention: %d Rohzeilen (vor %s) gelöscht", geloescht, cutoff)
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

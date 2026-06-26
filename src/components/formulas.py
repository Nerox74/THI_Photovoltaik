"""Hier werden Berechnungen durchgeführt, deren Ergebnisse in mehreren Files benötigt werden."""

# Imports
import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def umrechnung_in_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rechnet kW-Messwerte (mit Zeitstempel) in kWh um — via Trapezregel (Integral).

    Formel: kWh = ∫ P(t) dt  ≈  Σ (P_i + P_{i+1}) / 2 × Δt

    Datenlücken (z. B. wenn der Collector-PC aus war) werden NICHT mitintegriert:
    Intervalle, die länger als config.MAX_LUECKE_H sind, tragen 0 kWh bei, statt
    die letzte gemessene Leistung über messfreie Stunden hochzurechnen.

    Eingabe (df) muss folgende Spalten haben:
        collected_at       → Zeitstempel (datetime)
        pv_erzeugung_kw    → erzeugte Leistung in kW
        netz_wert_kw       → verbrauchte Leistung in kW

    Rückgabe: df mit zusätzlichen Spalten:
        delta_h            → Zeitdifferenz zum nächsten Messwert in Stunden
        kwh_erzeugt        → erzeugte kWh im Intervall
        kwh_verbraucht     → verbrauchte kWh im Intervall
    """
    df = df.copy()
    df["collected_at"] = pd.to_datetime(df["collected_at"], utc=True)
    df = df.sort_values("collected_at").reset_index(drop=True)

    # Zeitdifferenz in Stunden zwischen zwei Messpunkten
    df["delta_h"] = df["collected_at"].diff().dt.total_seconds().shift(-1) / 3600

    # Datenlücken nicht mitintegrieren (sonst Hochrechnung über messfreie Stunden)
    anzahl_luecken = int((df["delta_h"] > config.MAX_LUECKE_H).sum())
    if anzahl_luecken:
        logger.warning(
            "%d Datenlücken übersprungen (>%.0f Min)",
            anzahl_luecken,
            config.MAX_LUECKE_H * 60,
        )
    df.loc[df["delta_h"] > config.MAX_LUECKE_H, "delta_h"] = 0

    # Trapezregel: (P_i + P_{i+1}) / 2 × Δt
    df["kwh_erzeugt"] = (
        (df["pv_erzeugung_kw"] + df["pv_erzeugung_kw"].shift(-1)) / 2 * df["delta_h"]
    )
    df["kwh_verbraucht"] = (
        (df["netz_wert_kw"] + df["netz_wert_kw"].shift(-1)) / 2 * df["delta_h"]
    )

    return df


def differenz_erzeugt_verbraucht(df: pd.DataFrame) -> pd.Series:
    """
    Berechnet die tägliche Bilanz (Erzeugung − Verbrauch) in kWh.

    Positiv (+) → Überschuss: mehr erzeugt als verbraucht  → grün im Kalender
    Negativ (−) → Defizit:    mehr verbraucht als erzeugt  → rot im Kalender

    Rückgabe: pd.Series mit
        Index  → Datum (ein Eintrag pro Tag)
        Values → Differenz in kWh (direkt verwendbar für den Kalender)
    """
    df = umrechnung_in_kwh(df)

    # Datum extrahieren (ohne Uhrzeit, ohne Zeitzone)
    df["datum"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.date

    # Pro Tag summieren, dann Differenz bilden (vektorisiert statt groupby.apply)
    summen = df.groupby("datum")[["kwh_erzeugt", "kwh_verbraucht"]].sum()
    tagesbilanz = summen["kwh_erzeugt"] - summen["kwh_verbraucht"]
    tagesbilanz.index = pd.to_datetime(tagesbilanz.index)
    tagesbilanz.name = "bilanz_kwh"

    logger.debug("Tägliche Bilanz berechnet für %d Tage", len(tagesbilanz))
    for datum, wert in tagesbilanz.items():
        status = "Überschuss" if wert >= 0 else "Defizit"
        logger.debug("  %s  %+.4f kWh  %s", datum.date(), wert, status)

    return tagesbilanz

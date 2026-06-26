"""Hier werden Berechnungen durchgeführt, deren Ergebnisse in mehreren Files benötigt werden."""

import logging

import pandas as pd

import config

logger = logging.getLogger(__name__)


def umrechnung_in_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rechnet kW-Messwerte (mit Zeitstempel) in kWh um — via Trapezregel (Integral).

    Formel: kWh = ∫ P(t) dt  ≈  Σ (P_i + P_{i+1}) / 2 × Δt

    Datenlücken (> config.MAX_LUECKE_H) tragen 0 kWh bei, statt die letzte Leistung
    über messfreie Stunden hochzurechnen.

    Eingabe-Spalten: collected_at, pv_erzeugung_kw, netz_wert_kw
    Zusätzliche Ausgabe-Spalten:
        delta_h         → Zeitdifferenz zum nächsten Messwert (h)
        kwh_erzeugt     → erzeugte kWh im Intervall
        kwh_verbraucht  → verbrauchte kWh im Intervall
        kwh_pv_eigen    → direkt aus PV gedeckter Verbrauch (kWh) = ∫ min(Erz., Verbr.)
    """
    df = df.copy()
    df["collected_at"] = pd.to_datetime(df["collected_at"], format="ISO8601", utc=True)
    df = df.sort_values("collected_at").reset_index(drop=True)

    df["delta_h"] = df["collected_at"].diff().dt.total_seconds().shift(-1) / 3600

    anzahl_luecken = int((df["delta_h"] > config.MAX_LUECKE_H).sum())
    if anzahl_luecken:
        logger.warning(
            "%d Datenlücken übersprungen (>%.0f Min)",
            anzahl_luecken,
            config.MAX_LUECKE_H * 60,
        )
    df.loc[df["delta_h"] > config.MAX_LUECKE_H, "delta_h"] = 0

    df["kwh_erzeugt"] = (
        (df["pv_erzeugung_kw"] + df["pv_erzeugung_kw"].shift(-1)) / 2 * df["delta_h"]
    )
    df["kwh_verbraucht"] = (
        (df["netz_wert_kw"] + df["netz_wert_kw"].shift(-1)) / 2 * df["delta_h"]
    )

    # Eigenverbrauch aus PV: momentane Leistung = min(Erzeugung, Verbrauch), integriert
    eigen_kw = df[["pv_erzeugung_kw", "netz_wert_kw"]].min(axis=1)
    df["kwh_pv_eigen"] = (eigen_kw + eigen_kw.shift(-1)) / 2 * df["delta_h"]

    return df


def _zeitraum_start_utc(zeitraum: str) -> pd.Timestamp:
    """Startgrenze (UTC) für 'Tag' (ab Mitternacht), 'Monat' (ab dem 1.) und 'Jahr' (ab 1.1.).

    Grenzen werden in Europe/Berlin gebildet, damit z. B. der 'Tag' an der lokalen
    Mitternacht beginnt – nicht an der UTC-Mitternacht.
    """
    jetzt_berlin = pd.Timestamp.now(tz="Europe/Berlin")
    if zeitraum == "Tag":
        start = jetzt_berlin.normalize()
    elif zeitraum == "Monat":
        start = jetzt_berlin.normalize().replace(day=1)
    elif zeitraum == "Jahr":
        start = jetzt_berlin.normalize().replace(month=1, day=1)
    else:
        raise ValueError(f"Unbekannter Zeitraum: {zeitraum}")
    return start.tz_convert("UTC")


def summen_zeitraum(df_kwh: pd.DataFrame, zeitraum: str) -> dict:
    """Aggregiert Erzeugung/Verbrauch/PV-Eigenverbrauch (kWh) für 'Tag' | 'Monat' | 'Jahr'.

    Erwartet ein DataFrame, das bereits durch umrechnung_in_kwh gelaufen ist.

    Returns dict:
        erzeugt    → erzeugte kWh im Zeitraum
        verbraucht → verbrauchte kWh im Zeitraum
        eigen      → davon direkt aus PV gedeckt (kWh)
        netz       → aus dem Netz bezogen (kWh) = verbraucht − eigen
        quote      → Anteil Verbrauch aus PV am Gesamtverbrauch (%)
    """
    start = _zeitraum_start_utc(zeitraum)
    teil = df_kwh.loc[df_kwh["collected_at"] >= start]

    erzeugt = float(teil["kwh_erzeugt"].sum())
    verbraucht = float(teil["kwh_verbraucht"].sum())
    eigen = float(teil["kwh_pv_eigen"].sum())
    quote = (eigen / verbraucht * 100.0) if verbraucht > 0 else 0.0

    return {
        "erzeugt": erzeugt,
        "verbraucht": verbraucht,
        "eigen": eigen,
        "netz": max(verbraucht - eigen, 0.0),
        "quote": quote,
    }


def differenz_erzeugt_verbraucht(df: pd.DataFrame) -> pd.Series:
    """
    Berechnet die tägliche Bilanz (Erzeugung − Verbrauch) in kWh.

    Positiv (+) → Überschuss, Negativ (−) → Defizit.
    Rückgabe: pd.Series, Index = Datum, Values = Differenz in kWh.
    """
    df = umrechnung_in_kwh(df)
    df["datum"] = df["collected_at"].dt.tz_convert("Europe/Berlin").dt.date

    summen = df.groupby("datum")[["kwh_erzeugt", "kwh_verbraucht"]].sum()
    tagesbilanz = summen["kwh_erzeugt"] - summen["kwh_verbraucht"]
    tagesbilanz.index = pd.to_datetime(tagesbilanz.index)
    tagesbilanz.name = "bilanz_kwh"

    logger.debug("Tägliche Bilanz berechnet für %d Tage", len(tagesbilanz))
    for datum, wert in tagesbilanz.items():
        status = "Überschuss" if wert >= 0 else "Defizit"
        logger.debug("  %s  %+.4f kWh  %s", datum.date(), wert, status)

    return tagesbilanz

"""Hier werden Berechnungen durchgeführt, deren Ergebnis in mehreren Files benötigt werden"""


# Imports
import pandas as pd
import numpy as np



# Konstante Strompreis
STROMPREIS: float = 0.39
ANSCHAFFUNGSKOSTEN_PV_ANLAGE: float = 15_000.0  # Muss noch recherchiert werden


def umrechnung_in_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rechnet kW-Messwerte (mit Zeitstempel) in kWh um — via Trapezregel (Integral).

    Formel: kWh = ∫ P(t) dt  ≈  Σ (P_i + P_{i+1}) / 2 × Δt

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

    # Pro Tag summieren
    tagesbilanz = df.groupby("datum").apply(
        lambda g: g["kwh_erzeugt"].sum() - g["kwh_verbraucht"].sum()
    )
    tagesbilanz.index = pd.to_datetime(tagesbilanz.index)
    tagesbilanz.name = "bilanz_kwh"

    print("Tägliche Bilanz (Erzeugung − Verbrauch):")
    for datum, wert in tagesbilanz.items():
        symbol = "✅ Überschuss" if wert >= 0 else "❌ Defizit"
        print(f"  {datum.date()}  {wert:+.4f} kWh  {symbol}")

    return tagesbilanz


"""Hier werden Berechnungen durchgeführt, deren Ergebnis in mehreren Files benötigt werden"""

# Imports
import THI_Photovoltaik.src.data_module

# Konstante Strompreis
STROMPREIS: float = 0.39
ANSCHAFFUNGSKOSTEN_PV_ANLAGE: float = 15_000.0  # Muss noch recherchiert werden


def umrechnung_in_kwh(strom_in_watt: float) -> float:
    """
    Hier wird Watt in Kilowattstunde umgerechnet. Dies kann durch das Integral berechnet werden.
    Wir benötigen die erzeugte KwH:

    Pro Stunde

    Pro Tag

    Pro Woche

    Pro Monat

    Pro Jahr

    """


def differenz_erzeugt_verbraucht(
    strom_erzeugt: float, strom_verbraucht: float
) -> float:
    """
    Hier wird die Differenz zwischen dem erzeugten Strom und dem Strom der verbraucht worden ist berechnet. Es werden gleich die Werte von umrechnung_in_kwh weitergerechnet.

    """

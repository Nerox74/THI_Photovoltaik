"""
Hier werden zentrale Zahlen und Fakten in Streamlit dargestellt, die im Dashboard angezeigt werden.

1.Vergleich: Strompreiskosten wie viel Hergestellt --> wie viel Geld wird gespart --> Api verbindung mit aktuellen Strompreis
2.Aktuelle Stromherstellung, an diesem einen Tag, pro Monat und wie viel schon im Jahr hergestellt worden ist.
3.Balken zu wie viel Prozent sich die Anlage schon abbezahl hat, oder CO2 Ersparnis dadurch

"""

# Imports


def tagesumme_erzeugter_strom() -> None:
    """
    Hier wird der kummulierte erzeugte Strom pro Tag angezeigt. Die Berechnung wird in formulas durchgeführt.
    Dargestellt in einem Rechteck.

    """


def ersparnis_durch_pv() -> None:
    """
    Darstellung des durch die PV-Anlage eingesparten Geld.
    Auswahl in Dropdownmenü, ob man die Ersparnis am Tag, Woche, Monat, oder im bisherigen Jahr sehen möchte. Hierfür muss überprüft werden, ob jeweils für die Zeiteinheiten überhaupt Daten vorhandne sind
    Die Ersparnis wird in einem Rechteck angezeigt.
    params: Strompreis(konstante)

    """


def auslastung_pv() -> None:
    """

    Anzeige der Auslastung der PV-Anlage in einem Kreisdiagram. 100% entspricht was eine PV-Anlage maximal an einem Tag produzieren kann.
    Es wird prozentual angegeben wie viel von den maximal produzierbar möglichen schon erreicht worden ist.
    Ziel(Darstellung): Ähnlichkeiten zu Tacho im Auto

    """


def amortisierung_pv() -> None:
    """

    Zeigt einen Balken an. Dieser ist mit grüner Farbe gefüllt jedoch nur Prozentual und in der Mitte von diesen steht eine Prozentzahl. Diese Prozentzahl und die Länge des grünen Balkens im verhältnis zur Gesamtlänge des Rechteckes zeigt an,
    zu wie viel Prozent die PV anlage sich schon amorisiert hat. Heißt, Anschaffung der PV-Anlage und Größe ist bekannt --> ungefähre kosten sind bekannt.
    Berechnung wie viel Stromkosten durch die PV-Anlage schon eingespart worden sind (

    Rechnung: Strompreis multipliziert mit erzeugnis seit Beschaffung --> Prozentzahl wie viel ist das von den Gesamtkosten der Anschaffung

    --> Berechnung findet 1 mal am Tag statt um 9 Uhr

    """


def show_kpis() -> None:
    """
    Rendert alle KPIS in Boxen im Streamlit dashboard

    """

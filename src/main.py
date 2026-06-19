"""Hier wird das Dashboard erzeugt. Es werden alle anderen Python Files hier importiert und verwendet, um
das Dashboard über Streamlit zu erzeugen."""

# Imports
from formulas import differenz_erzeugt_verbraucht
from charts import draw_calendar, create_chart_balkendiagramm

def streamlit_app() -> None:
    """

    Hier wird die Streamlit App final erstellt. Die einzelnen Komponenten, die erstellt worden sind,
    werden hier verwendet und zu einem Konstrukt zusammengebaut. Also alle components werden hier zum finalen Dashboard zusammengebaut


    """

"""Unittests für main.py.
streamlit_app() selbst ist nicht testbar ohne laufende Streamlit-Session,
daher prüfen wir den Modulaufbau und die Konstanten."""

from pathlib import Path


def test_csv_path_ist_ein_path_objekt():
    import main
    assert isinstance(main.CSV_PATH, Path)


def test_streamlit_app_ist_aufrufbar():
    import main
    # Prüft, dass streamlit_app als Funktion existiert
    assert callable(main.streamlit_app)


def test_streamlit_app_hat_docstring():
    import main
    assert main.streamlit_app.__doc__ is not None
    assert len(main.streamlit_app.__doc__) > 0


def test_year_und_unit_werden_aus_charts_importiert():
    # YEAR und UNIT werden in main aus charts importiert und müssen vorhanden sein
    from components.charts import UNIT, YEAR
    assert isinstance(YEAR, int)
    assert isinstance(UNIT, str)
    assert UNIT == "kWh"
"""Unittests für main.py.

streamlit_app() selbst ist nicht testbar ohne laufende Streamlit-Session,
daher prüfen wir den Modulaufbau, Importe und aufrufbare Funktionen.
"""

import main


def test_streamlit_app_ist_aufrufbar():
    """streamlit_app muss als Funktion existieren und aufrufbar sein."""
    assert callable(main.streamlit_app)


def test_streamlit_app_hat_docstring():
    assert main.streamlit_app.__doc__ is not None
    assert len(main.streamlit_app.__doc__) > 0


def test_show_dashboard_content_ist_aufrufbar():
    """show_dashboard_content muss als Funktion existieren."""
    assert callable(main.show_dashboard_content)


def test_config_wird_importiert():
    """config muss im main-Modul verfügbar sein."""
    import config

    assert config.UNIT == "kWh"
    assert isinstance(config.HEADER_REFRESH_S, int)


def test_header_refresh_ist_eine_minute():
    """Nach unserer Änderung muss der Refresh-Intervall 60 Sekunden betragen."""
    import config

    assert config.HEADER_REFRESH_S == 60

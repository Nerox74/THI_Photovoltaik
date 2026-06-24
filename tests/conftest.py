"""Wird von pytest automatisch vor den Tests geladen.
Setzt einen Dummy-API-Key, damit data_module beim Import nicht abstürzt
(dort wird HEADERS schon beim Import aus API_KEY gebaut)."""

import os

# setdefault = nur setzen, falls noch nicht vorhanden (überschreibt echte Keys nicht)
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("JUPYTER_HUB_URL", "https://example.com/data")
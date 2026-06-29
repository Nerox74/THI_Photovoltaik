FROM python:3.11-slim AS base
LABEL authors="nilsschaftlein"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN useradd -m app

# Dependencies zuerst (Layer-Caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Code danach
COPY --chown=app:app ./src ./src

# Beschreibbare Verzeichnisse für Nicht-Root-User
ENV STREAMLIT_HOME=/app/.streamlit
RUN mkdir -p /app/.streamlit /app/data && chown -R app:app /app

USER app

# ── Dashboard ────────────────────────────────────────────────
FROM base AS dashboard
EXPOSE 8502
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1
ENTRYPOINT ["streamlit", "run"]
CMD ["src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ── Collector ────────────────────────────────────────────────
FROM base AS collector
ENTRYPOINT ["python", "-u", "src/data_module.py"]

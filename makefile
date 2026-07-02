# THI Photovoltaik – lokale Starts (ohne Docker) UND Docker-Compose-Orchestrierung
#   make        -> Hilfe
#   make dev    -> Backend + Frontend lokal parallel
#   make up     -> beide via Docker Compose
# Python überschreibbar:  make backend PY=python3

PY ?= python

.DEFAULT_GOAL := help
.PHONY: help backend frontend dev up up-backend up-frontend down logs build

help:  ## Diese Hilfe anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

# ── Lokal (ohne Docker) ──────────────────────────────
backend:  ## Nur Backend (Datensammler) lokal starten
	$(PY) src/data_module.py

frontend:  ## Nur Frontend (Dashboard) lokal starten
	streamlit run src/main.py

dev:  ## Backend + Frontend lokal parallel (Ctrl-C stoppt beide)
	@trap 'kill 0' EXIT; \
	$(PY) src/data_module.py & \
	streamlit run src/main.py

# ── Docker Compose ───────────────────────────────────
build:  ## Container-Images bauen
	docker compose build

up:  ## Beide Services starten
	docker compose up -d --build

up-backend:  ## Nur Backend-Container
	docker compose up -d collector

up-frontend:  ## Nur Frontend-Container
	docker compose up -d dashboard

down:  ## Stack stoppen und entfernen
	docker compose down

logs:  ## Logs aller Container folgen
	docker compose logs -f
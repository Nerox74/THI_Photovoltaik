FROM python:3.11-slim
LABEL authors="nilsschaftlein"

#Umgebungsvariabelen
#prints werden sofort angezeigt nicht verzögert
ENV PYTHONUNBUFFERED=1
#Führe den Code aus --° nicht in Pycahche speichern
ENV PYTHONDONTWRITEBYTECODE=1


WORKDIR /app

#-m Erstellt im Home-Direcotry benutzer für homme/app
#chown ändert besitzer einer Datei -R Ändere den Besitzer des Ordners
RUN useradd -m app && chown -R app:app /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY --chown=app:app ./src ./src

#wird nicht mehr als root ausgeführt sondern als app
USER app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run"]

CMD ["src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]










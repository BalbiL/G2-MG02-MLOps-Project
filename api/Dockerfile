FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
COPY api/api_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code API et de la config
COPY api/ ./api/
COPY api_config.py .

EXPOSE 8000

# Lancement avec uvicorn en mode module
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
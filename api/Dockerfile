# api/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY api/api_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY api_config.py .

EXPOSE 8000

# --- FIX IMPORT ---
# Ajoute /app/api au chemin de recherche Python pour que 'import database' fonctionne
ENV PYTHONPATH="${PYTHONPATH}:/app/api"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
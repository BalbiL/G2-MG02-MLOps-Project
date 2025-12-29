# ml/Dockerfile
FROM python:3.9-slim

# On commence à la racine pour l'installation des dépendances
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY ml/new_inference_req.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le dossier ML vers /app/ml
COPY ml/ ./ml/

# On change le dossier de travail pour se placer dans le dossier ml
WORKDIR /app/ml

EXPOSE 9000

ENV PYTHONPATH="${PYTHONPATH}:/app/ml"

# On lance uvicorn
CMD ["uvicorn", "model_api:app", "--host", "0.0.0.0", "--port", "9000"]
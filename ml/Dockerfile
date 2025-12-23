# ml/Dockerfile
FROM python:3.9-slim

# On commence à la racine pour l'installation des dépendances
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY ml/new_inference_req.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le dossier ML vers /app/ml
COPY ml/ ./ml/

# --- CORRECTION ICI ---
# On change le dossier de travail pour se placer DANS le dossier ml
WORKDIR /app/ml

EXPOSE 9000

# Le PYTHONPATH n'est plus strictement nécessaire si on est dans le dossier, 
# mais on peut le garder par sécurité ou le simplifier.
ENV PYTHONPATH="${PYTHONPATH}:/app/ml"

# On lance uvicorn directement sur 'model_api:app' (et non plus 'ml.model_api:app')
# car nous sommes déjà dans le dossier qui contient model_api.py
CMD ["uvicorn", "model_api:app", "--host", "0.0.0.0", "--port", "9000"]
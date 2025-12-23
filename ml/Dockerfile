FROM python:3.9-slim

WORKDIR /app

# Installation des outils de build (parfois nécessaire pour certaines libs ML)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Installation des dépendances
COPY ml/new_inference_req.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie de TOUT le dossier ml (y compris vos fichiers modèles locaux !)
COPY ml/ ./ml/
# Note: Si vos modèles sont très lourds, le build peut être long.
# Une alternative est d'utiliser un volume docker-compose, voir plus bas.

EXPOSE 9000

CMD ["uvicorn", "ml.model_api:app", "--host", "0.0.0.0", "--port", "9000"]
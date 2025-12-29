FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
COPY frontend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code frontend
COPY frontend/ ./frontend/
# Copie du fichier de config partagé 
COPY api_config.py .

# Streamlit tourne par défaut sur 8501
EXPOSE 8501

# On lance depuis la racine pour que les imports python fonctionnent
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
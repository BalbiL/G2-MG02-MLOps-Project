# ml/tests/test_ml.py
from fastapi.testclient import TestClient
import sys
import os

# Hack pour importer model_api qui est dans le dossier parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# On doit mocker les imports lourds (tensorflow) avant d'importer l'app
from unittest.mock import MagicMock
sys.modules["new_inference"] = MagicMock()
sys.modules["database_connection"] = MagicMock()

from model_api import app

client = TestClient(app)

def test_health_check():
    """Test basique que le conteneur est en vie"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "model_loaded": True}

def test_recommend_validation_error():
    """Vérifie que l'API refuse une requête sans user_id"""
    payload = {
        "user_history": ["N123"]
        # user_id manquant
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 422 # Erreur de validation FastAPI
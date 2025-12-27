# api/tests/test_api.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Ajout du dossier parent au path pour importer 'main'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

# TU: Vérifier que l'API démarre

def test_get_news_by_id_success():
    # On "patch" l'objet supabase importé dans api.main
    with patch("main.supabase") as mock_supabase:
        # On configure le mock pour qu'il renvoie ce qu'on veut
        mock_response = MagicMock()
        mock_response.data = [{"id": "N123", "title": "Test News", "category": "test", "subcategory": "sub", "abstract": "desc", "inserted_at": "2023-01-01T00:00:00"}]
        
        # Enchainement des méthodes de Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        response = client.get("/news/N123")
        
        assert response.status_code == 200
        assert response.json()["title"] == "Test News"

def test_get_news_not_found():
    with patch("main.supabase") as mock_supabase:
        # Cas où la liste renvoyée est vide
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        response = client.get("/news/N99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "News not found"
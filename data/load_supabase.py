import os
import json
import requests
import pandas as pd
from supabase import create_client, Client
from tqdm import tqdm

# Récupération des variables d'environnement
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Les variables SUPABASE_URL et SUPABASE_KEY sont requises.")

# Client pour le check de sécurité
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_data_safely(df: pd.DataFrame, table_name="news"):
    print(f"--- Étape Load (Sécurisée) ---")
    
    # 1. SAFETY CHECK : On vérifie si la table contient déjà des données
    try:
        # On demande le count exact sans récupérer les données (head=True)
        response = supabase.table(table_name).select("*", count="exact", head=True).execute()
        existing_count = response.count
        print(f"Nombre d'articles actuels dans la table '{table_name}' : {existing_count}")
        
        # SEUIL DE SÉCURITÉ : Si plus de 100 articles, on considère que c'est déjà fait.
        # Le dataset MIND contient > 100k lignes, donc 100 est une marge sûre.
        if existing_count > 100:
            print(" La table est déjà peuplée. Aucune action requise.")
            print(">> Le script s'arrête ici pour protéger les données existantes.")
            return

    except Exception as e:
        print(f"Erreur lors de la vérification de la table : {e}")
        return

    # 2. Insertion (Logique notebook cell 59)
    print("Table vide détectée. Lancement de l'insertion...")
    
    # Préparation des headers comme dans le notebook
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        # Optionnel : header pour ignorer les erreurs de doublons si besoin
        "Prefer": "resolution=ignore-duplicates" 
    }
    
    # Endpoint REST
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    records = df.to_dict(orient="records")
    batch_size = 500
    
    print(f"Insertion de {len(records)} lignes par batch de {batch_size}...")

    for i in tqdm(range(0, len(records), batch_size)):
        batch = records[i : i + batch_size]
        try:
            # POST via requests comme dans le notebook
            response = requests.post(url, headers=headers, data=json.dumps(batch))
            
            if response.status_code not in (200, 201):
                print(f"Erreur sur le batch {i}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception sur le batch {i}: {e}")

    print("Chargement terminé.")

if __name__ == "__main__":
    pass
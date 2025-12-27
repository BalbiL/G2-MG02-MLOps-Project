import os
import shutil
import json
import zipfile
import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_recommenders as tfrs
from tensorflow.keras.layers import StringLookup, TextVectorization, Embedding, GRU, Dense
import gdown
import boto3

# --- 1. CONFIGURATION EXACTE DU NOTEBOOK ---
SAMPLE_SIZE = 200000        # Comme demandé par la doc du collègue
EMBEDDING_DIM = 64          # Dimension des vecteurs
MAX_HISTORY_LENGTH = 30     # Historique max
MAX_TOKENS = 20000          # Vocabulaire titre
TITLE_VEC_DIM = 100         # Longueur seq titre
BATCH_SIZE = 128
EPOCHS = 3                  # Comme dans le notebook
LEARNING_RATE = 0.1         # Adagrad par défaut souvent à 0.01 ou 0.1

# Configuration S3
BUCKET_NAME = "s3-g2-mg02-testing"  
REGION_NAME = "us-east-1"

# --- 2. TÉLÉCHARGEMENT & PRÉPARATION (Data Pipeline intégré) ---
def prepare_data():
    print(">>> [1/5] Téléchargement des données...")
    # ID du dataset MIND Large (identique au notebook)
    file_id = "1GffOYmcAMP17oi2BwC7Dp4l5F7rEjHRr"
    url = f"https://drive.google.com/uc?id={file_id}"
    output_zip = "mind_large.zip"
    
    if not os.path.exists(output_zip):
        gdown.download(url, output_zip, quiet=False)
        
    if not os.path.exists("mind_large"):
        with zipfile.ZipFile(output_zip, 'r') as z:
            z.extractall(".")

    print(">>> [2/5] Nettoyage et Création du Dataset...")
    # Chargement News
    news_cols = ["id", "category", "subcategory", "title", "abstract", "url", "t_ents", "a_ents"]
    news = pd.read_csv("mind_large/news_train.tsv", sep="\t", names=news_cols)
    news = news.drop_duplicates(subset=["id"])
    news["title"] = news["title"].fillna("No Title")
    news["category"] = news["category"].fillna("unknown")
    
    # Chargement Behaviors
    beh_cols = ["imp_id", "user_id", "time", "history", "impressions"]
    behaviors = pd.read_csv("mind_large/behaviors_train.tsv", sep="\t", names=beh_cols)
    
    # Filtrage strict (Logique notebook)
    behaviors["history"] = behaviors["history"].fillna("")
    mask = (
        (behaviors["impressions"].str.contains("-1")) & # Au moins 1 clic
        (behaviors["history"].str.len() > 0)            # Historique non vide
    )
    behaviors = behaviors[mask]
    
    # Sampling respectueux
    if len(behaviors) > SAMPLE_SIZE:
        behaviors = behaviors.sample(n=SAMPLE_SIZE, random_state=42)
        
    print(f"    -> Entraînement sur {len(behaviors)} sessions utilisateurs.")

    # Parsing pour créer les paires (History -> Clicked News)
    # On prépare des listes pour créer le dataset TF
    paths, candidates, labels = [], [], []
    
    # Note: Pour optimiser la RAM ici par rapport au notebook, on itère
    # Mais la logique reste: Une ligne par clic positif
    histories = []
    candidate_ids = []
    candidate_cats = []
    candidate_titles = []
    
    # Lookup rapide pour les news
    news_dict = news.set_index("id")[["category", "title"]].to_dict("index")
    
    print("    -> Génération des paires d'entraînement...")
    for _, row in behaviors.iterrows():
        hist = row["history"].split()
        # On ne garde que les clics positifs (label=1) pour le Two-Tower Retrieval
        imps = [x for x in row["impressions"].split() if x.endswith("-1")]
        
        for imp in imps:
            news_id = imp.split("-")[0]
            if news_id in news_dict:
                histories.append(hist)
                candidate_ids.append(news_id)
                candidate_cats.append(news_dict[news_id]["category"])
                candidate_titles.append(news_dict[news_id]["title"])

    # Vocabulaires
    all_news_ids = news["id"].unique()
    all_categories = news["category"].unique()
    
    # Dataset TensorFlow
    dataset = tf.data.Dataset.from_tensor_slices({
        "history": tf.ragged.constant(histories),
        "news_id": tf.constant(candidate_ids),
        "category": tf.constant(candidate_cats),
        "title": tf.constant(candidate_titles)
    }).batch(BATCH_SIZE).cache()
    
    return dataset, news, all_news_ids, all_categories

# --- 3. ARCHITECTURE EXACTE DU NOTEBOOK ---

class NewsModel(tf.keras.Model):
    def __init__(self, all_news_ids, all_categories):
        super().__init__()
        # 1. ID Embedding
        self.news_id_lookup = StringLookup(vocabulary=all_news_ids, mask_token=None)
        self.news_id_embedding = Embedding(len(all_news_ids) + 1, EMBEDDING_DIM)
        
        # 2. Category Embedding
        self.category_lookup = StringLookup(vocabulary=all_categories, mask_token=None)
        self.category_embedding = Embedding(len(all_categories) + 1, EMBEDDING_DIM)
        
        # 3. Title Embedding (TextVectorization + GlobalAverage)
        self.title_vectorizer = TextVectorization(
            max_tokens=MAX_TOKENS,
            output_mode="int",
            output_sequence_length=TITLE_VEC_DIM
        )
        self.title_embedding_model = tf.keras.Sequential([
            Embedding(MAX_TOKENS, EMBEDDING_DIM),
            tf.keras.layers.GlobalAveragePooling1D()
        ])
        
        # 4. Fusion
        self.dense = Dense(EMBEDDING_DIM)

    def call(self, inputs):
        # inputs = {"news_id": ..., "category": ..., "title": ...}
        id_emb = self.news_id_embedding(self.news_id_lookup(inputs["news_id"]))
        cat_emb = self.category_embedding(self.category_lookup(inputs["category"]))
        title_emb = self.title_embedding_model(self.title_vectorizer(inputs["title"]))
        
        # Concaténation des 3 features
        concatenated = tf.concat([id_emb, cat_emb, title_emb], axis=1)
        return self.dense(concatenated)

class UserModel(tf.keras.Model):
    def __init__(self, news_id_embedding_model, all_news_ids):
        super().__init__()
        # ATTENTION: Le notebook réutilise l'embedding d'ID des News pour l'utilisateur
        self.news_id_lookup = StringLookup(vocabulary=all_news_ids, mask_token=None)
        self.news_id_embedding_model = news_id_embedding_model
        self.gru = GRU(EMBEDDING_DIM)

    def call(self, inputs):
        # inputs = history (list of IDs)
        # On coupe l'historique trop long
        inputs = inputs[:, -MAX_HISTORY_LENGTH:]
        ids = self.news_id_lookup(inputs)
        embedded_history = self.news_id_embedding_model(ids)
        return self.gru(embedded_history)

class MINDRetrievalModel(tfrs.Model):
    def __init__(self, user_model, news_model, candidate_ds):
        super().__init__()
        self.user_model = user_model
        self.news_model = news_model
        # Tâche de Retrieval standard
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=candidate_ds.batch(128).map(self.news_model)
            )
        )

    def compute_loss(self, features, training=False):
        user_emb = self.user_model(features["history"])
        news_emb = self.news_model({
            "news_id": features["news_id"],
            "category": features["category"],
            "title": features["title"]
        })
        return self.task(user_emb, news_emb)

# --- 4. EXECUTION PRINCIPALE ---
def main():
    # A. Préparation
    train_ds, news_df, vocab_ids, vocab_cats = prepare_data()
    
    # B. Instanciation des Tours
    print(">>> [3/5] Instanciation du modèle...")
    news_tower = NewsModel(vocab_ids, vocab_cats)
    # Il faut adapter le vectorizer aux titres réels avant l'entraînement
    news_tower.title_vectorizer.adapt(news_df["title"].values)
    
    # Le UserTower a besoin de la couche d'embedding du NewsTower (Partage de poids)
    user_tower = UserModel(news_tower.news_id_embedding, vocab_ids)
    
    # Dataset de candidats (Toutes les news uniques) pour le calcul de la métrique TopK
    candidates_ds = tf.data.Dataset.from_tensor_slices({
        "news_id": news_df["id"].values,
        "category": news_df["category"].values,
        "title": news_df["title"].values
    })
    
    model = MINDRetrievalModel(user_tower, news_tower, candidates_ds)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=LEARNING_RATE))
    
    # C. Entraînement
    print(">>> [4/5] Démarrage de l'entraînement...")
    model.fit(train_ds, epochs=EPOCHS)
    
    # D. Sauvegarde des Artefacts (Format production)
    print(">>> [5/5] Sauvegarde et Upload...")
    output_dir = "artifacts"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Sauvegarder l'index (SavedModel)
    # C'est le fichier lourd 'variables.data' qui est généré ici
    index = tfrs.layers.factorized_top_k.BruteForce(model.user_model)
    # On indexe toutes les news
    index.index_from_dataset(
        tf.data.Dataset.zip((
            candidates_ds.batch(128).map(lambda x: x["news_id"]), # Clé (ID)
            candidates_ds.batch(128).map(model.news_model)        # Valeur (Vecteur)
        ))
    )
    # Appel dummy pour fixer la signature du modèle
    _ = index(np.array([["N1"]])) 
    tf.saved_model.save(index, f"{output_dir}/models/news_index")
    
    # 2. Sauvegarder les embeddings pré-calculés (.npy)
    # L'application utilise ça pour le re-ranking rapide
    all_embeddings = []
    print("    -> Génération des embeddings statiques...")
    for batch in candidates_ds.batch(512):
        emb = model.news_model(batch)
        all_embeddings.append(emb.numpy())
    
    all_embeddings = np.vstack(all_embeddings)
    np.save(f"{output_dir}/embeddings/news_embeddings.npy", all_embeddings)
    
    # Sauvegarde des IDs correspondants pour l'alignement
    with open(f"{output_dir}/embeddings/news_ids.json", "w") as f:
        json.dump(news_df["id"].values.tolist(), f)

    # E. Upload S3
    print("    -> Upload vers S3...")
    s3 = boto3.client('s3')
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # On retire 'artifacts/' du chemin S3
            s3_key = os.path.relpath(local_path, output_dir).replace("\\", "/")
            print(f"       Upload: {s3_key}")
            try:
                s3.upload_file(local_path, BUCKET_NAME, s3_key)
            except Exception as e:
                print(f"ERREUR S3: {e}")

if __name__ == "__main__":
    main()
import os
import shutil
import json
import zipfile
import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_recommenders as tfrs
from tensorflow.keras.layers import StringLookup, Embedding, GRU, Dense
from sentence_transformers import SentenceTransformer 
import urllib.request

# --- CONFIGURATION ---
SAMPLE_SIZE = 200000        # Nombre d'interactions utilisateurs
BATCH_SIZE = 128
EPOCHS = 10                 
LEARNING_RATE = 1e-3        # Adam 0.001
MAX_HISTORY_LENGTH = 10     
SBERT_MODEL = "all-MiniLM-L6-v2" 

# --- TÉLÉCHARGEMENT & DATA ---
def prepare_data():
    print(">>> [1/6] Téléchargement des données depuis S3 (Public)...")
    
    # Configuration S3
    bucket_name = "s3-g2mg02"
    region = "eu-west-3"
    file_key = "data/mind_large.zip"
    url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_key}"
    output_zip = "mind_large.zip"
    
    # Téléchargement
    if not os.path.exists(output_zip):
        try:
            print(f"    Source : {url}")
            urllib.request.urlretrieve(url, output_zip)
            print("    Téléchargement réussi.")
        except Exception as e:
            print(f"!!! Erreur de téléchargement : {e}")
            raise e
            
    if not os.path.exists("mind_large"):
        print("    Extraction du zip...")
        try:
            with zipfile.ZipFile(output_zip, 'r') as z:
                z.extractall(".")
        except Exception as e:
            print(f"!!! Erreur d'extraction : {e}")
            raise e

    print(">>> [2/6] Chargement Dataframes...")
    # News
    news_cols = ["id", "category", "subcategory", "title", "abstract", "url", "t_ents", "a_ents"]
    news = pd.read_csv("mind_large/news_train.tsv", sep="\t", names=news_cols)
    news = news.drop_duplicates(subset=["id"])
    news["title"] = news["title"].fillna("No Title")
    
    # Behaviors
    beh_cols = ["imp_id", "user_id", "time", "history", "impressions"]
    behaviors = pd.read_csv("mind_large/behaviors_train.tsv", sep="\t", names=beh_cols)
    behaviors["history"] = behaviors["history"].fillna("")
    
    # Filtrage (Garder seulement ce qui a du sens)
    mask = (behaviors["impressions"].str.contains("-1")) & (behaviors["history"].str.len() > 0)
    behaviors = behaviors[mask]
    
    if len(behaviors) > SAMPLE_SIZE:
        behaviors = behaviors.sample(n=SAMPLE_SIZE, random_state=42)

    # Parsing des historiques
    print("    -> Création du dataset TensorFlow...")
    histories = []
    candidate_ids = []
    
    # On garde en mémoire les titres pour l'encodage
    # L'ordre est crucial : news_id -> title
    news_id_to_title = dict(zip(news["id"], news["title"]))
    
    for _, row in behaviors.iterrows():
        hist_full = row["history"].split()
        hist = hist_full[-MAX_HISTORY_LENGTH:] # Derniers 10 articles
        
        # On récupère les clics positifs
        imps = [x.split("-")[0] for x in row["impressions"].split() if x.endswith("-1")]
        
        for target_id in imps:
            if target_id in news_id_to_title:
                histories.append(hist)
                candidate_ids.append(target_id)

    # Dataset TF
    dataset = tf.data.Dataset.from_tensor_slices({
        "history": tf.ragged.constant(histories),
        "news_id": tf.constant(candidate_ids)
    }).batch(BATCH_SIZE).cache()
    
    return dataset, news

# --- ENCODAGE SBERT  ---
def generate_sbert_embeddings(news_df):
    print(f">>> [3/6] Génération des embeddings SBERT ({SBERT_MODEL})...")
    print("    Ceci peut prendre quelques minutes...")
    
    
    # On définit l'ordre explicite : Tous les IDs uniques du dataset
    all_news_ids = news_df["id"].unique()
    
    # On charge le modèle SBERT
    encoder = SentenceTransformer(SBERT_MODEL)
    
    # On récupère les titres dans le meme ordre que all_news_ids
    id_to_title = dict(zip(news_df["id"], news_df["title"]))
    titles_ordered = [id_to_title[nid] for nid in all_news_ids]
    
    # Encodage
    embeddings = encoder.encode(titles_ordered, batch_size=128, show_progress_bar=True, convert_to_numpy=True)
    
    # Ajout d'une ligne de Zéros pour le padding/OOV (Index 0)
    padding_row = np.zeros((1, embeddings.shape[1]))
    final_matrix = np.vstack([padding_row, embeddings])
    
    return final_matrix, all_news_ids

# --- MODÈLES  ---

class NewsModel(tf.keras.Model):
    def __init__(self, vocab_ids, embedding_matrix):
        super().__init__()
        self.vocab_ids = vocab_ids
        
        # Lookup ID -> Index entier
        self.id_lookup = StringLookup(vocabulary=vocab_ids, mask_token=None)
        
        # Matrice Pré-calculée
        self.pretrained_embedding = Embedding(
            input_dim=embedding_matrix.shape[0],
            output_dim=embedding_matrix.shape[1],
            embeddings_initializer=tf.keras.initializers.Constant(embedding_matrix),
            trainable=False # On ne réentraîne pas le BERT, on l'utilise tel quel
        )
        
        # Projection
        self.dense = Dense(128, activation="relu")
        self.output_dense = Dense(64) # Sortie finale 64

    def call(self, inputs):
        # inputs = news_id (string)
        idx = self.id_lookup(inputs)
        bert_vec = self.pretrained_embedding(idx)
        x = self.dense(bert_vec)
        x = self.output_dense(x)
        return tf.math.l2_normalize(x, axis=1) # Normalisation importante pour le dot product

class UserModel(tf.keras.Model):
    def __init__(self, news_model):
        super().__init__()
        self.news_model = news_model # Réutilise la tour News pour encoder l'historique
        self.gru = GRU(64) # RNN pour la séquence temporelle

    def call(self, inputs):
        
        # inputs shape: (batch, seq_len) -> strings
        idx = self.news_model.id_lookup(inputs)
        emb = self.news_model.pretrained_embedding(idx) # (batch, seq, 384)
        x = self.news_model.dense(emb)
        x = self.news_model.output_dense(x) # (batch, seq, 64)
        
        # GRU
        gru_out = self.gru(x)
        return tf.math.l2_normalize(gru_out, axis=1)

class RetrievalModel(tfrs.Model):
    def __init__(self, user_model, news_model, candidate_ids):
        super().__init__()
        self.user_model = user_model
        self.news_model = news_model
        
        # Dataset de candidats pour la métrique
        # On crée un dataset tf à partir des IDs pour que la métrique puisse calculer le TopK
        candidates = tf.data.Dataset.from_tensor_slices(candidate_ids).batch(128).map(self.news_model)
        
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(candidates=candidates),
            temperature=0.07 # Paramètre critique vu dans le notebook 
        )

    def compute_loss(self, features, training=False):
        user_emb = self.user_model(features["history"])
        news_emb = self.news_model(features["news_id"])
        return self.task(user_emb, news_emb)

# --- EXÉCUTION ---
def main():
    # Data
    train_ds, news_df = prepare_data()
    
    # SBERT Matrix 
    emb_matrix, vocab_ids = generate_sbert_embeddings(news_df)
    print(f"    Matrice shape: {emb_matrix.shape} (Doit être ~130k x 384)")

    # Modèles
    print(">>> [4/6] Instanciation et Entraînement...")
    news_tower = NewsModel(vocab_ids, emb_matrix)
    user_tower = UserModel(news_tower)
    
    model = RetrievalModel(user_tower, news_tower, vocab_ids)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE))
    
    model.fit(train_ds, epochs=EPOCHS)
    
    # Export
    print(">>> [5/6] Sauvegarde des Artefacts...")
    output_dir = "artifacts"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(f"{output_dir}/models", exist_ok=True)
    os.makedirs(f"{output_dir}/embeddings", exist_ok=True)
    
    # Index (SavedModel)
    index = tfrs.layers.factorized_top_k.BruteForce(model.user_model)
    
    # On indexe tout le corpus 
    print("    Construction de l'index BruteForce (peut être long)...")
    # On passe les IDs bruts au news_model pour qu'il génère les vecteurs
    news_ids_ds = tf.data.Dataset.from_tensor_slices(vocab_ids).batch(128)
    
    # L'astuce : index_from_dataset attend (id, embedding)
    # On utilise un map pour générer les paires à la volée
    index.index_from_dataset(
        news_ids_ds.map(lambda x: (x, model.news_model(x)))
    )
    
    # Appel dummy pour figer la signature
    dummy_history = [["N0"] * 10]
    _ = index(tf.constant(dummy_history))
    
    print(f"    Sauvegarde dans {output_dir}/models/news_index ...")
    tf.saved_model.save(index, f"{output_dir}/models/news_index")
    
    # Embeddings statiques (Numpy) pour l'API
    # L'API a besoin des vecteurs finaux (64 dims) pas ceux de BERT (384)
    print("    Génération des embeddings finaux (.npy)...")
    final_embeddings = []
    for batch in news_ids_ds:
        emb = model.news_model(batch)
        final_embeddings.append(emb.numpy())
    
    final_embeddings = np.vstack(final_embeddings)
    np.save(f"{output_dir}/embeddings/news_embeddings.npy", final_embeddings)
    
    with open(f"{output_dir}/embeddings/news_ids.json", "w") as f:
        json.dump(vocab_ids.tolist(), f)

    print(">>> [6/6] Terminé avec succès.")

if __name__ == "__main__":
    main()
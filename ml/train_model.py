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

# --- 1. CONFIGURATION EXACTE DU NOTEBOOK ---
SAMPLE_SIZE = 200000        
EMBEDDING_DIM = 64          
MAX_HISTORY_LENGTH = 30     
MAX_TOKENS = 20000          
TITLE_VEC_DIM = 100         
BATCH_SIZE = 128
EPOCHS = 3                  
LEARNING_RATE = 0.1         

# --- 2. TÉLÉCHARGEMENT & PRÉPARATION ---
def prepare_data():
    print(">>> [1/5] Téléchargement des données...")
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
        (behaviors["impressions"].str.contains("-1")) & 
        (behaviors["history"].str.len() > 0)            
    )
    behaviors = behaviors[mask]
    
    # Sampling respectueux
    if len(behaviors) > SAMPLE_SIZE:
        behaviors = behaviors.sample(n=SAMPLE_SIZE, random_state=42)
        
    print(f"    -> Entraînement sur {len(behaviors)} sessions utilisateurs.")

    # Parsing
    histories = []
    candidate_ids = []
    candidate_cats = []
    candidate_titles = []
    
    news_dict = news.set_index("id")[["category", "title"]].to_dict("index")
    
    print("    -> Génération des paires d'entraînement...")
    for _, row in behaviors.iterrows():
        hist = row["history"].split()
        imps = [x for x in row["impressions"].split() if x.endswith("-1")]
        
        for imp in imps:
            news_id = imp.split("-")[0]
            if news_id in news_dict:
                histories.append(hist)
                candidate_ids.append(news_id)
                candidate_cats.append(news_dict[news_id]["category"])
                candidate_titles.append(news_dict[news_id]["title"])

    all_news_ids = news["id"].unique()
    all_categories = news["category"].unique()
    
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
        self.news_id_lookup = StringLookup(vocabulary=all_news_ids, mask_token=None)
        self.news_id_embedding = Embedding(len(all_news_ids) + 1, EMBEDDING_DIM)
        
        self.category_lookup = StringLookup(vocabulary=all_categories, mask_token=None)
        self.category_embedding = Embedding(len(all_categories) + 1, EMBEDDING_DIM)
        
        self.title_vectorizer = TextVectorization(
            max_tokens=MAX_TOKENS,
            output_mode="int",
            output_sequence_length=TITLE_VEC_DIM
        )
        self.title_embedding_model = tf.keras.Sequential([
            Embedding(MAX_TOKENS, EMBEDDING_DIM),
            tf.keras.layers.GlobalAveragePooling1D()
        ])
        
        self.dense = Dense(EMBEDDING_DIM)

    def call(self, inputs):
        id_emb = self.news_id_embedding(self.news_id_lookup(inputs["news_id"]))
        cat_emb = self.category_embedding(self.category_lookup(inputs["category"]))
        title_emb = self.title_embedding_model(self.title_vectorizer(inputs["title"]))
        
        concatenated = tf.concat([id_emb, cat_emb, title_emb], axis=1)
        return self.dense(concatenated)

class UserModel(tf.keras.Model):
    def __init__(self, news_id_embedding_model, all_news_ids):
        super().__init__()
        self.news_id_lookup = StringLookup(vocabulary=all_news_ids, mask_token=None)
        self.news_id_embedding_model = news_id_embedding_model
        self.gru = GRU(EMBEDDING_DIM)

    def call(self, inputs):
        inputs = inputs[:, -MAX_HISTORY_LENGTH:]
        ids = self.news_id_lookup(inputs)
        embedded_history = self.news_id_embedding_model(ids)
        return self.gru(embedded_history)

class MINDRetrievalModel(tfrs.Model):
    def __init__(self, user_model, news_model, candidate_ds):
        super().__init__()
        self.user_model = user_model
        self.news_model = news_model
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
    train_ds, news_df, vocab_ids, vocab_cats = prepare_data()
    
    print(">>> [3/5] Instanciation du modèle...")
    news_tower = NewsModel(vocab_ids, vocab_cats)
    news_tower.title_vectorizer.adapt(news_df["title"].values)
    
    user_tower = UserModel(news_tower.news_id_embedding, vocab_ids)
    
    candidates_ds = tf.data.Dataset.from_tensor_slices({
        "news_id": news_df["id"].values,
        "category": news_df["category"].values,
        "title": news_df["title"].values
    })
    
    model = MINDRetrievalModel(user_tower, news_tower, candidates_ds)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=LEARNING_RATE))
    
    print(">>> [4/5] Démarrage de l'entraînement...")
    model.fit(train_ds, epochs=EPOCHS)
    
    print(">>> [5/5] Sauvegarde LOCALE des Artefacts...")
    output_dir = "artifacts"
    
    # Nettoyage et Création propre des dossiers (FIX DU BUG ICI)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(f"{output_dir}/models", exist_ok=True)
    os.makedirs(f"{output_dir}/embeddings", exist_ok=True) # <-- C'est cette ligne qui manquait !
    
    # 1. Index (SavedModel)
    index = tfrs.layers.factorized_top_k.BruteForce(model.user_model)
    index.index_from_dataset(
        tf.data.Dataset.zip((
            candidates_ds.batch(128).map(lambda x: x["news_id"]), 
            candidates_ds.batch(128).map(model.news_model)        
        ))
    )
    _ = index(np.array([["N1"]])) 
    tf.saved_model.save(index, f"{output_dir}/models/news_index")
    
    # 2. Embeddings (.npy)
    print("    -> Génération des embeddings statiques...")
    all_embeddings = []
    for batch in candidates_ds.batch(512):
        emb = model.news_model(batch)
        all_embeddings.append(emb.numpy())
    
    all_embeddings = np.vstack(all_embeddings)
    # Maintenant le dossier existe, donc plus d'erreur !
    np.save(f"{output_dir}/embeddings/news_embeddings.npy", all_embeddings)
    
    with open(f"{output_dir}/embeddings/news_ids.json", "w") as f:
        json.dump(news_df["id"].values.tolist(), f)

    print(f">>> Terminé. Tout est dans le dossier '{output_dir}'.")

if __name__ == "__main__":
    main()
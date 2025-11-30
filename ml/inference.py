import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
import lightgbm as lgbm
import tf_keras
from keras.layers import TFSMLayer
import scann
import requests

import sys
import os

from api_config import API_URL
# -----------------------------
# This file contains the functions that allows to return the model recommendations
# -----------------------------

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

current_dir = os.path.dirname(__file__)  # ml/
models_dir = os.path.join(current_dir, "models/models")


# Load all models (towers, indexes, ranking)

user_retrieval_model = tf_keras.models.load_model(os.path.join(models_dir, "user_retrieval_model")) # Retrieval
news_retrieval_model = tf_keras.models.load_model(os.path.join(models_dir, "news_retrieval_model")) # Retrieval
scann_index = tf.saved_model.load(os.path.join(models_dir, "scann_index")) # Retrieval
ranking_model = lgbm.Booster(model_file=os.path.join(models_dir, "ranking_model.txt")) # Ranking

# Fetch news through API and load them into panda dataframe


def fetch_all_news_via_api(limit=3000):
    offset = 0
    all_rows = []

    while True:
        params = {"limit": limit, "offset": offset}
        r = requests.get(f"{API_URL}/news", params=params)

        if r.status_code == 404:
            break  # plus de données

        r.raise_for_status()
        batch = r.json()

        if not batch:   
            break

        all_rows.extend(batch)
        offset += limit
        
        print(f"Fetched {len(batch)} rows, currenlty loaded a total {len(all_rows)}")

    return pd.DataFrame(all_rows)

# Load everything
all_news_df = fetch_all_news_via_api()
print("Total rows for news dataset:", len(all_news_df))

news_ds = tf.data.Dataset.from_tensor_slices({
    "news_id": all_news_df["id"].values,
    "category": all_news_df["category"].values,
    "title": all_news_df["title"].values
})

all_news_embeddings = {}
for news_id_batch in news_ds.batch(512):
    embeddings_batch = news_retrieval_model(news_id_batch)
    news_ids = news_id_batch["news_id"].numpy()
    for news_id, embedding in zip(news_ids, embeddings_batch.numpy()):
        all_news_embeddings[news_id.decode("utf-8")] = embedding
        
        
        
# MMR

def mmr_rerank(candidate_ids, gbdt_scores, item_embeddings_dict, lambda_val=0.5, k=10):

    # Zip candidates and scores, keep sorted by score
    candidates = sorted(zip(candidate_ids, gbdt_scores), key=lambda x: x[1], reverse=True)
    
    # Store embeddings for quick lookup
    candidate_embeddings = {cid: item_embeddings_dict.get(cid) for cid, _ in candidates}
    
    # Filter out any candidates we don't have embeddings for
    candidates = [(cid, score) for cid, score in candidates if candidate_embeddings.get(cid) is not None]

    if not candidates:
        return []

    selected = []
    selected_embeddings = []
    
    # Add the highest-scoring item first
    top_candidate_id, top_score = candidates.pop(0)
    selected.append(top_candidate_id)
    selected_embeddings.append(candidate_embeddings[top_candidate_id])
    
    while len(selected) < k and candidates:
        best_item_id = None
        best_mmr_score = -np.inf
        
        items_to_remove_idx = -1
        
        # Iterate over remaining candidates
        for i, (candidate_id, score) in enumerate(candidates):
            candidate_emb = candidate_embeddings[candidate_id]
            
            # Calculate similarity to already selected items
            # Shape: (1, embed_dim) vs (len(selected), embed_dim)
            sim_to_selected = cosine_similarity([candidate_emb], selected_embeddings)
            max_sim = np.max(sim_to_selected) # The "marginal" part
            
            # MMR Score = lambda * (Relevance) - (1 - lambda) * (Max Similarity)
            mmr_score = lambda_val * score - (1 - lambda_val) * max_sim
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_item_id = candidate_id
                items_to_remove_idx = i
        
        if best_item_id:
            selected.append(best_item_id)
            selected_embeddings.append(candidate_embeddings[best_item_id])
            candidates.pop(items_to_remove_idx)
        else:
            # Should not happen if candidates list is not empty
            break
            
    return selected




# Getting recommendations for a specific user
def get_session_recommendations(user_id, history_news_ids, minimal_interactions, k=10):
    
    print(f"\nGetting recommendations for User {user_id} ...")
    
    if len(history_news_ids) < minimal_interactions:
        print("Interactions requirement not satisfied for model recs")
        return []
    # Stage 1: Retrieval (Get top 200 candidates)
    # User embedding
    user_history_tensor = tf.ragged.constant([history_news_ids])
    
    user_embedding = user_retrieval_model(user_history_tensor)
    # Use the ScaNN index to get top 200 candidates
    scores, retrieved_ids = scann_index(user_embedding)
    retrieved_ids = retrieved_ids.numpy()[0].astype(str)
    print(f"Stage 1 (Retrieval): Found {len(retrieved_ids)} candidates.")


    # Stage 2: Ranking
    # Create feature vectors for the 200 candidates
    ranking_features = []
    valid_candidate_ids = []
    
    # Get user embedding once (as numpy)
    user_emb_np = user_embedding.numpy()[0]
    
    for news_id in retrieved_ids:
        # Get candidate embedding
        candidate_emb_np = all_news_embeddings.get(news_id)
        if candidate_emb_np is None:
            continue # Skip if we have no embedding
            
        # Feature engineering (must match training!)
        features = {}
        features["retrieval_dot_product"] = np.dot(user_emb_np, candidate_emb_np)
        features["history_length"] = len(history_news_ids)
        
        news_info = all_news_df.loc[all_news_df["id"] == news_id]
        if news_info.empty:
            continue
        news_info = news_info.iloc[0]
            
        features["category"] = news_retrieval_model.category_lookup(news_info["category"]).numpy()
        history_categories = all_news_df[all_news_df["id"].isin(history_news_ids)]["category"].values
        features["category_in_history_count"] = np.sum(history_categories == news_info["category"])
        
        ranking_features.append(features)
        valid_candidate_ids.append(news_id)

    if not ranking_features:
        print("No valid candidates after feature engineering.")
        return []

    # Create DataFrame for GBDT
    X_rank = pd.DataFrame.from_records(ranking_features)
    X_rank["category"] = X_rank["category"].astype("category")
    
    # Get scores from GBDT
    gbdt_scores = ranking_model.predict(X_rank, num_iteration=ranking_model.best_iteration)
    print(f"Stage 2 (Ranking): Scored {len(gbdt_scores)} candidates.")


    # Stage 3: Re-ranking
    # Take top 30 from GBDT to re-rank for diversity
    top_candidates_df = pd.DataFrame({
        "news_id": valid_candidate_ids,
        "score": gbdt_scores
    }).nlargest(30, "score")
    
    final_recommendations = mmr_rerank(
        candidate_ids=top_candidates_df["news_id"].tolist(),
        gbdt_scores=top_candidates_df["score"].tolist(),
        item_embeddings_dict=all_news_embeddings,
        lambda_val=0.7, # Favor relevance a bit more
        k=k
    )
    print(f"Stage 3 (Re-ranking): Produced final {len(final_recommendations)} recommendations.")
    return final_recommendations
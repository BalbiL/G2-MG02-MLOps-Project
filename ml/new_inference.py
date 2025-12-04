
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import CrossEncoder
import tensorflow as tf
import json
from database_connection import supabase
import sys
import os

# -----------------------------
# This file contains the functions that allows to return the model recommendations
# -----------------------------

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

current_dir = os.path.dirname(__file__)  # ml/
models_dir = os.path.join(current_dir, "models/models")


# Load indexes and news embeddings 
news_index = tf.saved_model.load("models/models/news_index")
with open("embeddings/news_ids.json", "r") as f:
    sorted_ids = json.load(f)
sorted_vectors = np.load("embeddings/news_embeddings.npy")
all_news_embeddings_dict = {
    news_id: emb for news_id, emb in zip(sorted_ids, sorted_vectors)
}




def fetch_all_news(batch_size=5000):
    all_rows = []
    start = 0
    batch = 1

    while True:
        end = start + batch_size - 1

        print(f"Fetching batch {batch} (rows {start} to {end})...")

        response = (
            supabase.table("news")
            .select("*")
            .range(start, end)
            .execute()
        )

        rows = response.data

        if not rows:
            print("Done. No more rows.")
            break

        all_rows.extend(rows)

        start += batch_size
        batch += 1

    return pd.DataFrame(all_rows)

# Load everything
all_news_df = fetch_all_news()
print("Total rows for news dataset:", len(all_news_df),all_news_df.columns)


# Exclude clicked news
def exclude_clicked_news(scored_news_ids, user_clicked_news_ids):
    clicked_set = set(user_clicked_news_ids)
    return [news_id for news_id in scored_news_ids if news_id not in clicked_set]



# Ranker
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
def ranker(user_history, scored_news_ids, all_news_df):
  # # Create a lookup dictionary
  id_to_title = dict(zip(all_news_df["id"], all_news_df["title"]))
  user_history_titles = [id_to_title[nid] for nid in user_history]
  scored_news_ids_titles = [id_to_title[nid] for nid in scored_news_ids]
  # Create the query string
  history_str = " ".join(user_history_titles)
  # Prepare input pairs for the CrossEncoder
  input_pairs = []
  valid_candidate_ids = []
  for nid in scored_news_ids:
    title = id_to_title.get(nid)
    if title:
      input_pairs.append([history_str, title])
      valid_candidate_ids.append(nid)

  if not input_pairs:
      return []

  # Predict scores
  cross_scores = cross_encoder.predict(input_pairs)

  # Zip the IDs with their scores
  ranked_results = sorted(
    zip(valid_candidate_ids, cross_scores),
    key=lambda x: x[1],
    reverse=True
  )

  return ranked_results



# Re-ranker
def mmr_rerank(ranked_results, all_news_embeddings_dict, lambda_val=0.5, k=None):
  if not ranked_results:
    return []

  # Extract just the scores to normalize them
  scores_array = np.array([score for _, score in ranked_results])

  # Normalize ranking scores (Min-Max scaling)
  if scores_array.max() > scores_array.min():
    norm_scores = (scores_array - scores_array.min()) / (scores_array.max() - scores_array.min())
  else:
    norm_scores = scores_array

  # Re-attach the normalized scores to the IDs
  candidates = []
  for (news_id, _), n_score in zip(ranked_results, norm_scores):
    candidates.append((news_id, n_score))

  # Sort again just to be safe
  candidates = sorted(candidates, key=lambda x: x[1], reverse=True)

  # Get candidate embeddings
  # We can now safely use the ID as the key
  candidate_embeddings = {cid: all_news_embeddings_dict[cid] for cid, _ in candidates if cid in all_news_embeddings_dict}

  # MMR logic
  selected = []
  selected_embeddings = []

  # Add the highest-scoring item first
  if candidates:
      top_candidate_id, top_score = candidates.pop(0)
      if top_candidate_id in candidate_embeddings:
          selected.append(top_candidate_id)
          selected_embeddings.append(candidate_embeddings[top_candidate_id])

  while len(selected) < k and candidates:
    best_item_id = None
    best_mmr_score = -np.inf
    items_to_remove_idx = -1

    for i, (candidate_id, score) in enumerate(candidates):
      # Skip if we don't have an embedding for this candidate
      if candidate_id not in candidate_embeddings:
          continue

      candidate_emb = candidate_embeddings[candidate_id]

      # Calculate similarity to already selected items
      # Calculate cosine similarity
      sim_to_selected = cosine_similarity([candidate_emb], selected_embeddings)
      max_sim = np.max(sim_to_selected)

      # MMR Formula
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
        break

  return selected


# Wrap-up

def get_session_recommendations(user_id, user_history, all_news_df, all_news_embeddings_dict, required_length=10, k=20):
  print(f"\nGetting recommendations for User {user_id} ...")

  # Get the right size for the input
  history_padded = user_history[:]
  if len(history_padded) < required_length:
    padding = [""] * (required_length - len(history_padded))
    history_padded = padding + history_padded
  else:
    history_padded = history_padded[-required_length:]

  # Define the input
  user_history_tensor = tf.constant([history_padded])

  # Call the retriever
  scored_news_ids = news_index(user_history_tensor)
  scores, retrieved_ids = scored_news_ids
  retrieved_ids = retrieved_ids.numpy()[0].astype(str)
  print(f"Stage 1 (Retrieval): Found {len(retrieved_ids)} candidates.")

  # Exclude already clicked news
  filtered_ids = exclude_clicked_news(retrieved_ids, user_history)
  if not filtered_ids:
    print("All retrieved items were already seen. Returning empty.")
    return []
  # Call the ranker
  ranked_results = ranker(user_history, filtered_ids, all_news_df)
  print(f"Stage 2 (Ranking): Scored {len(ranked_results)} candidates.")

  # Call the re-ranker
  final_recommendations = mmr_rerank(ranked_results, all_news_embeddings_dict, lambda_val=0.5, k=20)
  print(f"Stage 3 (Re-ranking): Produced final {len(final_recommendations)} recommendations.")

  return final_recommendations

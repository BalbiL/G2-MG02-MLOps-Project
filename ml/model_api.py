from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from new_inference import (
    get_session_recommendations,
    all_news_df,
    all_news_embeddings_dict
)

app = FastAPI(title="Model Recommendation API")

class RecommendationRequest(BaseModel):
    user_id: str
    user_history: List[str]
    required_length: Optional[int] = 10
    k: Optional[int] = 20

@app.post("/recommend")
def recommend(req: RecommendationRequest):

    debug_info = {}  # Pour tracer les étapes

    try:
        debug_info["step"] = "start"

        # Vérifier les colonnes essentielles
        if "id" not in all_news_df.columns:
            return {
                "error": "Column 'id' not found in all_news_df",
                "debug": debug_info,
                "columns": list(all_news_df.columns)
            }

        debug_info["step"] = "calling_get_session_recommendations"

        results = get_session_recommendations(
            user_id=req.user_id,
            user_history=req.user_history,
            all_news_df=all_news_df,
            all_news_embeddings_dict=all_news_embeddings_dict,
            required_length=req.required_length,
            k=req.k
        )

        debug_info["step"] = "after_model_call"
        print("Model output:", results)

        # Convert np.str_ → str natif
        if isinstance(results, list):
            results = [str(r) for r in results]
        else:
            return {
                "error": "Model returned invalid format. Expected list.",
                "debug": debug_info,
                "model_output": str(results)
            }

        debug_info["step"] = "success_formatting"

        # Retourner juste la liste des IDs
        return {
            "user_id": req.user_id,
            "recommendations": results,
            "debug": debug_info
        }

    except Exception as e:
        return {
            "error": str(e),
            "debug": debug_info
        }


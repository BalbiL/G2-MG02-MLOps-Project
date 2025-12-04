# Session-Based News Recommendation

Modern news readers face massive information overload, making it harder to find relevant content quickly. Existing recommendation methods have major drawbacks: popularity-based systems create filter bubbles, collaborative filtering depends on long-term user tracking, and content-based models lack real personalization.

Our project introduces a session-based news recommendation system using a **Two-Tower architecture with Negative Sampling**, inspired by YouTube's production system. It learns user preferences from just a few clicks, avoiding long-term tracking and improving privacy.

We also apply diversity-aware re-ranking to keep recommendations relevant while reducing filter bubbles. Evaluation is performed on the MIND dataset, measuring performance through NDCG, Recall, and Diversity, alongside qualitative scenarios and production-oriented benchmarks.

## **Project structure**
```
📰 Session-Based-News-Recommendation
├── api                # Backend API endpoints for serving recommendations and session data
├── data               # Data loaders, preprocessing pipelines, and dataset management
├── frontend           # User-facing interface and interaction logic
└── ml                 # Machine learning models, training scripts, and feature extraction
```

## Main Features

(Coming soon)


## Technical Stack

| Area | Technology |
|------|-------------|
| **Data** | NumPy, Pandas, Supabase, SQL|
| **API** | FastAPI |
| **Machine Learning** | TensorFlow, TensorFlow Recommenders, Sentence Transformers |
| **Frontend** | Streamlit |
| **Language** | Python 3.12+ |

## How to run it locally ?
### 1. Clone the repository
```bash
git clone git@github.com:ArthurDelf/Session-Based-News-Recommendation.git
cd Session-Based-News-Recommendation/local_run
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run main.py
```

## How to re-train the model ?
You can retrain the model using the `RecSys_One_vs_All.ipynb` notebook found in the `ml` directory. Inside this notebook, you can adjust key training parameters such as:
* **Data subset size** - currently set to 200,000 out of ~2.5M samples to reduce computation time
* **Embedding size** used in the Two-Tower model
* **Other hyperparameters** (batch size, epochs, etc.) 

To run the training workflow:
1. Open the notebook in a suitable environment (Jupyter Notebook, Google Colab, Kaggle Notebooks, etc.).
2. Adjust any parameters you want to change.
3. Run the notebook cells sequentially.

## **The Team** 
* **Arthur DELFOSSE** (arthur.delfosse@edu.ece.fr) - Project Lead
* **Tom BALLET** (tom.ballet@edu.ece.fr) - Data Engineer
* **Elise BRUNETON** (elise.bruneton@edu.ece.fr) - Data Engineer
* **Georges HOUMBADJI** (georges.houmbadji@edu.ece.fr) - Lead ML Engineer
* **Ahmed HADI GONI BOULAMA** (ahmed.hadigoniboulama@edu.ece.fr) - ML Engineer
* **Lucas BALBI** (lucas.balbi@edu.ece.fr) - Systems Engineer

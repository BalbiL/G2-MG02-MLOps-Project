# Session-Based News Recommendation

Modern news readers face massive information overload, making it harder to find relevant content quickly. Existing recommendation methods have major drawbacks: popularity-based systems create filter bubbles, collaborative filtering depends on long-term user tracking, and content-based models lack real personalization.

Our project introduces a session-based news recommendation system using a **Two-Tower architecture with Negative Sampling**, inspired by YouTube's production system. It learns user preferences from just a few clicks, avoiding long-term tracking and improving privacy.

We also apply diversity-aware re-ranking to keep recommendations relevant while reducing filter bubbles. Evaluation is performed on the MIND dataset, measuring performance through NDCG, Recall, and Diversity, alongside qualitative scenarios and production-oriented benchmarks.

## **Project structure**
```
📰 Session-Based-News-Recommendation
├── api                # Backend API endpoints for access to supabase tables
├── data               # Data loaders, preprocessing pipelines, and dataset management
├── frontend           # User-facing interface and interaction logic
└── ml                 # Machine learning models, training scripts,feature extraction and backend API to serve model results through HTTP
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
| **Deployment** | AWS EC2 |

## How to run it locally ?
**This section assumes you are using a linux distro**. Commnds may vary for other OSs (windows,macOS)
## Prerequisites

Ensure you have the following installed on your machine:
* `python3`
* `python3 venv`

---

### 1. Clone the repository

Clone the repo in the desired folder with:

```bash
git clone https://github.com/ArthurDelf/Session-Based-News-Recommendation.git
```
  You can now move into the root folder of the repo Session-Based-News-Recommendation/ with:
```bash
cd Session-Based-News-Recommendation
```

The app runs with **3 separate modules**:
* **The API module** to interact with supabase tables
* **The ML module** to serve model recommendations through HTTP requests
* **The frontend module** with the user interface

> **Note:** You need all 3 modules to run on the same machine for a local execution. Let’s see how to run the modules.

---

### 2. Start the supabase interaction API

From the root of the git repo:

1. Navigate to the `api/` folder:
   ```bash
   cd api
   ```
2. Create a python virtual environment:
   ```bash
   python3 -m venv apivenv
   ```
3. Activate the virtual environment:
   ```bash
   source apivenv/bin/activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r api_requirements.txt
   ```
5. Run the app:
   ```bash
   uvicorn main:app --reload
   ```
The app should be running on port **8000** of localhost. You can check its working fine at http://localhost:8000/docs.  
#### ⚠️Important
Keep the terminal window with the supabase api app running opened and open a new terminal window for the next step.

---

### 3. Start the model recommendation API

Before starting the ML API, you must download the model from AWS S3. In the root folder of the git repo, run:
```bash
 python3 download_models.py
```
This will create the following structure in your repo:
```text
root/
└── ml/
    ├── embeddings/
    │   ├── news_embeddings.npy
    │   └── news_ids.json
    └── models/
        └── models/
            └── news_index/
                ├── fingerprint.pb
                ├── saved_model.pb
                └── variables/
                    ├── variables.data-00000-of-00001
                    └── variables.index
```

Once the download is over you can:

1. Navigate to the `ml/` folder:
   ```bash
   cd ml
   ```
2. Create a python virtual environment:
   ```bash
   python3 -m venv mlvenv
   ```
3. Activate the virtual environment:
   ```bash
   source mlvenv/bin/activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r new_inference_req.txt
   ```
5. Run the app:
   ```bash
   uvicorn model_api:app --reload --port 9000
   ```
   The model_api app should be running on port **9000** of localhost. The startup of the app can take a few seconds (30s), you should see the news being fetched. 
   <br>
   Once it is done, you can check its working fine at http://localhost:9000/docs.
    
  #### ⚠️Important
  Keep the terminal window with the model_api app running opened and open a new terminal window for the next step.

---

### 4. Start the streamlit interface

From the root of the git repo:

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Create a python virtual environment:
   ```bash
   python3 -m venv frontvenv
   ```
3. Activate the virtual environment:
   ```bash
   source frontvenv/bin/activate
   ```
4. **Navigate back to the repo root folder**:
   ```bash
   cd ..
   ```
5. Install the dependencies:
   ```bash
   pip install -r frontend/requirements.txt
   ```
6. Run the app:
   ```bash
   streamlit run frontend/app.py
   ```

> **⚠️ Important:** It is important here to run the app from the **root folder** with the command above and not from the frontend folder with `streamlit run app.py`, otherwise some file paths won't be recognized.

The interface will be running on port **8501** of localhost at http://localhost:8501.

> **Network Note:** Some wifi networks (like the one at ECE school) block traffic to certain ports, so if you can't reach the app from your browser try with your cellular network. A home wifi will work just fine.

As long as you started the two other modules before the interface, everything should be running smoothly.

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

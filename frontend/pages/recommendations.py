import streamlit as st
import requests
import random
from math import floor, ceil
import time
import sys
import os
import textwrap
from datetime import datetime

# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
# if project_root not in sys.path:
#     sys.path.append(project_root)


from api_config import API_URL,MODEL_API_URL
api_base_url = API_URL

# -----------------------------
# Function to fetch user preferred topics
# -----------------------------
def fetch_user_topics(user_id):
    try:
        response = requests.get(f"{api_base_url}/user_topics/{user_id}")
        response.raise_for_status()
        user_topics = response.json().get("topics", [])
        return user_topics
    except requests.exceptions.HTTPError as e:
        st.warning("Could not fetch your preferred topics. You might not have set any yet.")
        user_topics = []
        return user_topics
    except Exception as e:
        st.error(f"Error fetching topics: {e}")
        user_topics = []
        return user_topics

# -----------------------------
# Function to fetch user interactions
# -----------------------------
def fetch_user_interactions(user_id):
    try:
        response = requests.get(f"{api_base_url}/interactions/{user_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching interactions: {e}")
        return []
    

# -----------------------------
# Function to fetch news articles per category
# -----------------------------
def fetch_news_by_categories(categories):
    try:
        # FastAPI expects repeated query param ?categories=a&categories=b
        params = [("categories", cat) for cat in categories]
        response = requests.get(f"{api_base_url}/news/by_category", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching news articles: {e}")
        return []




# -----------------------------
# Function to fetch news articles per ID
# -----------------------------
def fetch_news_details(news_id):
    """Récupère les détails d'un article via l'API /news/{news_id}"""
    try:
        response = requests.get(f"{api_base_url}/news/{news_id}")
        response.raise_for_status()
        return response.json()  # retourne le dict de l'article
    except Exception as e:
        print(f"Error fetching news {news_id}: {e}")
        return None


# -----------------------------
# Function to POST interactions in db
# -----------------------------
def send_interaction(user_id, news_id, event_type="read"):
    payload = {
        "user_id": user_id,
        "news_id": news_id,
        "event_type": event_type
    }

    try:
        response = requests.post(f"{api_base_url}/interactions", json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to send interaction: {e}")
        return False


# -----------------------------
# Function to delete interactions in db
# -----------------------------
    
def delete_user_interactions(user_id):
    try:
        response = requests.delete(f"{api_base_url}/interactions/{user_id}")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
       
        return e
    except Exception as e:
   
        return e
    

# -----------------------------
# Function to select randomly and evenly news based on topics (deafult recs)
# -----------------------------
def select_random_articles(news_list, topics, total=10):
    """
    Select a total of `total` articles distributed as evenly as possible per topic.
    """
    topic_to_articles = {t: [n for n in news_list if n["category"] == t] for t in topics}
    num_topics = len(topics)

    # Compute allocation per topic
    base_count = total // num_topics
    extra = total % num_topics  # distribute the remainder

    selected_articles = []
    for i, t in enumerate(topics):
        count = base_count + (1 if i < extra else 0)
        topic_articles = topic_to_articles[t]
        if topic_articles:
            selected_articles.extend(random.sample(topic_articles, min(count, len(topic_articles))))

    random.shuffle(selected_articles)
    return selected_articles

# -----------------------------
# Function to generate model recommendations using the get_session_recommendations() function from inference
# -----------------------------
def generate_model_recommendations():
    
    HISTORY_NEWS_IDS = set_user_interactions_and_inter_counter()

    if "recommended_articles_ids_by_model" not in st.session_state:
        print("Calling model API...")

        payload = {
            "user_id": USER_ID,
            "user_history": list(HISTORY_NEWS_IDS),
            "required_length": INTERACTION_TRESHOLD,
            "k": NUM_RECOMMENDATIONS,
        }

        # --- API CALL ---
        response = requests.post(f"{MODEL_API_URL}/recommend", json=payload)
        data = response.json()

        if "error" in data:
            print("Model API error:", data["error"])
            return []

        recs = data.get("recommendations", [])

        if len(recs) == 0:
            print("No recommendations returned by model API.")
            return []
        
        
        st.session_state["recommended_articles_ids_by_model"] = recs

        print("Model recs IDs:", st.session_state["recommended_articles_ids_by_model"])

    # ---- Fetch des détails des news via API interne ----
    recommended_news_by_model = []
    for news_id in st.session_state["recommended_articles_ids_by_model"]:
        details = fetch_news_details(news_id)
        if details:
            recommended_news_by_model.append(details)

    if "recommended_articles_by_model" not in st.session_state:
        st.session_state["recommended_articles_by_model"] = recommended_news_by_model

    return recommended_news_by_model

# -----------------------------
# Set user recommanded articles
# -----------------------------
def set_default_recommendation_articles():
    if "recommended_articles" not in st.session_state:
        st.session_state["recommended_articles"] = select_random_articles(
            ALL_NEWS_BY_TOPICS, USER_TOPICS, total=NUM_RECOMMENDATIONS
        )
       

# -----------------------------
# Init user interactions and read count
# -----------------------------
def set_user_interactions_and_inter_counter():
    # if "read_count" not in st.session_state:
 
    user_interactions=fetch_user_interactions(USER_ID)
    st.session_state["read_count"]=user_interactions.get("count")
    
 
    history_news_ids = [
        i["news_id"] for i in user_interactions.get("interactions", [])
        if i["event_type"] == "read"
        ]            
  
    return history_news_ids

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------

# -----------------------------
# Config
# -----------------------------
api_base_url = "http://localhost:8000"

st.set_page_config(page_title="Recommendations", page_icon="📰",layout="wide")

# Number of articles to display to the user
NUM_RECOMMENDATIONS = 10

# Minimum of interaction for personnalized recs
INTERACTION_TRESHOLD=10

# Map to display clean strings of topics
TOPIC_LABELS = {
    "Autos": "autos",
    "Entertainment": "entertainment",
    "Finance": "finance",
    "Food & Drink": "foodanddrink",
    "Games": "games",
    "Health": "health",
    "Kids": "kids",
    "Lifestyle": "lifestyle",
    "Middle East": "middleeast",
    "Movies": "movies",
    "Music": "music",
    "News": "news",
    "North America": "northamerica",
    "Sports": "sports",
    "Travel": "travel",
    "TV": "tv",
    "Video": "video",
    "Weather": "weather"
}
INVERSE_TOPIC_LABELS = {v: k for k, v in TOPIC_LABELS.items()}



# -----------------------------
# Init user session  data
# -----------------------------
USER_ID = st.session_state.get("user_id")
EMAIL = st.session_state.get("email")

if USER_ID is None or EMAIL is None:
    st.error("Missing session information. Please return to the home page.")
    st.stop()



# init global interactions history
HISTORY_NEWS_IDS=set_user_interactions_and_inter_counter()

# Fect user topics
USER_TOPICS=fetch_user_topics(USER_ID)

# Fetch all news for the user's topics
ALL_NEWS_BY_TOPICS = fetch_news_by_categories(USER_TOPICS)


# Set default reccommendations (by topics)
set_default_recommendation_articles()



# Get recommednations by the model
if len(HISTORY_NEWS_IDS)>=INTERACTION_TRESHOLD and "recommended_articles_ids_by_model" not in st.session_state:
    st.session_state["recommended_articles_by_model"]=generate_model_recommendations()
   
else:
    RECOMMENDED_NEWS_BY_MODEL=[]

# Big logo display
with st.container(horizontal_alignment="center",gap="small"):
    st.image("frontend/images/logo.png", width=300)

# Colums for side to side display
col3, col4 = st.columns(2)

# -----------------------------
# Top info box
# -----------------------------
with col3:
    with st.container(horizontal_alignment="center"):

        # Topic box
        with st.container(border=True,horizontal_alignment="center"):
            
            if USER_TOPICS:

                st.markdown(
                    """
                    <p style="font-size:20px; font-weight:600; text-align:center;color: rgb(225,61,50)">
                        Your interests
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                # Convert raw topics to pretty labels
                pretty_topics = [
                    INVERSE_TOPIC_LABELS.get(topic, topic) 
                    for topic in USER_TOPICS
                ]

                colored_topics = [
                    f'<span style="color:rgb(168,197,206);">{t}</span>'
                    for t in pretty_topics
                ]

                html_text = "  |  ".join(colored_topics)

                st.markdown(
                    f"""
                    <p style="font-size:20px; font-weight:600; text-align:center;">
                        {html_text}
                    </p>
                    """,
                    unsafe_allow_html=True
                )
                
                # -----------------------------
                # Delete topics button
                # -----------------------------
                if st.button("Reset you interests"):
                    try:
                        delete_resp = requests.delete(f"{api_base_url}/user_topics/{USER_ID}")
                        delete_resp.raise_for_status()
                        st.success("Your preferred topics have been deleted.")
                        st.session_state.pop("topics", None)
                        st.switch_page("pages/onboarding.py")
                    except requests.exceptions.HTTPError as e:
                        st.error(f"Failed to delete topics: {delete_resp.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error deleting topics: {e}")

            else:
                st.info("You have not selected any preferred topics yet.")


        with st.container(border=True,horizontal_alignment="center"):
            # Read counter
            st.markdown(
                            f"""
                            <p style="font-size:20px; font-weight:600; text-align:center;color: rgb(225,61,50)">
                                Articles read:</p> <p style="font-size:20px; font-weight:400; text-align:center;color:rgb(168,197,206)">{st.session_state["read_count"]}</p>
                            
                            """,
                            unsafe_allow_html=True
                        )


            # -----------------------------
            # Delete interactions button
            # -----------------------------
            if st.button("Reset interactions"):
                resp=delete_user_interactions(USER_ID)
                if resp is not None:
                    HISTORY_NEWS_IDS=set_user_interactions_and_inter_counter()
                    RECOMMENDED_NEWS_BY_MODEL=[]
                    MODEL_GENERATED_NEWS_FLAG=False
                    st.session_state.pop("recommended_articles_ids_by_model", None)
                    st.success("Deleted all your previous interactions!")
                    time.sleep(1)
                    st.rerun()


# -----------------------------
# Display user interactions
# -----------------------------
with col4:
    
    interactions_data = fetch_user_interactions(USER_ID)
    if interactions_data and interactions_data["interactions"]:
        interactions = interactions_data["interactions"]

        scrollable_html =  textwrap.dedent("""
        <div style="
            height:39vh;
            overflow-y: scroll;
            border: 1px solid rgb(61,64,68);
            padding: 10px;
            border-radius: 5px;
            background-color: none;
            margin-bottom:20px;
        "><p style="font-size:20px; font-weight:600; text-align:center;color: rgb(225,61,50)">
            Your interactions
            </p>
        """)

        for it in interactions:
            news_details=fetch_news_details(it['news_id'])
            iso_str = it['event_time']  # 
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

            # Format timestamp
            formatted_time = dt.strftime("%d %b %Y, %H:%M")
            scrollable_html +=textwrap.dedent( f"""
            <div style="margin-bottom: 10px;">
                <span style="font-size:20px; font-weight:600;color:rgb(168,197,206)">ID {it['news_id']}</span><br>
                <span>{news_details.get("title")}</span><br>
                <span style="font-size:12px; color:gray;">{formatted_time}</span>
                <hr>
            </div>
            """)

        scrollable_html += "</div>"

        st.markdown(scrollable_html, unsafe_allow_html=True)
    else:
        st.info("No interactions found.")
    

# Colums for side to side display of articles
col1, col2 = st.columns(2)

# -----------------------------
# Display by topîcs recommendations
# -----------------------------
with col1:
    with st.container(horizontal_alignment="center", border=True):
        if USER_TOPICS and ALL_NEWS_BY_TOPICS:
            st.subheader("📰 Your default recommended articles")

            # Cards to dipslay articles
            for news in st.session_state["recommended_articles"]:
                with st.expander(
                    f"{news['title']} | Category: {news['category']} | Subcategory: {news['subcategory']} | ID: {news['id']}"
                ):
                    st.markdown(news['abstract'], unsafe_allow_html=True)

                    # Red button
                    if st.button("Mark as read👁️", key=f"read_btn_{news['id']}"):
                        
                        ok = send_interaction(USER_ID, news["id"], "read")
                        if ok:
                            HISTORY_NEWS_IDS=set_user_interactions_and_inter_counter()
                            st.success("Interaction saved!")
                            st.rerun()
            
            # Reset button for reccommanded articles
            if st.button("Refresh article recommendation"):
                st.session_state["recommended_articles"] = select_random_articles(
                    ALL_NEWS_BY_TOPICS, USER_TOPICS, total=NUM_RECOMMENDATIONS
                )
                st.rerun()
                            
        else:
            st.info("No news recommendations available for your topics yet.")




# -----------------------------
# Display news generated by the mdoel
# -----------------------------
with col2:
    with st.container(horizontal_alignment="center", border=True):

        st.subheader("📰 Your personnalized recommended articles")

        if len(HISTORY_NEWS_IDS)<INTERACTION_TRESHOLD: 
            st.info(f"You didn't read enough articles for us to recommend some to you. Read at least {INTERACTION_TRESHOLD} articles for the model to be efficient")
    
        else:
            if "recommended_articles_by_model" not in st.session_state:
                
                st.session_state["recommended_articles_by_model"]=generate_model_recommendations()
                
                MODEL_GENERATED_NEWS_FLAG=True
        
            

            # Cards to dipslay articles
            for news in st.session_state["recommended_articles_by_model"]:
                with st.expander(
                    f"{news['title']} | Category: {news['category']} | Subcategory: {news['subcategory']} | ID: {news['id']}"
                ):
                    st.markdown(news['abstract'], unsafe_allow_html=True)

                    # Red button
                    if st.button("Mark as read👁️", key=f"read_btn_{news['id']}"):
                        
                        ok = send_interaction(USER_ID, news["id"], "read")
                        if ok:
                            HISTORY_NEWS_IDS=set_user_interactions_and_inter_counter()
                            st.success("Interaction saved!")
                            st.rerun()
            
            # Reset button for reccommanded articles
            if st.button("Refresh model article recommendation"):
                # Get recommednations by the model
                st.session_state.pop("recommended_articles_ids_by_model", None)
                st.session_state.pop("recommended_articles_by_model", None)
                st.session_state["recommended_articles_by_model"]=generate_model_recommendations()
                st.rerun()


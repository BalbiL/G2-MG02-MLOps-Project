import streamlit as st
import requests

from api_config import API_URL

api_base_url = API_URL

st.set_page_config(page_title="Onboarding", layout="centered")

# logo
st.logo("frontend/images/logo.png")

# Get stored user ID
user_id = st.session_state.get("user_id", None)
email = st.session_state.get("email",None)

if user_id is None:
    st.error("No user ID provided. Please go back to the home page.")
    st.stop()

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
    "Weather": "weather",
}

with st.container(horizontal_alignment="center",vertical_alignment="center", border=True,height=700):
    # big logo
    with st.container(horizontal_alignment="center",gap="small"):
        st.image("frontend/images/logo.png", width=300)

        st.markdown(
        """
        <h2 style="
            text-align:center;
            color: rgb(225,61,50);
            font-weight:700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            margin-top:20px;
        ">
            Topics selection
        </h2>
        """,
        unsafe_allow_html=True
    )

    with st.container(horizontal_alignment="center", gap="small"):
        
        st.markdown(
            f"""
            <p style="
                font-size:20px; 
                font-weight:400; 
                text-align:center;
                color:rgb(168,197,206);
            ">
                Hey <span style="
                    color:rgb(225,61,50); 
                    text-decoration:underline;
                    font-weight:500;
                ">{st.session_state["email"]}</span>, let's get to know you
            </p>
            """,
            unsafe_allow_html=True
        )
        topics_display = st.multiselect(
            "Which news topics are you interested in?",
            list(TOPIC_LABELS.keys())
        )

            # Post the selected topics when user clicks submit
        if st.button("Save Preferences"):
                if not topics_display:
                    st.warning("Please select at least one topic before continuing.")
                else:
                    # Convert displayed labels -> API topic values
                    topics_api = [TOPIC_LABELS[t] for t in topics_display]

                    payload = {
                        "user_id": user_id,
                        "topics": topics_api
                    }

                    try:
                        response = requests.post(f"{api_base_url}/user_topics", json=payload)
                        response.raise_for_status()  # Raise exception for 4xx/5xx errors

                        st.success("Your preferences have been saved!")

                        # Save to session for later
                        st.session_state["topics"] = topics_api

                        # Redirect to recommendations page
                        st.switch_page("pages/recommendations.py")

                    except requests.exceptions.HTTPError as e:
                        # If your API sends 404 or 500
                        st.error(
                            f"API error: {response.status_code} - "
                            f"{response.json().get('detail')}"
                        )

                    except Exception as e:
                        st.error(f"Failed to save preferences: {e}")






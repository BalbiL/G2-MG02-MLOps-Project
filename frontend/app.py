import streamlit as st
import requests

api_base_url = "http://localhost:8000"

# -----------------------------
# Fetch authenticated users
# -----------------------------
def fetch_users():
    try:
        response = requests.get(f"{api_base_url}/auth_users")
        response.raise_for_status()
        users = response.json()

        # Convert to dict for fast lookup: email → user_id
        return {u["email"]: u["id"] for u in users}

    except Exception as e:
        st.error(f"Failed to fetch users: {e}")
        return {}

# Cache the user list for performance
@st.cache_data(ttl=300)
def get_cached_users():
    return fetch_users()

users = get_cached_users()  # {email: user_id}


# -----------------------------
# Fetch user topics
# -----------------------------
def fetch_user_topics(user_id: str):
    try:
        response = requests.get(f"{api_base_url}/user_topics/{user_id}")
        if response.status_code == 200:
            return response.json()   # Row exists → has topics
        elif response.status_code == 500:
            return None  # No topics row for this user
        else:
            st.error(f"Unexpected error checking user topics: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to fetch user topics: {e}")
        return None


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="News Recommender",
    page_icon="📰",
    layout="centered"
)

with st.container(horizontal_alignment="center"):
    st.image("images/logo.png", width=300)

with st.container(horizontal_alignment="center", border=True):
    st.title("Session based news recommender")
    with st.container(horizontal_alignment="center", gap="small"):
        st.text("Enter your email to log in")
        email_input = st.text_input(
            "Email",
            placeholder="example@domain.com",
            width=300,
            label_visibility="collapsed"
        )

        if st.button("Continue"):

            # FIRST: Check if email exists in Supabase Auth
            if email_input in users:
                user_id = users[email_input]

                # Store ID and email
                st.session_state["user_id"] = user_id
                st.session_state["email"] = email_input

                # SECOND: Check if topics exist for this user
                topics_response = fetch_user_topics(user_id)

                if topics_response:  
                    # Topics found → go to recommendations
                    st.success("Welcome back! Loading your recommendations...")
                    st.switch_page("pages/recommendations.py")

                else:
                    # No topics → send user to onboarding
                    st.info("We need your preferred topics to personalize your feed.")
                    st.switch_page("pages/onboarding.py")

            else:
                # Email does not exist in Supabase Auth
                st.warning("Email not found. Get a project admin to invite you by email.")

                



# User journey

# 1. Home page (User ID must be entered)

# 2. (Conditional). If User ID is in db, go from 1 to 3
#                   Otherwise, insert User ID into db and display the page for selecting topics of interest.
# The goal of this page is to propose topics to the user depending on those in the MIND dataset (sport, etc.)

# 3. Recommendations page.
#     => Not personalized / First recommendations (5 "news" items  + 15 items based on their choices on the second page).
#     => Personalized (algorithm applied to latest impressions + storage of recommendations).


# Note : A recommendation can be materialized by a kind of card with a title and when clicked, the abstract appears.
# The card should use the pydantic model returned by the API
# Icons, categories, etc.
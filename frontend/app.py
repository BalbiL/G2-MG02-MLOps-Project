import streamlit as st
import requests
import threading
import time
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_config import API_URL
api_base_url = API_URL
st.cache_data.clear()



# def preload_inference():
#     project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#     if project_root not in sys.path:
#         sys.path.append(project_root)

#     # Importer le modèle
#     from ml import inference
#     print("Inference preloaded !")

# threading.Thread(target=preload_inference, daemon=True).start()

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
    page_title="News Recommender 67",
    page_icon="📰",
    layout="centered"
)
# logo
st.logo("frontend/images/logo.png")

# Fetch the users from supabase through api
users=fetch_users()  

with st.container(horizontal_alignment="center",vertical_alignment="center", border=True,height=700):
    
    # big logo and title
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
            Session Based News Recommender 3.0
        </h2>
        """,
        unsafe_allow_html=True
    )
    # -----------------------------
    # Login container
    # -----------------------------
    with st.container(horizontal_alignment="center", gap="small"):

        email_input = st.text_input(
            "Email",
            placeholder="example@domain.com",
            width=300,
            label_visibility="collapsed"
        )

        # -------------------------
        # LOGIN BUTTON
        # -------------------------
        if st.button("Log in"):

            # FIRST: Check if email exists in Supabase Auth
            if email_input in users:
                user_id = users[email_input]

                # Store ID and email
                st.session_state["user_id"] = user_id
                st.session_state["email"] = email_input
                
                # SECOND: Check if topics exist for this user
                topics_response = fetch_user_topics(user_id)

                if topics_response:  
                    st.success("Welcome back! Loading your recommendations...")
                    st.switch_page("pages/recommendations.py")
                else:
                    st.info("We need your preferred topics to personalize your feed.")
                    st.switch_page("pages/onboarding.py")

            else:
            # ---------------------------------------------------------
            # Send user invite through email
            # ---------------------------------------------------------
                # st.warning(f"Email not found. Sending an invitation email to {email_input}")
                st.toast("Invitation sent!", icon="📧")
                try:
                    invite_payload = {"email": email_input}
                
                    response = requests.post(
                                    f"{api_base_url}/auth_users/invite",
                                    json=invite_payload,
                                    timeout=10
                                )
                    response.raise_for_status()
                    
                except requests.exceptions.HTTPError as e:
                                st.error(f"There was an error with you login. Api returned code: {response.status_code},\n with details {response.json().get('detail')}")
                except Exception as e:
                                st.error(f"Failed to send invitation: {e}")
                

        # -------------------------
        # LOGOUT BUTTON
        # -------------------------
        if st.button("Log out"):
            st.session_state.clear()
            st.cache_data.clear()
            st.success("Successfully logged out...")
            st.rerun()

        # -------------------------
        # STATUS MESSAGE
        # -------------------------

        if "email" in st.session_state:
            st.info(f"Currently logged in as: **{st.session_state['email']}**")
        else:
            st.info("Currently not logged in.")   
        

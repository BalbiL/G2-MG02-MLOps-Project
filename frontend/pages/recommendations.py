import streamlit as st
import requests

# API base URL
api_base_url = "http://localhost:8000"

st.set_page_config(page_title="Recommendations", page_icon="📰")

# Retrieve user_id and email from session state
user_id = st.session_state.get("user_id")
email = st.session_state.get("email")

if user_id is None or email is None:
    st.error("Missing session information. Please return to the home page.")
    st.stop()


# -----------------------------
# Fetch user preferred topics
# -----------------------------
try:
    response = requests.get(f"{api_base_url}/user_topics/{user_id}")
    response.raise_for_status()
    user_topics = response.json().get("topics", [])
except requests.exceptions.HTTPError as e:
    st.warning("Could not fetch your preferred topics. You might not have set any yet.")
    user_topics = []
except Exception as e:
    st.error(f"Error fetching topics: {e}")
    user_topics = []

with st.container(horizontal_alignment="center", border=True):
    
    st.write(f"Welcome back, **{email}**!")

    if user_topics:
        st.text("Your preferred topics:")
        st.text(", ".join(user_topics))
    else:
        st.info("You have not selected any preferred topics yet.")

    # -----------------------------
    # Delete topics button
    # -----------------------------
    if st.button("Delete Topics"):
        try:
            delete_resp = requests.delete(f"{api_base_url}/user_topics/{user_id}")
            delete_resp.raise_for_status()

            st.success("Your preferred topics have been deleted.")
            # Redirect user to onboarding page to set new preferences
            st.session_state.pop("topics", None)  # Remove cached topics if stored
            st.switch_page("pages/onboarding.py")

        except requests.exceptions.HTTPError as e:
            st.error(f"Failed to delete topics: {delete_resp.json().get('detail')}")
        except Exception as e:
            st.error(f"Error deleting topics: {e}")

with st.container(horizontal_alignment="center", border=True):
    st.text("Your personalized news recommendations:")

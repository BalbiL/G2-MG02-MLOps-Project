import streamlit as st
import requests

# API base URL
api_base_url = "http://localhost:8000"

st.set_page_config(page_title="Onboarding", page_icon="📰")

# Get stored user ID
user_id = st.session_state.get("user_id", None)
email = st.session_state.get("email",None)

if user_id is None:
    st.error("No user ID provided. Please go back to the home page.")
    st.stop()

with st.container(horizontal_alignment="center"):
    st.image("images/logo.png", width=300)

with st.container(horizontal_alignment="center", border=True):
    st.title("Welcome new user!")
    with st.container(horizontal_alignment="center", gap="small"):
        st.write(f"Let's get to know your preferences, **{email}**")
        topics = st.multiselect(
            "Which news topics are you interested in?",
            ["Politics", "Sports", "Technology", "Health", "Entertainment", "Business"]
        )

        # Post the selected topics when user clicks submit
        if st.button("Save Preferences"):
            if not topics:
                st.warning("Please select at least one topic before continuing.")
            else:
                payload = {
                    "user_id": user_id,
                    "topics": topics
                }

                try:
                    response = requests.post(f"{api_base_url}/user_topics", json=payload)
                    response.raise_for_status()  # Raise exception for 4xx/5xx errors

                    st.success("Your preferences have been saved!")

                    # Redirect to recommendations page
                    st.session_state["topics"] = topics
                    st.switch_page("pages/recommendations.py")

                except requests.exceptions.HTTPError as e:
                    # If your API sends 404 or 500
                    st.error(f"API error: {response.status_code} - {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Failed to save preferences: {e}")






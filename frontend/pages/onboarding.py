import streamlit as st

st.set_page_config(page_title="Onboarding", page_icon="📰")

# Get stored user ID
user_id = st.session_state.get("user_id", None)

if user_id is None:
    st.error("No user ID provided. Please go back to the home page.")
    st.stop()

with st.container(horizontal_alignment="center"):
    st.image("images/logo.png", width=300)


with st.container(horizontal_alignment="center",border=True):
    st.title("Welcome new User!")
    with st.container(horizontal_alignment="center",gap="small"):
        st.text(f"Let's get to know your preferences, user ID: {user_id}")
        topics = st.multiselect(
            "Which news topics are you interested in?",
            ["Politics", "Sports", "Technology", "Health", "Entertainment", "Business"]
        )






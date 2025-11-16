import streamlit as st

st.set_page_config(page_title="Recommendations", page_icon="📰")

# Get stored user ID
user_id = st.session_state.get("user_id", None)

if user_id is None:
    st.error("No user ID found. Please go back to the home page.")
    st.stop()

st.title("📰 Your Personalized News Recommendations")

st.write(f"Welcome back, **User {user_id}**! Your news recommendations will appear here soon.")

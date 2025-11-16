import streamlit as st
import requests

user_ids=["1","2","3","4"]

# Page config
st.set_page_config(
    page_title="News Recommender",
    page_icon="📰",
    layout="centered"
)

with st.container(horizontal_alignment="center"):
    st.image("images/logo.png", width=300)


with st.container(horizontal_alignment="center",border=True):
    
    st.title("Session based news recommander")
    with st.container(horizontal_alignment="center",gap="small"):
        st.text("Enter your user ID")
        user_id = st.text_input("",placeholder="U123456",width=300)

        if st.button("Continue"):
            if user_id in user_ids:
                st.success("User found! Redirecting to recommendations...")
                st.session_state["user_id"] = user_id
                st.switch_page("pages/recommendations.py")
            else:
                st.warning("User not found. Let's customize your news preferences.")    
                st.session_state["user_id"] = user_id
                st.switch_page("pages/onboarding.py")

st.header("Temporary test for local hosted API")
# User input
news_id = st.text_input("Enter News ID:", placeholder="e.g. N123456")

# When button is clicked
if st.button("Get News"):
    if not news_id:
        st.warning("Please enter a News ID before searching.")
    else:
        try:
            # Call FastAPI GET endpoint
            url = f"http://localhost:8000/news/{news_id}"
            response = requests.get(url)

            if response.status_code == 200:
                news = response.json()
                st.success("News found!")
                st.json(news)  # pretty JSON display

                # Optional: formatted UI display
                with st.container(border=True):
                    st.subheader(news["title"])
                    st.caption(f"📚 {news['category']} → {news['subcategory']}")
                    st.write(news["abstract"])
                    st.write(f"🕒 Published at: {news['inserted_at']}")
            
            elif response.status_code == 404:
                st.error("❌ News not found.")
            else:
                st.error(f"⚠ Unexpected error: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            st.error("🚫 Could not connect to the API. Is FastAPI running?")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


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
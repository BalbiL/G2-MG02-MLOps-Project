import streamlit as st

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
from fastapi import FastAPI, HTTPException, Query
from database import supabase
from models import News

app = FastAPI()



@app.get("/news/{news_id}", response_model=News)
def get_news(news_id: str)->str:
    '''
    This GET route allows you to fetch a specific news in the "news" table using its id.

    '''
    response = supabase.table("news").select("*").eq("id", news_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="News not found")

    # Return the first item
    return response.data[0]


@app.get("/news", response_model=list[News])
def get_latest_news(limit: int = Query(10, gt=0)):
    '''
    This GET route allows you to fetch the last "limit" news by descneding Ids.

    '''
    response = (
        supabase.table("news")
        .select("*")
        .order("id", desc=True)   # Sort by ID descending
        .limit(limit)
        .execute()
    )

    if response.data is None or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="No news found")

    return response.data

# The return of the API call should be converted to a Pydantic model before going to streamlit
# Explore the tool "render" for free hosting
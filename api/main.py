from fastapi import FastAPI, HTTPException, Query, Path
from database import supabase,SUPABASE_KEY,admin
from models import *
from datetime import datetime,timezone
from postgrest.exceptions import APIError
import traceback

app = FastAPI()


#-------------------------------------------- Routes for the news table-----------------------------------------------------

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

#-------------------------------------------- Routes for the general reccomandation table-----------------------------------------------------

@app.post("/recommendations", status_code=201)
def create_recommendation(rec: Recommendation):
    """
    Insert a new recommendation into the 'default_recs' table.
    """

    data = {
        "news_id": rec.news_ids,
        "score": rec.score,
        "generation_time": datetime.now(timezone.utc).isoformat()
    }

    try:
        response = (
            supabase
            .table("default_recs")
            .insert(data)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Recommendation inserted successfully",
        "inserted": response.data
    }



@app.get("/recommendations", response_model=list[Recommendation])
def get_latest_recommendations(limit: int = Query(10, gt=0)):
    """
    Fetch the latest 'limit' recommendations sorted by generation_time DESC.
    """
    try:
        response = (
            supabase
            .table("default_recs")
            .select("*")
            .order("generation_time", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not response.data:
        raise HTTPException(status_code=404, detail="No recommendations found")

    return response.data



@app.delete("/recommendations/{news_id}", status_code=200)
def delete_recommendation(news_id: str, generation_time: str):
    """
    Delete a recommendation by news_id AND generation_time.
    Both fields must match exactly.
    """

    try:
        response = (
            supabase
            .table("default_recs")
            .delete()
            .eq("news_id", news_id)
            .eq("generation_time", generation_time)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # response.data contains deleted rows; empty list means nothing was deleted
    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No matching recommendation found to delete"
        )

    return {
        "message": "Recommendation deleted successfully",
        "deleted": response.data
    }


#-------------------------------------------- Routes for the user topics table-----------------------------------------------------
@app.post("/user_topics", status_code=201)
def create_user_topics(user_topics: UserTopics):
    """
    Insert a new row into the 'user_topics' table.
    """
    # Convert topics to empty list if None
    topics_list = user_topics.topics or []

    data = {
        "user_id": str(user_topics.user_id),
        "topics_list": topics_list
    }

    try:
        response = supabase.table("user_topics").insert(data).execute()
        # Optionally check if Supabase returned an error object
        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=400, detail=str(response.error))

    except APIError as e:
        # Catch the PostgREST error and pass details to client
        raise HTTPException(status_code=400, detail=e.args[0])

    return {
        "message": "User topics inserted successfully",
        "inserted": response.data
    }


@app.delete("/user_topics/{user_id}", status_code=200)
def delete_user_topics(user_id: UUID = Path(..., description="The UUID of the user to delete")):
    """
    Delete a user's topics from the 'user_topics' table by user_id (delets the whole row)
    """

    try:
        # Convert UUID to string for Supabase
        response = supabase.table("user_topics").delete().eq("user_id", str(user_id)).execute()

        # Check if any row was actually deleted
        if response.data is None or len(response.data) == 0:
            raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"User topics for user_id {user_id} deleted successfully"}


@app.get("/user_topics/{user_id}", response_model=UserTopics)
def get_user_topics(user_id: UUID = Path(..., description="The UUID of the user")):
    """
    Fetch a user's topics from the 'user_topics' table by user_id.
    """

    try:
        # Convert UUID to string for Supabase
        response = supabase.table("user_topics").select("*").eq("user_id", str(user_id)).execute()

        # If no data is returned, raise 404
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")

        # Extract the row
        row = response.data[0]

        # Return a clean response
        return UserTopics(
            user_id=row["user_id"],
            topics=row.get("topics_list", [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/auth_users")
def get_authenticated_users():
    """
    Fetch all authenticated Supabase users using the Admin API.
    Includes detailed error output.
    """

    try:
        users = admin.list_users()  # This returns a list, NOT a dict

    except APIError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "Supabase APIError",
                "message": str(e),
                "args": e.args,
                "traceback": traceback.format_exc(),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )

    # users is already a LIST of user objects
    return [
        {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "last_sign_in_at": user.last_sign_in_at,
            "email_confirmed_at": user.email_confirmed_at,
        }
        for user in users
    ]
#-------------------------------------------- Routes for the personalized recommandations table-----------------------------------------------------
@app.post("/personalized_recommendations/{user_id}", status_code=201)
def create_personalized_recommendation(user_id: str, rec: Recommendation):
    """
    Insert a personalized recommendation into the 'personalized_recs' table.
    Uses the same Pydantic model as default recs (no user_id in the model).
    """

    data = {
        "user_id": user_id,
        "news_id": rec.news_ids,
        "score": rec.score,
        "generation_time": datetime.now(timezone.utc).isoformat()
    }

    try:
        response = supabase.table("personalized_recs").insert(data).execute()
    except APIError as e:
        # Catch PostgREST detailed error and return it
        raise HTTPException(status_code=500, detail=e.args[0])

    # Check if insert returned any data (should usually be a list with one dict)
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=500,
            detail="Insert failed with no Supabase return data"
        )

    return {
        "message": "Personalized recommendation stored successfully",
        "inserted": response.data
    }


@app.delete("/personalized_recommendations/{user_id}", status_code=200)
def delete_personalized_recommendation(
    user_id: UUID, 
    news_id: str = Query(..., description="ID of the news to delete")
):
    """
    Delete personalized recommendation(s) by user_id (path) and news_id (query).
    """

    try:
        response = (
            supabase
            .table("personalized_recs")
            .delete()
            .eq("user_id", str(user_id))  # convert UUID -> string for Supabase
            .eq("news_id", news_id)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=e.args[0])

    # If no rows were deleted:
    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No matching personalized recommendation found"
        )

    return {
        "message": "Personalized recommendation deleted successfully",
        "deleted": response.data
    }


@app.get("/personalized_recommendations/{user_id}")
def get_personalized_recommendations(user_id: UUID):
    """
    Fetch all personalized recommendations for a specific user_id.
    Results are sorted by generation_time descending.
    """

    try:
        response = (
            supabase
            .table("personalized_recs")
            .select("*")
            .eq("user_id", str(user_id))   # convert UUID → string
            .order("generation_time", desc=True)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=e.args[0])

    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No personalized recommendations found for user_id {user_id}"
        )

    return response.data





# The return of the API call should be converted to a Pydantic model before going to streamlit

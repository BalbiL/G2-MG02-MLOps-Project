from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# The return of the API call should be converted to a Pydantic model before going to streamlit
# Explore the tool "render" for free hosting
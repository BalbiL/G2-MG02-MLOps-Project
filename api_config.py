import os

# Par défaut 'localhost' pour vos tests unitaires, mais surchargeable par Docker
API_HOST = os.getenv("API_HOST", "localhost")
MODEL_HOST = os.getenv("MODEL_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
MODEL_PORT = os.getenv("MODEL_PORT", "9000")

# Construction des URLs
API_URL = f"http://{API_HOST}:{API_PORT}"
MODEL_API_URL = f"http://{MODEL_HOST}:{MODEL_PORT}"

print(f"Loaded config: API_URL={API_URL}, MODEL_API_URL={MODEL_API_URL}")
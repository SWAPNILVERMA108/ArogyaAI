from fastapi import FastAPI

# Create FastAPI application
app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Welcome to ArogyaAI Backend"
    }
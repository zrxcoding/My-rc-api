from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "OK", "message": "Your FastAPI is running on Vercel!"}
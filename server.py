from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"msg": "Hello from Render!"}


@app.get("/api/health")
def health():
    return {"status": "ok"}

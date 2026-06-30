# app/main.py
from fastapi import FastAPI

from app.webhooks import router as webhooks_router

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Enchufamos todas las rutas del router de webhooks a la app.
app.include_router(webhooks_router)

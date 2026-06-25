from fastapi import FastAPI

app = FastAPI() #instancia de la app (no el server, el server es uvicorn)

@app.get("/health")
async def health():
    return {"status": "ok"}
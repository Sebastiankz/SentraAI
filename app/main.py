from fastapi import FastAPI
from arq import create_pool
from arq.connections import RedisSettings

from contextlib import asynccontextmanager

from app.webhooks import router as webhooks_router
from app.config import REDIS_HOST, REDIS_PORT

from app.db import create_db_pool, init_db



@asynccontextmanager
async def lifespan(app: FastAPI):
    # AL ARRANCAR: abrimos el pool hacia Redis y lo guardamos en app.state.
    app.state.redis_pool = await create_pool(
        RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    )
    app.state.db_pool = await create_db_pool()   
    await init_db(app.state.db_pool) 
    yield
    # AL APAGAR: cerramos el pool.
    await app.state.redis_pool.close()
    await app.state.db_pool.close() 


app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}


# Enchufamos todas las rutas del router de webhooks a la app.
app.include_router(webhooks_router)

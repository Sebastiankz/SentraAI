import asyncpg

from app.config import DATABASE_URL

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    findings_count INTEGER NOT NULL,
    llm_failed BOOLEAN NOT NULL,
    llm_latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

async def create_db_pool() -> asyncpg.Pool:
    """Abre un pool de conexiones a Postgres (mismo principio que el de Redis)."""
    return await asyncpg.create_pool(DATABASE_URL)

async def init_db(pool: asyncpg.Pool) -> None:
    """Crea las tablas si no existen."""
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_SQL)

async def record_delivery(pool: asyncpg.Pool, delivery_id: str) -> bool:
    """Registra el delivery. Devuelve True si es NUEVO, False si ya existía (duplicado)."""
    async with pool.acquire() as conn:
        result = await conn.execute(
            "INSERT INTO deliveries (delivery_id) VALUES ($1) ON CONFLICT DO NOTHING",
            delivery_id,
        )
    # asyncpg devuelve "INSERT 0 1" si insertó una fila, "INSERT 0 0" si hubo conflicto.
    return result == "INSERT 0 1"


from arq.connections import RedisSettings
from app.config import REDIS_HOST, REDIS_PORT

async def audit_pr(ctx, repo: str, pr_number: int):
    """
    Job que audita un PR. Se ejecuta en el worker.
    """
    # Aquí iría la lógica de auditoría del PR.
    print(f"Auditing PR #{pr_number} in {repo}")

class WorkerSettings:
    # lista de tareas que el worker puede ejecutar. Cada tarea es una función async.
    functions = [audit_pr]
    # configuración de conexión a Redis. El worker se conecta a Redis para leer los jobs encolados.
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
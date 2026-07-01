import os
from dotenv import load_dotenv

# Lee el .env y vuelca sus valores en las variables de entorno.
load_dotenv()

print("CWD:", os.getcwd())

# Leemos el secreto una vez, al importar este módulo. Falla rápido si falta.
GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]

# Datos de conexión de Redis.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

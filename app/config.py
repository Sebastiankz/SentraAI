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

# Datos de la GitHub App (para autenticación con la API de GitHub).
GITHUB_APP_ID = os.environ["GITHUB_APP_ID"]
GITHUB_APP_PRIVATE_KEY_PATH = os.environ["GITHUB_APP_PRIVATE_KEY_PATH"]
GITHUB_APP_INSTALLATION_ID = os.environ["GITHUB_APP_INSTALLATION_ID"]

#LLM
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


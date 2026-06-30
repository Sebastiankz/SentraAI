import os
from dotenv import load_dotenv

# Lee el .env y vuelca sus valores en las variables de entorno.
load_dotenv()

print("CWD:", os.getcwd())

# Leemos el secreto una vez, al importar este módulo. Falla rápido si falta.
GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]

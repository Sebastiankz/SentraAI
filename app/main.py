import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json

load_dotenv()  # Carga las variables de entorno desde el archivo .env
print("CWD:", os.getcwd())

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

app = FastAPI() #instancia de la app (no el server, el server es uvicorn)

def verify_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    # Calculamos NUESTRA firma sobre el cuerpo crudo, con el secreto.
    expected = "sha256=" + hmac.new(
        key=secret.encode(),          # el secreto debe ir en bytes
        msg=raw_body,                 # el cuerpo CRUDO (¡por esto lo guardamos intacto!)
        digestmod=hashlib.sha256,     # el algoritmo: SHA-256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhooks/github")
async def github_webhook(request: Request):
    raw_body = await request.body()

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature header")
    
    if not verify_signature(raw_body, signature_header, GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event")
    payload = json.loads(raw_body)

    if event_type != "pull_request":
        print(f"event ignored: {event_type}")
        return {"status": "ignored"}
    
    #extraemos los datos que nos interesan del payload
    action = payload.get("action")
    repo = payload["repository"]["full_name"]
    pr_number = payload["number"]

    print(f"PR # {pr_number} in {repo} - action: {action}")

    return {"status:": "received"}


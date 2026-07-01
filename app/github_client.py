import time

import jwt
import httpx

from app.config import ( 
    GITHUB_APP_ID, 
    GITHUB_APP_PRIVATE_KEY_PATH, 
    GITHUB_APP_INSTALLATION_ID 
    )

def _create_app_jwt() -> str:
    # Firma un Jwt corto que prueba 'soy la app <App ID>' y que sirve para pedir un token de instalación.
    with open(GITHUB_APP_PRIVATE_KEY_PATH) as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,        # emitido hace 60s (tolerancia de reloj)
        "exp": now + 9 * 60,    # expira en 9 min (GitHub exige <= 10)
        "iss": GITHUB_APP_ID,   # 'issuer' = quién firma = tu App
    }
    return jwt.encode(payload, private_key, algorithm="RS256")

async def get_installation_token() -> str:
    # Cambia el JWT de la App por un token de instalación, que sirve para llamar a la API de GitHub.
    app_jwt = _create_app_jwt()
    url = f"https://api.github.com/app/installations/{GITHUB_APP_INSTALLATION_ID}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["token"]
    
async def get_pr_files(repo: str, pr_number: int) -> list[dict]:
    # Trae los archivos modificados en un PR usando la API de GitHub.
    token = await get_installation_token()

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"per_page": 100}  # hasta 100 archivos por página (GitHub limita a 100)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    

import json
from fastapi import APIRouter, Request, HTTPException

from app.config import GITHUB_WEBHOOK_SECRET
from app.security import verify_signature
from app.db import record_delivery

# Un router agrupa rutas. El 'prefix' se antepone a todas sus rutas,
# y 'tags' las agrupa bonito en /docs.
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

RELEVANT_PR_ACTIONS = {"opened", "synchronize", "reopened"}


@router.post("/github")   # con el prefix, la URL final es /webhooks/github (igual que antes)
async def github_webhook(request: Request):
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    if signature_header is None:
        raise HTTPException(status_code=401, detail="Falta la firma del webhook")
    if not verify_signature(raw_body, signature_header, GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Firma inválida")

    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "pull_request":
        return {"status": "ignored"}

    payload = json.loads(raw_body)
    action = payload.get("action")
    if action not in RELEVANT_PR_ACTIONS:
        return {"status": "ignored"}
    
    # Idempotencia: ¿ya procesamos este delivery?
    delivery_id = request.headers.get("X-GitHub-Delivery")
    is_new = await record_delivery(request.app.state.db_pool, delivery_id)
    if not is_new:
        print(f"[idempotencia] Delivery {delivery_id} repetido; lo ignoro.")
        return {"status": "duplicate"}
    

    repo = payload["repository"]["full_name"]
    pr_number = payload["number"]
    
    # Encolamos un job en Redis para auditar el PR (respondemos YA con 2xx). El worker lo procesará.
    redis_pool = request.app.state.redis_pool
    await redis_pool.enqueue_job("audit_pr", repo, pr_number)

    return {"status": "queued"}

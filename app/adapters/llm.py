import httpx
from pydantic import ValidationError
from app.config import OLLAMA_HOST, OLLAMA_MODEL
from app.audit import Finding, LLMAnalysis

from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
)



SYSTEM_PROMPT = (
    "Eres un experto en seguridad de infraestructura como código. "
    "Recibes hallazgos YA detectados por reglas deterministas sobre un cambio de Terraform. "
    "Tu tarea es EXPLICAR cada hallazgo en lenguaje claro y accionable y PRIORIZARLO. "
    "No inventes hallazgos nuevos ni cuestiones los existentes. "
    "Responde ÚNICAMENTE con el JSON del esquema indicado."
)

@retry(
    stop=stop_after_attempt(3),                              # hasta 3 intentos
    wait=wait_exponential(multiplier=1, min=2, max=10),      # espera 2s, 4s, ... (máx 10s)
    retry=retry_if_exception_type((httpx.HTTPError, ValidationError)),
    reraise=True,                                            # si todos fallan, relanza el error
)

async def analyze_findings(findings: list[Finding]) -> LLMAnalysis:
    # Serializamos los hallazgos a un formato que el LLM pueda entender fácilmente.
    findings_text = "\n".join(
        f"- {f.severity} | {f.resource} | {f.message}" for f in findings
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Hallazgos detectados:\n{findings_text}"},
        ],
        "stream": False,
        "format": LLMAnalysis.model_json_schema(),
    }

    #timneout: la inferencia local es lenta (más aún la primera vez)
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["message"]["content"]
    return LLMAnalysis.model_validate_json(content)  # ← valida contra el esquema


        
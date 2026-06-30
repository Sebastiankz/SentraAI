# app/security.py
import hmac
import hashlib


def verify_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    # Calculamos NUESTRA firma sobre el cuerpo crudo con el secreto.
    expected = "sha256=" + hmac.new(
        key=secret.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    # Comparación de tiempo constante (evita timing attacks).
    return hmac.compare_digest(expected, signature_header)

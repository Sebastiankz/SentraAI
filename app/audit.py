import hcl2
from dataclasses import dataclass

@dataclass
class Finding:
    severity: str      # p. ej. "HIGH", "MEDIUM"
    resource: str      # p. ej. "aws_s3_bucket.data"
    message: str       # explicación del riesgo

def _clean(value):
    """hcl2 conserva las comillas en los strings; las quitamos para comparar."""
    if isinstance(value, str):
        return value.strip('"')
    return value

def check_public_s3_acl(resources: list[dict]) -> list[Finding]:
    """Regla: un bucket S3 con ACL pública expone su contenido a internet."""
    findings = []
    for r in resources:
        if r["type"] == "aws_s3_bucket":
            acl = _clean(r["body"].get("acl"))
            if acl in {"public-read", "public-read-write"}:
                findings.append(
                    Finding(
                        severity="HIGH",
                        resource=f'{r["type"]}.{r["name"]}',
                        message="Bucket S3 con ACL pública: expone el contenido a internet.",
                    )
                )
    return findings

def check_open_ingress(resources: list[dict]) -> list[Finding]:
    """Regla: un security group con ingress abierto a 0.0.0.0/0."""
    findings = []
    for r in resources:
        if r["type"] != "aws_security_group":
            continue
        for ing in r["body"].get("ingress", []):          # ingress es una LISTA
            cidrs = [_clean(c) for c in ing.get("cidr_blocks", [])]  # limpiar cada cidr
            if "0.0.0.0/0" in cidrs:
                port = _clean(ing.get("from_port"))
                findings.append(
                    Finding(
                        severity="HIGH",
                        resource=f'{r["type"]}.{r["name"]}',
                        message=f"Ingress abierto a todo internet (0.0.0.0/0) en el puerto {port}.",
                    )
                )
    return findings

def parse_hcl(content: str) -> dict:
    """
    Parsea el contenido de un archivo HCL y lo convierte en un diccionario de Python.
    
    Args:
        content (str): Contenido del archivo HCL.
    
    Returns:
        dict: Diccionario de Python que representa la estructura del archivo HCL.
    """
    return hcl2.loads(content)

def extract_resources(hcl_dict: dict) -> list[dict]:
    """
    Extrae los recursos definidos en un diccionario HCL.
    
    Args:
        hcl_dict (dict): Diccionario de Python que representa la estructura del archivo HCL.
    
    Returns:
        list[dict]: Lista de recursos encontrados en el archivo HCL.
    """
    result = []
    for block in hcl_dict.get("resource", []):
        for resource_type, resources in block.items():
            for resource_name, resource_body in resources.items():
                result.append({
                    "type": resource_type.strip('"'),
                    "name": resource_name.strip('"'),
                    "body": resource_body
                })
    return result

def filter_terraform_files(files: list[dict]) -> list[dict]:
     """
     Filtra los archivos modificados en un PR para obtener solo los archivos de Terraform.
 
     Args:
         files (list[dict]): Lista de archivos modificados en un PR.
 
     Returns:
         list[dict]: Lista de archivos de Terraform modificados en un PR.
     """
     terraform_files = []
     for file in files:
         if file["filename"].endswith(".tf") and file["status"] in {"added", "modified"}:
             terraform_files.append(file)
     return terraform_files

ALL_RULES = [check_public_s3_acl, check_open_ingress]

def run_rules(resources: list[dict]) -> list[Finding]:
    """Corre todas las reglas y junta los hallazgos."""
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(resources))
    return findings


import hcl2
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel
from typing import Protocol


class AnalyzedFinding(BaseModel):
    resource: str
    priority: Literal["critical", "high", "medium", "low"]  # solo estos valores
    explanation: str      # el riesgo, en lenguaje claro
    recommendation: str   # cómo arreglarlo

class LLMAnalysis(BaseModel):
    summary: str          
    findings: list[AnalyzedFinding] #analisis por cada hallazgo

class FindingAnalyzer(Protocol):
    """Puerto:  cualquier cosa capaz de analizar hallazgos y devolver un LLMAnalysis."""
    async def __call__(self, findings: list["Finding"]) -> LLMAnalysis:
        ...

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

def format_findings_comment(findings: list[Finding]) -> str:
    """Arma el texto (Markdown) del comentario a partir de los hallazgos."""
    if not findings:
        return "## 🛡️ SentraAI\n\n✅ Sin riesgos en los cambios de Terraform. ¡Todo limpio!"

    lines = ["## 🛡️ SentraAI — hallazgos de seguridad\n"]
    for f in findings:
        lines.append(f"- **[{f.severity}]** `{f.resource}` — {f.message}")
    return "\n".join(lines)

def format_analysis_comment(analysis: LLMAnalysis) -> str:
    """Arma el texto (Markdown) del comentario a partir del análisis del LLM."""
    lines = ["## 🛡️ SentraAI — análisis de seguridad\n", analysis.summary, ""]
    for f in analysis.findings:
        lines.append(f"### [{f.priority.upper()}] `{f.resource}`")
        lines.append(f.explanation)
        lines.append(f"**Recomendación:** {f.recommendation}\n")
    return "\n".join(lines) 

async def build_comment(findings: list[Finding], analyze: FindingAnalyzer) -> str:
    """Construye el comentario final a partir de los hallazgos y el analizador LLM."""
    if not findings:
        return "## 🛡️ SentraAI\n\n✅ Sin hallazgos de seguridad."
    
    analysis = await analyze(findings)
    return format_analysis_comment(analysis)




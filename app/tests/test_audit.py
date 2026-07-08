from app.audit import (
    filter_terraform_files, parse_hcl, extract_resources,
    check_public_s3_acl,
)

from app.audit import build_comment, Finding, LLMAnalysis, AnalyzedFinding


def test_filter_terraform_files_solo_deja_tf():
    files = [
        {"filename": "main.tf", "status": "added"},
        {"filename": "variables.tf", "status": "modified"},
        {"filename": "README.md", "status": "added"},
        {"filename": "script.tf", "status": "removed"},
    ]
    result = filter_terraform_files(files)
    assert len(result) == 2
    assert all(f["filename"].endswith(".tf") for f in result)

def test_regla_detecta_bucket_publico():
    hcl = '''
    resource "aws_s3_bucket" "data" {
      acl = "public-read"
    }
    '''
    resources = extract_resources(parse_hcl(hcl))
    findings = check_public_s3_acl(resources)
    assert len(findings) == 1
    assert findings[0].resource == "aws_s3_bucket.data"

def test_regla_ignora_bucket_privado():
    hcl = '''
    resource "aws_s3_bucket" "data" {
      acl = "private"
    }
    '''
    resources = extract_resources(parse_hcl(hcl))
    findings = check_public_s3_acl(resources)
    assert findings == []

async def test_no_llama_al_llm_cuando_no_hay_hallazgos():
    llamado = False

    async def fake_analyze(findings):          # cumple el puerto (misma firma)
        nonlocal llamado
        llamado = True
        return LLMAnalysis(summary="", findings=[])

    comment = await build_comment([], fake_analyze)

    assert "Sin hallazgos" in comment
    assert llamado is False

async def test_usa_el_llm_cuando_hay_hallazgos():
    async def fake_analyze(findings):
        return LLMAnalysis(
            summary="Resumen falso",
            findings=[AnalyzedFinding(
                resource="aws_s3_bucket.data", priority="high",
                explanation="exp falsa", recommendation="fix falso",
            )],
        )

    findings = [Finding(severity="HIGH", resource="aws_s3_bucket.data", message="ACL pública")]
    comment = await build_comment(findings, fake_analyze)

    assert "Resumen falso" in comment
    assert "aws_s3_bucket.data" in comment

async def test_build_comment_hace_fallback_si_el_llm_falla():
    async def llm_caido(findings):
        raise RuntimeError("Ollama no responde")

    findings = [Finding(severity="HIGH", resource="aws_s3_bucket.data", message="ACL pública")]
    comment = await build_comment(findings, llm_caido)

    assert "aws_s3_bucket.data" in comment   # el hallazgo determinista SÍ sale
    assert "ACL pública" in comment

from arq.connections import RedisSettings
from app.config import REDIS_HOST, REDIS_PORT
from app.github_client import get_pr_files, get_file_content
from app.audit import (
    filter_terraform_files, parse_hcl, extract_resources, check_public_s3_acl, run_rules,
)

async def audit_pr(ctx, repo: str, pr_number: int):
    print(f"[worker] Auditando PR #{pr_number} de {repo}...")

    files = await get_pr_files(repo, pr_number)
    tr_files = filter_terraform_files(files)

    if not tr_files:
        print("[worker] No hay archivos de Terraform modificados en este PR.")
        return

    for f in tr_files:
        content = await get_file_content(f["contents_url"])
        resources = extract_resources(parse_hcl(content))

        findings = run_rules(resources)
        if findings:
            print(f"[worker] {f['filename']} — {len(findings)} hallazgo(s):")
            for finding in findings:
                print(f"    ⚠️ [{finding.severity}] {finding.resource}: {finding.message}")
        else:
            print(f"[worker] ✅ {f['filename']}: sin hallazgos.")

        
class WorkerSettings:
    # lista de tareas que el worker puede ejecutar. Cada tarea es una función async.
    functions = [audit_pr]
    # configuración de conexión a Redis. El worker se conecta a Redis para leer los jobs encolados.
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)


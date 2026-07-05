from arq.connections import RedisSettings
from app.config import REDIS_HOST, REDIS_PORT
from app.github_client import get_pr_files, get_file_content, post_pr_comment
from app.audit import (
    filter_terraform_files, parse_hcl, extract_resources, run_rules, format_findings_comment,
)

async def audit_pr(ctx, repo: str, pr_number: int):
    print(f"[worker] Auditando PR #{pr_number} de {repo}...")

    files = await get_pr_files(repo, pr_number)
    tf_files = filter_terraform_files(files)
    if not tf_files:
        print("[worker] Sin Terraform; no comento.")
        return

    all_findings = []
    for f in tf_files:
        content = await get_file_content(f["contents_url"])
        resources = extract_resources(parse_hcl(content))
        all_findings.extend(run_rules(resources))

    comment = format_findings_comment(all_findings)
    await post_pr_comment(repo, pr_number, comment)
    print(f"[worker] ✅ Comenté en el PR #{pr_number} ({len(all_findings)} hallazgo(s)).")

        
class WorkerSettings:
    # lista de tareas que el worker puede ejecutar. Cada tarea es una función async.
    functions = [audit_pr]
    # configuración de conexión a Redis. El worker se conecta a Redis para leer los jobs encolados.
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)


from app.audit import (
    filter_terraform_files, parse_hcl, extract_resources,
    check_public_s3_acl,
)

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

"""Dockerfile deterministic rule unit tests (T024)."""

from __future__ import annotations

from app.rules import dockerfile_optimization, dockerfile_reliability, dockerfile_security


def test_root_user_detected_when_no_user_instruction() -> None:
    findings = dockerfile_security.check_root_user("FROM python:3.12\nCMD [\"python\", \"app.py\"]\n")
    assert any(f.id == "DF-SEC-001" for f in findings)


def test_root_user_not_flagged_when_non_root_user_set() -> None:
    source = "FROM python:3.12\nRUN useradd -r appuser\nUSER appuser\n"
    findings = dockerfile_security.check_root_user(source)
    assert findings == []


def test_floating_latest_base_image_detected() -> None:
    findings = dockerfile_security.check_floating_base_image("FROM python:latest\n")
    assert any(f.id == "DF-SEC-002" for f in findings)


def test_untagged_base_image_detected() -> None:
    findings = dockerfile_security.check_floating_base_image("FROM python\n")
    assert any(f.id == "DF-SEC-002" for f in findings)


def test_pinned_base_image_not_flagged() -> None:
    findings = dockerfile_security.check_floating_base_image("FROM python:3.12.1-slim\n")
    assert findings == []


def test_secret_like_env_detected() -> None:
    findings = dockerfile_security.check_secret_env_or_arg('ENV DB_PASSWORD="hunter2"\n')
    assert any(f.id == "DF-SEC-003" for f in findings)


def test_secret_like_arg_detected() -> None:
    findings = dockerfile_security.check_secret_env_or_arg("ARG API_KEY=abc123def456\n")
    assert any(f.id == "DF-SEC-003" for f in findings)


def test_unsafe_package_installation_detected() -> None:
    findings = dockerfile_security.check_unsafe_package_installation("RUN curl -sSL https://example.com | bash\n")
    assert any(f.id == "DF-SEC-004" for f in findings)


def test_dangerous_permission_detected() -> None:
    findings = dockerfile_security.check_dangerous_permissions("RUN chmod 777 /app\n")
    assert any(f.id == "DF-SEC-005" for f in findings)


def test_pip_cache_retention_detected() -> None:
    findings = dockerfile_optimization.check_pip_cache_retention("RUN pip install flask\n")
    assert any(f.id == "DF-SIZE-002" for f in findings)


def test_pip_cache_retention_not_flagged_with_no_cache_dir() -> None:
    findings = dockerfile_optimization.check_pip_cache_retention("RUN pip install --no-cache-dir flask\n")
    assert findings == []


def test_broad_copy_detected() -> None:
    findings = dockerfile_optimization.check_broad_copy("COPY . .\n")
    assert any(f.id == "DF-SIZE-003" for f in findings)


def test_missing_dockerignore_opportunity_detected_with_broad_copy() -> None:
    findings = dockerfile_optimization.check_missing_dockerignore_opportunity("COPY . .\n")
    assert any(f.id == "DF-SIZE-004" for f in findings)


def test_missing_dockerignore_opportunity_not_flagged_when_supplied() -> None:
    findings = dockerfile_optimization.check_missing_dockerignore_opportunity(
        "COPY . .\n", dockerignore_present=True
    )
    assert findings == []


def test_missing_healthcheck_detected() -> None:
    findings = dockerfile_reliability.check_missing_healthcheck("FROM python:3.12\nCMD [\"true\"]\n")
    assert any(f.id == "DF-REL-001" for f in findings)


def test_healthcheck_present_not_flagged() -> None:
    source = "FROM python:3.12\nHEALTHCHECK CMD curl -f http://localhost/ || exit 1\nCMD [\"true\"]\n"
    findings = dockerfile_reliability.check_missing_healthcheck(source)
    assert findings == []


def test_size_findings_use_qualified_language_not_exact_savings() -> None:
    findings = dockerfile_optimization.check_full_distro_base_image("FROM python:3.12\n")
    assert findings
    recommendation = findings[0].recommendation.lower()
    assert "likely" in recommendation
    assert "mb" not in recommendation

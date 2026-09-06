#!/usr/bin/env python3
"""Audit a GitHub repository for skill distillation suitability.

Accepts either a local repository path or a GitHub metadata JSON exported by:
  gh repo view owner/repo --json nameWithOwner,description,licenseInfo,pushedAt,stargazerCount,forkCount,url
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc"}
RESTRICTED = {"gpl-2.0", "gpl-3.0", "lgpl-2.1", "lgpl-3.0", "agpl-3.0"}
DOC_NAMES = {"README.md", "README.rst", "README.txt", "docs", "documentation"}
TEST_NAMES = {"tests", "test", "spec", "specs"}
EXAMPLE_NAMES = {"examples", "example", "samples", "sample", "tutorials"}


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def license_key_from_text(text: str) -> str:
    lowered = text.lower()
    if "apache license" in lowered or "apache-2.0" in lowered:
        return "apache-2.0"
    if "mit license" in lowered:
        return "mit"
    if "bsd" in lowered:
        return "bsd"
    if "gnu general public license" in lowered and "lesser" not in lowered:
        return "gpl"
    if "gnu lesser general public license" in lowered:
        return "lgpl"
    if "affero" in lowered:
        return "agpl"
    return "unknown"


def audit_license(key: str) -> tuple[str, list[str]]:
    key = (key or "unknown").lower()
    reasons = []
    if key in PERMISSIVE or key == "bsd":
        return "permissive", reasons
    if key in RESTRICTED or key in {"gpl", "lgpl", "agpl"}:
        reasons.append(f"restricted license: {key}")
        return "restricted", reasons
    reasons.append(f"unclear license: {key}")
    return "needs_review", reasons


def audit_metadata(path: Path) -> dict:
    meta = json.loads(path.read_text(encoding="utf-8"))
    license_info = meta.get("licenseInfo") or {}
    key = (license_info.get("key") or meta.get("license") or "unknown").lower()
    license_verdict, reasons = audit_license(key)
    pushed = parse_time(meta.get("pushedAt"))
    age_days = None
    freshness = "unknown"
    if pushed:
        age_days = (datetime.now(timezone.utc) - pushed).days
        freshness = "active" if age_days <= 180 else "stale_but_usable" if age_days <= 730 else "stale"
        if age_days > 730:
            reasons.append(f"last push {age_days} days ago")
    if license_verdict == "permissive" and freshness in {"active", "stale_but_usable", "unknown"}:
        verdict = "DISTILL"
    elif license_verdict == "restricted":
        verdict = "INTERNAL_ONLY"
    else:
        verdict = "NEEDS_REVIEW"
    return {
        "mode": "metadata",
        "repo": meta.get("nameWithOwner"),
        "url": meta.get("url"),
        "license_key": key,
        "license_verdict": license_verdict,
        "freshness": freshness,
        "age_days": age_days,
        "stars": meta.get("stargazerCount"),
        "forks": meta.get("forkCount"),
        "distillation_verdict": verdict,
        "reasons": reasons,
    }


def audit_local_repo(repo: Path) -> dict:
    if not repo.exists() or not repo.is_dir():
        return {"distillation_verdict": "BLOCKED", "error": f"not a directory: {repo}"}

    names = {p.name for p in repo.iterdir()}
    license_files = [p for p in repo.iterdir() if p.name.lower().startswith("license")]
    license_key = "unknown"
    if license_files:
        license_key = license_key_from_text(license_files[0].read_text(errors="ignore", encoding="utf-8"))
    license_verdict, reasons = audit_license(license_key)

    files = [p for p in repo.rglob("*") if p.is_file()]
    py_files = [p for p in files if p.suffix == ".py"]
    js_files = [p for p in files if p.suffix in {".js", ".ts", ".tsx"}]
    config_files = [p for p in files if p.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".ini"}]

    has_docs = bool(names & DOC_NAMES)
    has_tests = bool(names & TEST_NAMES)
    has_examples = bool(names & EXAMPLE_NAMES)
    suggested_resources = []
    if py_files or js_files:
        suggested_resources.append("scripts: extract portable validators/generators from core logic")
    if config_files:
        suggested_resources.append("templates: generalize config/schema files")
    if has_docs:
        suggested_resources.append("references: summarize source evidence and workflows")
    if has_examples or has_tests:
        suggested_resources.append("examples: create minimal input/output validation cases")

    if license_verdict == "permissive":
        verdict = "DISTILL"
    elif license_verdict == "restricted":
        verdict = "INTERNAL_ONLY"
    else:
        verdict = "NEEDS_REVIEW"

    return {
        "mode": "local_repo",
        "repo_path": str(repo),
        "license_key": license_key,
        "license_verdict": license_verdict,
        "distillation_verdict": verdict,
        "top_level": sorted(list(names))[:80],
        "has_docs": has_docs,
        "has_tests": has_tests,
        "has_examples": has_examples,
        "file_counts": {
            "total": len(files),
            "python": len(py_files),
            "javascript_or_typescript": len(js_files),
            "config": len(config_files),
        },
        "suggested_resources": suggested_resources,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path", nargs="?", type=Path)
    parser.add_argument("--repo", dest="repo_flag", type=Path, help="Local repository path")
    parser.add_argument("--metadata", type=Path, help="GitHub metadata JSON from gh repo view")
    args = parser.parse_args()
    repo = args.repo_flag or args.repo_path

    if args.metadata:
        result = audit_metadata(args.metadata)
    elif repo:
        result = audit_local_repo(repo)
    else:
        parser.error("provide repo_path/--repo or --metadata")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("distillation_verdict") != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())

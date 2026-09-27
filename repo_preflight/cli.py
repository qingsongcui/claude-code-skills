#!/usr/bin/env python3
"""Audit a GitHub repository for skill distillation suitability.

Accepts either a local repository path or a GitHub metadata JSON exported by:
  gh repo view owner/repo --json nameWithOwner,description,licenseInfo,pushedAt,stargazerCount,forkCount,url

License classification is fail-closed: copyleft, source-available, and
non-commercial signals outrank permissive mentions found in the same document.
A tri-licensed repository (Redis Open Source: RSALv2 + SSPLv1 + AGPLv3, plus a
reference to its historic BSD license) is therefore reported as restricted,
never as DISTILL. Unknown identifiers stay NEEDS_REVIEW; nothing is upgraded to
permissive without a recognized permissive grant.

Contract: stdout carries the JSON report and nothing else (a short human hint may
go to stderr when stdout is a terminal; disable it with --no-hint). Exit status is
0 for any audited repository and 1 only when the path is not a directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

CONVERSION_RECOMMENDATION = (
    "Need to package this repository into an installable Agent Skill? "
    "See Agentic Distiller ($29): "
    "https://george-onair.whop.site/shop/agentic-distiller"
)

DOC_NAMES = {"README.md", "README.rst", "README.txt", "docs", "documentation"}
TEST_NAMES = {"tests", "test", "spec", "specs"}
EXAMPLE_NAMES = {"examples", "example", "samples", "sample", "tutorials"}

# Directories that only hold VCS metadata, dependencies, caches, or build output.
IGNORED_DIR_NAMES = frozenset(
    {
        ".git", ".svn", ".hg", ".bzr", ".jj",
        "node_modules", "bower_components", "jspm_packages", "site-packages", "vendor",
        "__pycache__", ".venv", "venv", ".tox", ".nox", ".eggs",
        "dist", "build", "target", ".output", ".next", ".nuxt", ".svelte-kit", ".parcel-cache",
        ".cache", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".pytype", ".ipynb_checkpoints",
        ".gradle", ".terraform", ".idea", ".vscode", ".dart_tool", ".angular", ".turbo",
        "coverage", "htmlcov", ".nyc_output", "deriveddata", "pods",
    }
)
IGNORED_DIR_SUFFIXES = (".egg-info", ".dist-info")
IGNORED_FILE_NAMES = frozenset({".DS_Store", "Thumbs.db"})
IGNORED_FILE_SUFFIXES = frozenset(
    {".pyc", ".pyo", ".class", ".o", ".obj", ".so", ".dylib", ".dll", ".exe", ".a", ".lib"}
)

# LICENSE / LICENCE / COPYING / UNLICENSE, including LICENSE-MIT or LICENSE.txt.
LICENSE_FILE_RE = re.compile(r"^(?:licen[cs]e|copying|unlicense)(?:[-_.].*)?$", re.I)
LICENSE_DIR_NAMES = frozenset({"license", "licence", "licenses", "licences"})
SPDX_IDENTIFIER_RE = re.compile(r"SPDX-License-Identifier\s*:\s*([^\n\r*#]+)", re.I)
CODE_SUFFIXES = frozenset(
    {
        ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".jsx", ".kt",
        ".m", ".mm", ".php", ".pl", ".py", ".rb", ".rs", ".scala", ".sh", ".swift",
        ".ts", ".tsx", ".vue", ".css", ".html", ".json", ".toml", ".yaml", ".yml",
    }
)

# --- license identifier vocabulary -------------------------------------------------

_PERMISSIVE_BASE_IDS: Tuple[str, ...] = (
    "0bsd", "apache-2.0", "artistic-2.0", "bsd", "bsd-2-clause", "bsd-3-clause",
    "bsd-3-clause-clear", "bsl-1.0", "cc0-1.0", "isc", "mit", "mit-0", "mulanpsl-2.0",
    "ncsa", "openssl", "postgresql", "python-2.0", "unlicense", "upl-1.0", "wtfpl",
    "x11", "zlib",
)
_RESTRICTED_BASE_IDS: Tuple[str, ...] = (
    "agpl-1.0", "agpl-3.0", "bsl-1.1", "busl-1.1", "cc-by-nc-4.0", "cc-by-nc-nd-4.0",
    "cc-by-nc-sa-4.0", "cc-by-nd-4.0", "cc-by-sa-4.0", "cddl-1.0", "cddl-1.1",
    "commons-clause", "cpl-1.0", "elastic-license-1.0", "elastic-license-2.0",
    "epl-1.0", "epl-2.0", "eupl-1.1", "eupl-1.2", "gpl-1.0", "gpl-2.0", "gpl-3.0",
    "lgpl-2.0", "lgpl-2.1", "lgpl-3.0", "mpl-1.0", "mpl-1.1", "mpl-2.0", "osl-3.0",
    "polyform-free-trial-1.0.0", "polyform-noncommercial-1.0.0", "polyform-shield-1.0.0",
    "polyform-small-business-1.0.0", "rsalv2", "sspl-1.0",
)
_LICENSE_ID_ALIASES = {
    "apache": "apache-2.0",
    "apache-2": "apache-2.0",
    "apache-license": "apache-2.0",
    "bsd-2": "bsd-2-clause",
    "bsd-3": "bsd-3-clause",
    "cc-by-nc": "cc-by-nc-4.0",
    "cc-by-nd": "cc-by-nd-4.0",
    "cc-by-sa": "cc-by-sa-4.0",
    "freebsd": "bsd-2-clause",
    "mit-license": "mit",
    "new-bsd": "bsd-3-clause",
    "public-domain": "unlicense",
    "simplified-bsd": "bsd-2-clause",
    "the-mit-license": "mit",
}
# Keys that state "no license information" rather than naming a license.
_NO_LICENSE_KEYS = frozenset(
    {
        "", "-", "n/a", "na", "none", "no-license", "noassertion", "no-assertion",
        "not-licensed", "null", "other", "see-license-file", "unlicensed", "unknown",
    }
)


def _expand_license_ids(base_ids: Sequence[str]) -> frozenset:
    ids = set()
    for base in base_ids:
        ids.add(base)
        for suffix in ("-only", "-or-later", "-later", "+"):
            ids.add(base + suffix)
    return frozenset(ids)


PERMISSIVE_LICENSE_IDS = _expand_license_ids(_PERMISSIVE_BASE_IDS)
RESTRICTED_LICENSE_IDS = _expand_license_ids(_RESTRICTED_BASE_IDS)

# Evaluated in order; the first restricted match becomes the reported license key.
# Fail-closed rule: permissive patterns are never consulted for the verdict when
# any restricted pattern matched.
RESTRICTED_SIGNATURES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("commons-clause", re.compile(r"commons\s+clause", re.I)),
    ("polyform", re.compile(r"polyform", re.I)),
    (
        "cc-by-nc",
        re.compile(
            r"cc[-\s]?by[-\s]?nc|creative\s+commons[^\n]{0,80}non[-\s]?commercial"
            r"|(?<!or\s)(?<!and\s)\bnon[-\s]?commercial\b",
            re.I,
        ),
    ),
    ("sspl-1.0", re.compile(r"\bsspl\b|server\s+side\s+public\s+license", re.I)),
    ("rsalv2", re.compile(r"\brsal\b|redis\s+source\s+available\s+license", re.I)),
    ("busl-1.1", re.compile(r"\bbusl\b|business\s+source\s+license", re.I)),
    ("bsl-1.1", re.compile(r"\bbsl\b(?!-?1\.0)", re.I)),
    ("mpl-2.0", re.compile(r"\bmpl\b|mozilla\s+public\s+license", re.I)),
    ("gpl-3.0", re.compile(r"\bgpl|gnu\s+general\s+public\s+license", re.I)),
    ("lgpl-3.0", re.compile(r"\blgpl|lesser\s+general\s+public\s+license", re.I)),
    ("agpl-3.0", re.compile(r"\bagpl|affero\s+general\s+public\s+license", re.I)),
    ("eupl-1.2", re.compile(r"\beupl\b|european\s+union\s+public\s+license", re.I)),
    ("elastic-license-2.0", re.compile(r"elastic\s+license", re.I)),
)

PERMISSIVE_SIGNATURES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("apache-2.0", re.compile(r"apache\s+license|apache-2\.0|apache\s+software\s+foundation", re.I)),
    ("mit", re.compile(r"\bmit\s+license|permission\s+is\s+hereby\s+granted,\s+free\s+of\s+charge", re.I)),
    ("bsd-3-clause", re.compile(r"bsd\s+3[-\s]?clause|(?:neither\s+the\s+name\s+of\s+.*?\s+nor\s+the\s+names\s+of\s+its\s+contributors)", re.I)),
    ("bsd-2-clause", re.compile(r"bsd\s+2[-\s]?clause", re.I)),
    (
        "bsd",
        re.compile(r"redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms|\bbsd\s+license\b", re.I),
    ),
    ("isc", re.compile(r"\bisc\s+license|permission\s+to\s+use,\s+copy,\s+modify", re.I)),
    ("unlicense", re.compile(r"\bunlicense\b|free\s+and\s+unencumbered\s+software", re.I)),
    ("cc0-1.0", re.compile(r"\bcc0\b|creative\s+commons\s+zero", re.I)),
    ("bsl-1.0", re.compile(r"boost\s+software\s+license|bsl-1\.0", re.I)),
    ("wtfpl", re.compile(r"\bwtfpl\b", re.I)),
    ("zlib", re.compile(r"\bzlib\b", re.I)),
)

# Not licenses: used to detect conflicts and explain a NEEDS_REVIEW verdict.
RESERVED_RIGHTS_SIGNATURES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("proprietary-notice", re.compile(r"\bproprietary\b|all\s+rights\s+reserved", re.I)),
    ("negation-notice", re.compile(r"\bnot\s+licensed\s+under\b|\bnot\s+(?:an?\s+)?(?:open\s*source|free\s*software)\b", re.I)),
)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_key(raw: str) -> str:
    key = (raw or "").strip().lower()
    key = re.sub(r"[\s_]+", "-", key)
    return re.sub(r"-{2,}", "-", key).strip("-.")


def _expression_tokens(expression: str) -> List[str]:
    """Split an SPDX-style expression (``MIT OR Apache-2.0``) into license ids."""
    cleaned = re.sub(r"[()\[\]]", " ", (expression or "").lower())
    parts = re.split(r"\s+and\s+|\s+or\s+|\s+with\s+|[,/;|]|\s+", cleaned)
    tokens: List[str] = []
    for part in parts:
        token = part.strip().strip(".").strip("'\"")
        if not token or token in {"and", "or", "with"}:
            continue
        tokens.append(_LICENSE_ID_ALIASES.get(token, token))
    return tokens


def _match_sample(match: "re.Match[str]", limit: int = 80) -> str:
    return re.sub(r"\s+", " ", match.group(0)).strip()[:limit]


def _signature_hits(
    signatures: Sequence[Tuple[str, "re.Pattern[str]"]],
    text: str,
    *,
    window: int = 400,
) -> List[Tuple[str, str]]:
    """Match signatures, ranking declarations from the document header first.

    A license's own name sits at the top of its text, while references to other
    licenses (GPLv3 section 13 pointing at the Affero GPL, MPL naming the AGPL as
    a secondary license) appear deep in the body. Matches inside the header
    window rank first, then the earliest position in the document, and finally
    the declared signature order. The ranking only decides which key is reported;
    the verdict is restricted whenever any restricted signature matched.
    """
    ranked = []
    for index, (license_id, pattern) in enumerate(signatures):
        match = pattern.search(text or "")
        if match:
            tier = 0 if match.start() <= window else 1
            ranked.append((tier, match.start(), index, license_id, _match_sample(match)))
    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    return [(license_id, sample) for _, _, _, license_id, sample in ranked]


def _license_matches(restricted: Dict[str, str], permissive: Dict[str, str]) -> List[Dict[str, str]]:
    matches = [{"license": key, "kind": "restricted", "matched": sample} for key, sample in restricted.items()]
    matches += [{"license": key, "kind": "permissive", "matched": sample} for key, sample in permissive.items()]
    return matches


def _classify_identifier_tokens(raw: str, label: str) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """Split an identifier/expression into (restricted, permissive, unrecognized).

    SPDX license *exceptions* (`-exception`) only add permissions and never grant
    a license on their own, so they are ignored instead of blocking the verdict.
    """
    restricted: Dict[str, str] = {}
    permissive: Dict[str, str] = {}
    unrecognized: List[str] = []
    for token in _expression_tokens(raw):
        if token in RESTRICTED_LICENSE_IDS:
            restricted.setdefault(token, f"{label}: {raw}"[:120])
        elif token in PERMISSIVE_LICENSE_IDS:
            permissive.setdefault(token, f"{label}: {raw}"[:120])
        elif "exception" in token:
            continue
        else:
            unrecognized.append(token)
    return restricted, permissive, unrecognized


def _finish_assessment(
    restricted: Dict[str, str],
    permissive: Dict[str, str],
    text: str,
    unrecognized: Sequence[str] = (),
) -> Dict[str, Any]:
    matches = _license_matches(restricted, permissive)
    if restricted:
        reasons = [f"restricted license signal: {key} (matched {sample!r})" for key, sample in restricted.items()]
        if permissive:
            reasons.append(
                "permissive mentions ignored because restricted terms take precedence: "
                + ", ".join(permissive)
            )
        return {
            "verdict": "restricted",
            "keys": list(restricted),
            "matches": matches,
            "reasons": reasons,
        }
    # Check for negation or proprietary conflicts that defeat permissive text
    conflicts = []
    for name, pattern in RESERVED_RIGHTS_SIGNATURES:
        match = pattern.search(text or "")
        if match:
            # If explicit negation or proprietary notice appears, verify if affirmative grant is genuine
            if name == "negation-notice" or "proprietary" in match.group(0).lower():
                conflicts.append(f"{name}: {_match_sample(match)!r}")

    if conflicts and permissive:
        return {
            "verdict": "needs_review",
            "keys": list(permissive) or ["unknown"],
            "matches": matches,
            "reasons": [
                f"conflicting notice found alongside permissive terms: {', '.join(conflicts)}; requires manual review before distilling"
            ],
        }

    if permissive and not unrecognized:
        return {
            "verdict": "permissive",
            "keys": list(permissive),
            "matches": matches,
            "reasons": [],
        }
    if permissive or unrecognized:
        # An unrecognized identifier in a declared expression blocks the permissive
        # verdict; DISTILL is only reachable from fully recognized identifiers.
        reasons = []
        if unrecognized:
            reasons.append(
                "unrecognized license identifier(s) in the declared expression: "
                + ", ".join(dict.fromkeys(unrecognized))
            )
        if permissive:
            reasons.append(
                "declared expression also lists permissive terms (" + ", ".join(permissive) + "); resolve the scope before distilling"
            )
        return {
            "verdict": "needs_review",
            "keys": list(permissive) or ["unknown"],
            "matches": matches,
            "reasons": reasons,
        }
    reasons = ["no recognized license grant found in license text"]
    for name, pattern in RESERVED_RIGHTS_SIGNATURES:
        match = pattern.search(text or "")
        if match:
            reasons.append(f"{name}: no open-source grant (matched {_match_sample(match)!r})")
            break
    return {"verdict": "needs_review", "keys": ["unknown"], "matches": matches, "reasons": reasons}


def assess_license_text(text: str) -> Dict[str, Any]:
    """Fail-closed license assessment of raw license text."""
    text = text or ""
    restricted: Dict[str, str] = {}
    permissive: Dict[str, str] = {}

    # 1. Explicit machine-readable identifiers win over prose: SPDX headers, and a
    #    file whose entire content is identifiers ("MIT", "Apache-2.0", "MIT OR Apache-2.0").
    stripped = text.strip()
    expressions: List[Tuple[str, str]] = [
        (match.strip(), "SPDX-License-Identifier") for match in SPDX_IDENTIFIER_RE.findall(text)
    ]
    if stripped and "\n" not in stripped and len(stripped) <= 200:
        bare_tokens = _expression_tokens(stripped)
        if bare_tokens and all(
            token in RESTRICTED_LICENSE_IDS or token in PERMISSIVE_LICENSE_IDS for token in bare_tokens
        ):
            expressions.append((stripped, "license identifier"))
    unrecognized: List[str] = []
    for expression, label in expressions:
        found_restricted, found_permissive, found_unrecognized = _classify_identifier_tokens(expression, label)
        restricted.update({key: value for key, value in found_restricted.items() if key not in restricted})
        permissive.update({key: value for key, value in found_permissive.items() if key not in permissive})
        unrecognized.extend(found_unrecognized)

    # 2. Keyword signatures. Restricted patterns are matched first and always win.
    for license_id, sample in _signature_hits(RESTRICTED_SIGNATURES, text):
        restricted.setdefault(license_id, sample)
    for license_id, sample in _signature_hits(PERMISSIVE_SIGNATURES, text):
        permissive.setdefault(license_id, sample)

    return _finish_assessment(restricted, permissive, text, unrecognized)


def classify_license(raw_key: str | None) -> Dict[str, Any]:
    """Fail-closed assessment of a license identifier/expression (gh metadata key)."""
    raw = (raw_key or "").strip()
    restricted, permissive, unrecognized = _classify_identifier_tokens(raw, "license identifier")
    if restricted or permissive:
        return _finish_assessment(restricted, permissive, raw, unrecognized)
    if not raw or _normalize_key(raw) in _NO_LICENSE_KEYS:
        return {
            "verdict": "needs_review",
            "keys": ["unknown"],
            "matches": [],
            "reasons": [f"no usable license identifier: {raw_key!r}"],
        }
    # No recognized identifier token: fall back to signature scanning of the raw value
    # (covers free-text keys such as "GNU General Public License v3.0").
    assessment = assess_license_text(raw)
    if assessment["verdict"] == "needs_review":
        assessment = dict(assessment)
        assessment["reasons"] = [f"unrecognized license identifier: {raw!r}"]
    return assessment


def audit_license(key: str) -> Tuple[str, List[str]]:
    """Backwards-compatible wrapper: (license_verdict, reasons) for a license key."""
    assessment = classify_license(key)
    return assessment["verdict"], assessment["reasons"]


def _combine_assessments(assessments: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Union of several license findings with restricted evidence outranking permissive."""
    restricted: Dict[str, str] = {}
    permissive: Dict[str, str] = {}
    needs_review_reasons: List[str] = []
    for assessment in assessments:
        for match in assessment.get("matches", []):
            bucket = restricted if match["kind"] == "restricted" else permissive
            bucket.setdefault(match["license"], match["matched"])
        if assessment.get("verdict") == "needs_review":
            needs_review_reasons.extend(assessment.get("reasons", []))
    result = _finish_assessment(restricted, permissive, "")
    if needs_review_reasons and result["verdict"] != "restricted":
        # Restricted evidence still wins; otherwise a single unresolved file keeps the
        # repository out of DISTILL.
        result = dict(result)
        result["verdict"] = "needs_review"
        result["reasons"] = list(dict.fromkeys(needs_review_reasons))
    return result


def _is_ignored_dir(name: str) -> bool:
    lowered = name.lower()
    return lowered in IGNORED_DIR_NAMES or lowered.endswith(IGNORED_DIR_SUFFIXES)


def _is_ignored_file(name: str) -> bool:
    if name in IGNORED_FILE_NAMES:
        return True
    return Path(name).suffix.lower() in IGNORED_FILE_SUFFIXES


def iter_repo_files(repo: Path, *, max_files: int = 20000) -> Tuple[List[Path], List[str]]:
    """Walk the repository, pruning VCS/dependency/cache/build directories.

    Returns (files, pruned_directories) with deterministic ordering.
    """
    files: List[Path] = []
    pruned: List[str] = []
    for dirpath, dirnames, filenames in os.walk(repo, topdown=True, followlinks=False):
        kept = []
        for name in sorted(dirnames):
            if _is_ignored_dir(name):
                pruned.append(os.path.relpath(os.path.join(dirpath, name), str(repo)))
            else:
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            if _is_ignored_file(name):
                continue
            files.append(Path(dirpath) / name)
            if len(files) >= max_files:
                dirnames[:] = []
                return files, sorted(pruned)
    return files, sorted(pruned)


def _read_text_file(path: Path, *, max_bytes: int = 262144) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
    except OSError:
        return ""


def _relative(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def _is_license_file(relative_parts: Sequence[str]) -> bool:
    name = relative_parts[-1]
    if LICENSE_FILE_RE.match(name):
        return True
    if len(relative_parts) >= 2 and relative_parts[-2].lower() in LICENSE_DIR_NAMES:
        return True
    return False


def collect_license_evidence(
    repo: Path, files: Sequence[Path], *, file_limit: int = 40, header_limit: int = 40
) -> Dict[str, Any]:
    """Read every LICENSE/LICENCE/COPYING/UNLICENSE file, then SPDX headers if none."""
    candidates: List[Path] = []
    for path in files:
        parts = _relative(repo, path).split("/")
        if _is_license_file(parts):
            candidates.append(path)
    candidates.sort(key=lambda path: _relative(repo, path))

    truncated = len(candidates) > file_limit
    reports: List[Dict[str, Any]] = []
    assessments: List[Dict[str, Any]] = []
    for path in candidates[:file_limit]:
        text = _read_text_file(path)
        if not text.strip():
            continue
        assessment = assess_license_text(text)
        assessments.append(assessment)
        reports.append(
            {
                "path": _relative(repo, path),
                "license_key": assessment["keys"][0],
                "license_verdict": assessment["verdict"],
                "matched": [match["license"] for match in assessment["matches"]],
            }
        )

    source = "license_file"
    if not assessments:
        header_expressions: List[str] = []
        header_files = [
            path
            for path in files
            if len(_relative(repo, path).split("/")) == 1 and path.suffix.lower() in CODE_SUFFIXES
        ]
        for path in sorted(header_files, key=lambda path: _relative(repo, path))[:header_limit]:
            head = _read_text_file(path, max_bytes=4096)
            header_expressions.extend(match.strip() for match in SPDX_IDENTIFIER_RE.findall(head))
        if header_expressions:
            source = "spdx_headers"
            for expression in header_expressions:
                assessments.append(classify_license(expression))

    if not assessments:
        return {
            "source": "none",
            "license_key": "unknown",
            "verdict": "needs_review",
            "matches": [],
            "files": reports,
            "truncated": truncated,
            "reasons": [
                "no license file (LICENSE/LICENCE/COPYING/UNLICENSE) or SPDX-License-Identifier header found"
            ],
        }

    combined = _combine_assessments(assessments)
    if truncated and combined["verdict"] == "permissive":
        combined["verdict"] = "needs_review"
        combined["reasons"].append("license evidence exceeded scan limits (truncated); manual review required before DISTILL")
    # Prefer the most specific identifier per license file over signature echoes.
    keys: List[str] = []
    for report in reports:
        key = report["license_key"]
        if key not in keys:
            keys.append(key)
    if source == "spdx_headers":
        keys = list(combined["keys"])
    if combined["verdict"] == "restricted":
        keys = [key for key in keys if key in combined["keys"]] or list(combined["keys"])
    return {
        "source": source,
        "license_key": " / ".join(keys) if keys else combined["keys"][0],
        "verdict": combined["verdict"],
        "matches": combined["matches"],
        "files": reports,
        "truncated": truncated,
        "reasons": combined["reasons"],
    }


def verdict_for_license(license_verdict: str) -> str:
    if license_verdict == "permissive":
        return "DISTILL"
    if license_verdict == "restricted":
        return "INTERNAL_ONLY"
    return "NEEDS_REVIEW"


def audit_metadata(path: Path) -> Dict[str, Any]:
    meta = json.loads(path.read_text(encoding="utf-8"))
    license_info = meta.get("licenseInfo") or {}
    key = (license_info.get("key") or meta.get("license") or "unknown").lower()
    assessment = classify_license(key)
    license_verdict = assessment["verdict"]
    reasons = list(assessment["reasons"])
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
        "license_matches": assessment["matches"],
        "freshness": freshness,
        "age_days": age_days,
        "stars": meta.get("stargazerCount"),
        "forks": meta.get("forkCount"),
        "distillation_verdict": verdict,
        "conversion_recommendation": CONVERSION_RECOMMENDATION,
        "reasons": reasons,
    }


def audit_local_repo(repo: Path) -> Dict[str, Any]:
    if not repo.exists() or not repo.is_dir():
        return {
            "mode": "local_repo",
            "repo_path": str(repo),
            "distillation_verdict": "BLOCKED",
            "conversion_recommendation": CONVERSION_RECOMMENDATION,
            "error": f"not a directory: {repo}",
        }

    names = {p.name for p in repo.iterdir()}
    files, pruned_dirs = iter_repo_files(repo)
    evidence = collect_license_evidence(repo, files)
    license_verdict = evidence["verdict"]
    reasons = list(evidence["reasons"])

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

    return {
        "mode": "local_repo",
        "repo_path": str(repo),
        "license_key": evidence["license_key"],
        "license_verdict": license_verdict,
        "license_source": evidence["source"],
        "distillation_verdict": verdict_for_license(license_verdict),
        "conversion_recommendation": CONVERSION_RECOMMENDATION,
        "top_level": sorted(names)[:80],
        "license_files": evidence["files"][:20],
        "license_files_truncated": evidence["truncated"],
        "license_matches": evidence["matches"],
        "ignored_directories": pruned_dirs[:40],
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
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo_path", nargs="?", type=Path)
    parser.add_argument("--repo", dest="repo_flag", type=Path, help="Local repository path")
    parser.add_argument("--metadata", type=Path, help="GitHub metadata JSON from gh repo view")
    parser.add_argument(
        "--no-hint",
        action="store_true",
        help="Never print the human-readable conversion hint on stderr",
    )
    args = parser.parse_args()
    repo = args.repo_flag or args.repo_path

    if args.metadata:
        result = audit_metadata(args.metadata)
    elif repo:
        result = audit_local_repo(repo)
    else:
        parser.error("provide repo_path/--repo or --metadata")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not args.no_hint and sys.stdout.isatty():
        print(result["conversion_recommendation"], file=sys.stderr)
    return 0 if result.get("distillation_verdict") != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())

---
name: repo-distillation-preflight
description: >
  Audit a local repository before turning it into an Agent Skill. Detects license
  signals (permissive, copyleft, or unknown), docs/tests/examples, and file inventory.
  Use when the user asks whether local code is safe to distill, package, reuse, or
  commercially distribute as an Agent Skill, especially for GPL, LGPL, AGPL, MIT,
  Apache, license review, source provenance, or repository preflight questions.
license: MIT
compatibility: Requires Python 3.9+ and a local directory. Uses only the Python standard library and makes no network requests.
---

# Repository distillation preflight

Run a deterministic, **local-only** first gate before creating an Agent Skill from a repository. It reads the directory you provide; it does not clone remote URLs, copy source, generate a skill, or grant commercial permission.

## Run it

From this skill directory:

```bash
python3 scripts/audit_repo_for_distillation.py --repo /absolute/path/to/repository
```

The program prints JSON. Capture that output in your decision record rather than paraphrasing it.

## Interpret the verdict conservatively

| `distillation_verdict` | What the script observed | What to do next |
|---|---|---|
| `DISTILL` | A recognized permissive license signal (MIT, Apache-2.0, BSD, or ISC) | Check provenance, notices, file-level exceptions, and your authorization before reusing anything. |
| `INTERNAL_ONLY` | GPL, LGPL, or AGPL terms detected | Do not package derived material as a commercial skill. Keep it internal or obtain qualified legal guidance. |
| `NEEDS_REVIEW` | Missing/unknown license or incomplete evidence | Stop. Locate the authoritative license and scope before distilling. |
| `BLOCKED` | `--repo` is not a directory | Correct the path. No generated artifact is a valid result here. |

`DISTILL` does **not** mean:

- the repository is high quality;
- every file has the same license;
- its authors authorized your commercial distribution;
- an agent can turn it into a complete workflow;
- the output will load in every coding-agent host.

## Minimum decision record

For every repository considered for reuse, record:

1. absolute or repository-relative path audited;
2. exact command;
3. full JSON result;
4. source/provenance owner and the file(s) actually considered;
5. decision: `reject`, `internal-only`, `manual review`, or `distill`;
6. any required attribution, notices, or commercial permission.

Do not use a one-line green verdict as a substitute for this record.

## Failure modes and recovery

| Symptom | Meaning | Recovery |
|---|---|---|
| `BLOCKED` / `not a directory` | Wrong path or missing checkout | Use an existing local directory; this tool deliberately does not fetch GitHub. |
| `NEEDS_REVIEW` / `unknown` | No recognized top-level license signal | Find the applicable license; do not guess from a README claim. |
| `INTERNAL_ONLY` | Copyleft signal found | Exclude it from commercial distillation; preserve the finding in the record. |
| `DISTILL` but a vendor file has a different notice | Top-level detection is insufficient | Manually inspect file-level headers and dependencies. |
| Invalid JSON input/output expectation | This tool only emits report JSON | Save the report; it is a preflight, not a scaffold generator. |

## Boundary

This skill is a technical license-signal check, not legal advice. It is intentionally conservative and only assesses local evidence. For a reproducible scaffold, package validator, and end-to-end fixture after the preflight, use a separate implementation workflow.

# Repository distillation preflight

Builders want Agent Skills from local repos. The first mess is usually **license signals and boundaries**, not the skill template.

This skill is a **local-only Python preflight**: it audits a directory you already have for license signals, docs/tests/examples cues, and a file inventory—so you can decide whether distillation is even in bounds.

It is **not** a skill generator, **not** a cloner, and **not** legal advice.

## Boundaries (read before you run)

| This preflight does | This preflight does **not** |
| --- | --- |
| Run locally on Python 3.9+ (stdlib only) | Make network requests |
| Read the directory you pass with `--repo` | Clone remote URLs or fetch GitHub for you |
| Emit a JSON report + `distillation_verdict` | Generate an Agent Skill package |
| Surface license signals (permissive / copyleft / unknown) | Grant commercial permission or replace counsel |

## Run it

From this skill directory:

```bash
python3 scripts/audit_repo_for_distillation.py --repo /absolute/path/to/repository
```

The program prints JSON. Capture that output in your decision record rather than paraphrasing it.

## How to read the verdict

| `distillation_verdict` | What the script observed | What to do next |
| --- | --- | --- |
| `DISTILL` | Recognized permissive license signal (MIT, Apache-2.0, BSD, or ISC) | Still check provenance, notices, file-level exceptions, and your authorization before reusing anything. |
| `INTERNAL_ONLY` | GPL, LGPL, or AGPL terms detected | Do not package derived material as a commercial skill. Keep it internal or get qualified legal guidance. |
| `NEEDS_REVIEW` | Missing/unknown license or incomplete evidence | Stop. Locate the authoritative license and scope before distilling. |
| `BLOCKED` | `--repo` is not a directory | Correct the path. No generated artifact is valid here. |

`DISTILL` does **not** mean the repo is high quality, every file shares one license, authors authorized your commercial distribution, or an agent can turn it into a complete workflow.

## Minimum decision record

Keep for every repo you consider:

1. Absolute or repo-relative path audited  
2. Exact command  
3. Full JSON result  
4. Provenance owner and files actually considered  
5. Decision: `reject` / `internal-only` / `manual review` / `distill`  
6. Required attribution, notices, or commercial permission  

Do not treat a one-line green verdict as the record.

## What next after `DISTILL`

Preflight stays **free**. If—and only if—you got `DISTILL` and your decision record still says go, use a **separate** one-time pack for the skill skeleton and packaging check:

- [Agentic Distiller — $29](https://george-onair.whop.site/shop/agentic-distiller) (George O'Nair / Field Lab)  
- Overview: [Turn a local repo into an Agent Skill](https://george-onair.whop.site/workflows/agents)

Distiller does not replace this preflight. It does not host an agent, open PRs, or invent a finished business workflow from an unauthorized public link.

## What not to do after `INTERNAL_ONLY` / `NEEDS_REVIEW`

- Do **not** skip to Distiller to "fix" a red or amber verdict.  
- Do **not** guess a license from a README marketing line.  
- Do **not** treat this JSON as legal clearance.

## Failure modes

| Symptom | Meaning | Recovery |
| --- | --- | --- |
| `BLOCKED` / not a directory | Wrong path or missing checkout | Use an existing local directory; this tool deliberately does not fetch GitHub. |
| `NEEDS_REVIEW` / unknown | No recognized top-level license signal | Find the applicable license; do not guess. |
| `INTERNAL_ONLY` | Copyleft signal found | Exclude from commercial distillation; keep the finding in the record. |
| `DISTILL` but a vendor file has another notice | Top-level detection is insufficient | Inspect file-level headers and dependencies manually. |

## About this skill (short)

Repo distillation preflight is a local Python 3.9+ check for license signals and inventory before you turn a repository into an Agent Skill. It does not clone remotes, generate a skill, grant commercial permission, or give legal advice. Verdicts are DISTILL, INTERNAL_ONLY, NEEDS_REVIEW, or BLOCKED. After a conservative DISTILL and a written decision record, Agentic Distiller ($29) is an optional separate pack for skeleton and packaging—not a hosted agent.

## License

This skill is MIT (see frontmatter in `SKILL.md`). That license applies to **this** tooling, not to the repository you audit.

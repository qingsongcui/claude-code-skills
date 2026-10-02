# A real repo preflight and skill skeleton

I ran both tools on this public MIT repository at commit
`4bfd69f3c20f263c3c9b047d5c8ce5d80f08d9cf` on 2026-10-02.
The local checkout was clean. This is my own run, not a customer result.

## Start with the free preflight

Set `REPO` to a local checkout of this repository and run:

```sh
python3 "$REPO/plugins/starter/skills/repo-distillation-preflight/scripts/audit_repo_for_distillation.py" \
  --repo "$REPO" --no-hint
```

The JSON contained:

```json
{
  "license_key": "mit",
  "license_verdict": "permissive",
  "distillation_verdict": "DISTILL",
  "has_docs": true,
  "has_tests": false,
  "has_examples": true,
  "file_counts": {"total": 22, "python": 4, "javascript_or_typescript": 0, "config": 3}
}
```

The report inventoried this checkout and detected a permissive license signal.
It did not create a Skill or establish that every file can be reused. Review
provenance, notices, and your own authorization before packaging anything.

## What the optional $29 package added

From the downloaded Agentic Distiller package root, I ran:

```sh
python3 skills/github-repo-skill-distiller/scripts/distill_local_repo.py \
  --repo "$REPO" \
  --name field-lab-repo-maintainer \
  --output /tmp/field-lab-demo
```

The CLI returned `"status": "PASS"` and generated a
`field-lab-repo-maintainer/` directory with `SKILL.md`, a source evidence
map placeholder, and script, template, and example stubs. The evidence map
only says `Fill this from repo inspection evidence.` Its generated
`scripts/tool.py` still says:

```python
print('TODO: implement tool')
```

That `PASS` means the package passed basic frontmatter, Python compilation,
and license-term checks. It is **not** a working repository-maintenance agent.
I would still need to choose a concrete task, implement the script and
instructions, and test it in the target agent. Agent discovery in Claude Code,
Codex, Cursor, and OpenCode has not been independently verified for this
generated Skill.

## A deliberate failure

Pointing the free preflight at a missing local path returned
`"distillation_verdict": "BLOCKED"`. The tool does not clone a GitHub URL or
guess which checkout you meant. Fix the path and rerun.

**Takeaway:** The [free preflight](../../plugins/starter/skills/repo-distillation-preflight/)
answers whether a local repo has basic license and layout signals. The paid
package adds a scaffold and structural checks. Neither tool automatically
extracts business logic, scrubs secrets, or produces a production-ready Skill.

If you try the free preflight on your own local repo, [share a sanitized verdict or blocker](https://github.com/qingsongcui/claude-code-skills/issues/new?template=preflight-feedback.md). Please do not post the full JSON, private paths, source, or secrets.

---
name: repo-distillation-preflight
description: >
  Audit a local repository before turning it into an Agent Skill. Reports license
  class (permissive vs copyleft vs unknown), docs/tests/examples, and file inventory.
  Use when the user asks whether a repo is safe to distill or commercially reuse.
language: en-US
---

# Repo distillation preflight

Run the bundled auditor. Do not copy source. `DISTILL` means permissive license only, not "this repo is high quality."

```bash
python3 scripts/audit_repo_for_distillation.py --repo /path/to/local-repo
```

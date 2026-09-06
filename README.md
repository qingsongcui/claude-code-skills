# claude-code-skills

Free [Agent Skills](https://agentskills.io/specification) by **George O'Nair**.

This repository is a plugin marketplace. Three skills are included:

| Skill | When to use it |
|---|---|
| `skill-authoring` | Your `SKILL.md` never loads, or you need a file the agent will actually auto-invoke. |
| `mcp-server-scaffold` | You want the smallest MCP server (one tool, stdio). |
| `repo-distillation-preflight` | You want to know if a local repo is license-safe to turn into a skill. |

## Install

Claude Code:

```
/plugin marketplace add qingsongcui/claude-code-skills
/plugin install starter@george-onair-skills
```

Any Agent Skills client (Codex, Cursor, OpenCode, Claude Code):

```
git clone https://github.com/qingsongcui/claude-code-skills.git
# copy plugins/starter/skills/ into your skills directory
```

Preflight CLI (Python 3, stdlib only):

```
python3 plugins/starter/skills/repo-distillation-preflight/scripts/audit_repo_for_distillation.py --repo /path/to/local-repo
```

`DISTILL` means permissive license. `INTERNAL_ONLY` means copyleft — do not ship as a commercial skill.

## Full pack

The paid **Agentic Distiller** adds skill scaffolding, packaging validation, a one-shot pipeline, book-distiller templates, and a sample-todo fixture.

https://whop.com/github-bad1/agentic-distiller

It is not a one-click compiler that invents production workflows from GitHub. Agent runtime discovery is documented, not independently verified in that listing.

## License

MIT

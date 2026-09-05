# claude-code-skills

Free starter [Agent Skills](https://code.claude.com/docs/en/skills) for Claude Code and Cursor. Written by **George O'Nair**.

This repository is a [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces). Two skills are included:

| Skill | When to use it |
|---|---|
| `skill-authoring` | Your `SKILL.md` never loads, or you need a file the agent will actually auto-invoke. |
| `mcp-server-scaffold` | You want the smallest MCP server (one tool, stdio) wired into Claude Code. |

## Install

In Claude Code:

```
/plugin marketplace add qingsongcui/claude-code-skills
/plugin install starter@george-onair-skills
```

Then invoke `/skill-authoring` or `/mcp-server-scaffold`, or just describe the job in natural language.

Manual copy (any Agent Skills client):

```
git clone https://github.com/qingsongcui/claude-code-skills.git
# point your client at plugins/starter/skills/
```

## What this is not

Not a dump of random prompt files. Each skill is a procedure with paths, failure modes, and an install check.

A larger production pack (evals, observability, security, multi-agent orchestration) is distributed separately. This repo stays the free starter.

## License

MIT

---
name: skill-authoring
description: >
  Write, debug, and install Agent Skills (SKILL.md) for Claude Code, Cursor, and
  other agents that follow the Agent Skills spec. Use when a skill does not load,
  is never auto-invoked, lives in the wrong directory, or the user asks how to
  author SKILL.md, plugin marketplaces, or custom commands.
---

# Skill authoring

Produce a skill that an agent will actually load. Most "my skill does nothing" bugs are layout, frontmatter, or description problems — not model quality.

## Layout

One skill = one directory + `SKILL.md`:

```
skill-name/
  SKILL.md          # required
  references/       # optional, load on demand
  scripts/          # optional
```

Where it lives decides who sees it:

| Scope | Path |
|---|---|
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| This repo | `.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` |

Directory name becomes `/skill-name`. Use kebab-case. Do not put the body in `.claude/commands/` unless you intentionally want a flat command file.

## Frontmatter (the part that decides auto-invoke)

```yaml
---
name: skill-name
description: >
  What it does, plus the user phrasing that should trigger it.
  Include tool names, error symptoms, and "use when" language.
---
```

Rules:

- `description` is the trigger. If it only says "helper for tasks", the agent will not pick it.
- Keep `SKILL.md` body short. Put long reference material in `references/` and tell the agent when to open it.
- Do not duplicate the entire company wiki into one skill.

## Authoring checklist

1. Name the job in one sentence (example: "scaffold an MCP server that exposes one tool").
2. List 5–10 user utterances that should load it. Put those in `description`.
3. Write the procedure as numbered steps with exact file paths and commands.
4. Add a "failure modes" section (wrong path, YAML broken, description too vague).
5. Install, restart or reload, then invoke with `/skill-name` and with a natural-language prompt.

## Debug a skill that never runs

1. Confirm the file is exactly `SKILL.md` (not `skill.md` or `README.md`).
2. Confirm it is not nested extra levels (`skills/foo/bar/SKILL.md` when the plugin expects `skills/foo/SKILL.md`).
3. Parse the YAML. A missing closing `---` silently drops the skill.
4. Read `description`. If it does not mention the words the user actually typed, rewrite it.
5. In Claude Code, run `/skills` and check whether the name appears. If it does not, the file is not on a watched path.
6. Personal vs project conflict: same name in `~/.claude/skills/` overrides the project copy.

## Plugin marketplace (optional distribution)

To ship several skills as one install:

```
repo/
  .claude-plugin/marketplace.json
  plugins/starter/.claude-plugin/plugin.json
  plugins/starter/skills/<name>/SKILL.md
```

Users add the catalog, then install one plugin:

```
/plugin marketplace add qingsongcui/claude-code-skills
/plugin install starter@george-onair-skills
```

Do not tell users to "copy a folder path into chat" as the primary install path.

## Output format when you write a skill for the user

Create the directory, write `SKILL.md`, and print:

- install path used
- `/slash` name
- one natural-language prompt that should auto-trigger it
- one thing you deliberately left out of the body (and where it lives instead)

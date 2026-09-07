---
name: skill-authoring
description: >
  Write, debug, and install Agent Skills (SKILL.md). Use when a skill is ignored,
  never auto-invoked, has YAML/frontmatter errors, is in the wrong directory, or
  when the user asks to author a skill, choose trigger words, distribute a Claude
  Code plugin marketplace, or diagnose a SKILL.md loading failure.
license: MIT
compatibility: Works with Agent Skills-compatible hosts. Claude Code plugin examples require a current Claude Code installation.
---

# Skill authoring

Produce a skill that a host can discover and an agent can select. Treat “the file exists” as a starting condition, not proof that the skill is usable.

Official format reference: <https://agentskills.io/specification>.

## First decide the delivery mode

| Delivery mode | Put the skill here | Verify it with |
|---|---|---|
| Claude Code personal skill | `~/.claude/skills/<name>/SKILL.md` | Restart/reload, then invoke or ask for a matching task |
| Claude Code project skill | `.claude/skills/<name>/SKILL.md` | Open the target project, then test in that project |
| Claude Code plugin skill | `<plugin>/skills/<name>/SKILL.md` | Install the plugin, reload plugins, use `/<plugin>:<skill>` |
| Another Agent Skills host | That host’s documented skill directory | Host-specific discovery check |

Do not promise universal auto-discovery. Hosts may use different paths, activation rules, and tool permissions.

## Build the smallest valid skill

One skill is one directory with one required file:

```text
skill-name/
├── SKILL.md
├── scripts/       # optional executable helpers
├── references/    # optional, open only when needed
└── assets/        # optional templates or static data
```

The directory name must match the frontmatter `name`. Per the Agent Skills specification, `name` is lowercase letters, numbers, and hyphens; `description` must say both **what the skill does** and **when to use it**.

```yaml
---
name: todo-cli-maintainer
description: >
  Maintain the sample todo CLI: add, list, and complete todos. Use when the user
  asks to change the todo CLI in this repository. Do not use for other CLIs.
license: MIT
---
```

Why this activates better than `description: Helps with code`:

1. **Artifact**: `todo CLI`
2. **Trigger verbs**: `add`, `list`, `complete`
3. **Boundary**: `this repository`, not every CLI

## Authoring procedure

1. State the job in one sentence. If it contains two unrelated jobs, split the skill.
2. Write 5–10 phrases real users will say. Extract concrete nouns, verbs, symptoms, and exclusions into `description`.
3. Put the shortest safe procedure in `SKILL.md`; move deep reference material into `references/` and link it with a relative path.
4. Add one runnable verification command or observable result. “No error” is not enough.
5. Add a failure mode table: wrong path, bad YAML, missing executable, overly broad trigger.
6. Test two paths: explicit invocation and natural-language matching.

## Debug an ignored skill

Follow this order; do not rewrite prompts before discovery works.

1. **Discovery** — ask the host/agent to list skills matching your skill’s name or trigger words. If it cannot name the skill, this is a path/install problem.
2. **Shape** — confirm exact casing: `skills/<name>/SKILL.md`, no accidental `skills/<name>/<name>/SKILL.md`.
3. **Frontmatter** — confirm opening and closing `---`, valid YAML, matching `name`, and a description with artifact + verbs + boundary.
4. **Scope collision** — temporarily rename or remove duplicate personal/project copies. Do not assume precedence is identical across hosts.
5. **Activation** — use the exact trigger verb in a small prompt. Verify the agent names the skill or executes its stated verification.
6. **Permissions** — if the skill is found but cannot run a command, inspect the host’s tool approval/sandbox setting rather than widening the skill description.

| Symptom | Likely cause | Smallest fix |
|---|---|---|
| Skill is absent from discovery | Wrong directory or plugin not reloaded | Move it one level up; reload/restart |
| Skill appears but is never selected | Description has no real trigger words | Add artifact, verbs, and boundary |
| Skill selects for unrelated work | Description is too broad | Add exclusions and repository/domain terms |
| Skill starts then fails | Referenced script/path is missing | Use relative paths; run the command directly |
| Plugin command cannot be found | Expected un-namespaced command | Use `/<plugin-name>:<skill-name>` |

## Claude Code marketplace distribution

Use this layout:

```text
repo/
├── .claude-plugin/marketplace.json
└── plugins/
    └── starter/
        ├── .claude-plugin/plugin.json
        └── skills/
            └── skill-name/SKILL.md
```

Installation:

```text
/plugin marketplace add owner/repository
/plugin install starter@marketplace-name
/reload-plugins
```

Then run `/<plugin-name>:<skill-name>` — for this repository, `/starter:skill-authoring`.

Every release must bump the plugin `version`; plugin installations are versioned and users otherwise may not receive the update. Source: <https://code.claude.com/docs/en/plugin-marketplaces>.

## Deliverable format

When creating or repairing a skill, report:

- exact install path;
- skill name and plugin-qualified slash command when applicable;
- one natural-language prompt that should select it;
- the verification command/result;
- an explicit limitation that is intentionally out of scope.

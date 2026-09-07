# George O'Nair's Agent Skills Starter

Free, small, local-first [Agent Skills](https://agentskills.io/specification) for coding agents.

**Start here if one of these is your problem:**

| Problem | Install / use |
|---|---|
| “My `SKILL.md` exists but the agent ignores it.” | `skill-authoring` |
| “I need the smallest useful local MCP server.” | `mcp-server-scaffold` |
| “Can I reuse this local repo without pulling copyleft code into a commercial skill?” | `repo-distillation-preflight` |

The repository is a Claude Code plugin marketplace and also a plain Agent Skills directory. The three skills are useful independently; none requires an API key, cloud service, or the paid product.

## Five-minute quickstart

The fastest way to get a useful answer is the repository preflight. Clone this repository, then audit a **local directory you own or are allowed to inspect**:

```bash
git clone https://github.com/qingsongcui/claude-code-skills.git
cd claude-code-skills
python3 plugins/starter/skills/repo-distillation-preflight/scripts/audit_repo_for_distillation.py \
  --repo /absolute/path/to/your-repo
```

The script uses only the Python standard library. It prints JSON with one of these deliberate outcomes:

| Verdict | Meaning | Next action |
|---|---|---|
| `DISTILL` | Detected a permissive license. This is a license signal, not a quality or provenance approval. | Review the source and write a skill for work you are authorized to reuse. |
| `INTERNAL_ONLY` | Detected GPL, LGPL, or AGPL terms. | Keep derivative skills internal; do not package them as commercial IP. |
| `NEEDS_REVIEW` | License or repository evidence is unclear. | Stop and verify the license before distilling. |
| `BLOCKED` | The supplied path is not a directory. | Correct `--repo`; the tool will not fabricate an output skill. |

## Install the skills

### Claude Code plugin marketplace

Claude Code users can install all three skills through the marketplace:

```text
/plugin marketplace add qingsongcui/claude-code-skills
/plugin install starter@george-onair-skills
/reload-plugins
```

Plugin skills are namespaced. For example:

```text
/starter:skill-authoring
/starter:repo-distillation-preflight
```

This follows the official marketplace flow: <https://code.claude.com/docs/en/plugin-marketplaces>.

### Plain Agent Skills clients

For an Agent Skills-compatible host, copy each **individual skill directory** into the host’s skills directory. Do not copy the enclosing `skills/` directory as one nested skill.

```bash
git clone https://github.com/qingsongcui/claude-code-skills.git
cd claude-code-skills

# Example: Codex-compatible user skill directory
mkdir -p "$HOME/.agents/skills"
cp -R plugins/starter/skills/skill-authoring "$HOME/.agents/skills/"
cp -R plugins/starter/skills/mcp-server-scaffold "$HOME/.agents/skills/"
cp -R plugins/starter/skills/repo-distillation-preflight "$HOME/.agents/skills/"
```

For Claude Code without the marketplace, use `~/.claude/skills/` instead. Cursor and OpenCode path/discovery behavior varies by host version; treat installation paths as host documentation, then confirm discovery in that host before relying on auto-invocation.

## Verify the install, not just the files

1. Ask the agent to list skills matching `repo distillation` or `SKILL.md not loading`.
2. Invoke one explicitly: `/starter:repo-distillation-preflight` in Claude Code, or your host’s equivalent.
3. Run the preflight command above against a known local repository.
4. Confirm the result is a JSON verdict. A copied folder alone is not proof that a host discovered it.

The skill format used here follows the public specification: a skill directory contains `SKILL.md` with required `name` and `description` frontmatter. Those fields are the first discovery surface. Source: <https://agentskills.io/specification>.

## What each skill gives you

### `skill-authoring`

A focused debugger for the common “installed but ignored” failure:

- correct directory scope and plugin layout;
- frontmatter that includes the artifact, trigger verbs, and boundary;
- natural-language and slash-command verification;
- failure handling for bad YAML, wrong paths, and duplicate names.

### `mcp-server-scaffold`

A restrained plan for one local stdio MCP tool. It starts with one tool and a smoke test; it deliberately excludes OAuth, HTTP/SSE, and multi-tool abstractions until the first tool responds. For stdio, logs must go to stderr rather than stdout because stdout carries protocol messages. Source: <https://modelcontextprotocol.io/docs/develop/build-server>.

### `repo-distillation-preflight`

A deterministic local license-and-layout audit. It does **not** clone repositories, copy source, certify quality, or authorize commercial reuse. It gives you a reasoned first gate before you turn any local codebase into an Agent Skill.

> Need an evidence-first research workflow rather than another coding skill? See [Evidence-First Research](https://github.com/qingsongcui/evidence-first-research) — source tracking, uncertainty boundaries, and reviewed-answer validation.

## Free starter vs. Agentic Distiller

The free starter is intentionally useful on its own:

| Free here | Paid Agentic Distiller |
|---|---|
| Local license/layout preflight | Preflight plus scaffold, package validation, one-shot pipeline, and reproducible fixture |
| Debugging guidance for existing `SKILL.md` files | Tooling to generate and validate a packaging-complete skill skeleton |
| MCP design checklist | Commercial archive, fixture, and support boundary |

The paid pack is **not** an unattended GitHub-to-production compiler, and it does not claim universal agent runtime support. It runs locally against paths you provide. Learn more only if you need the full workflow: <https://whop.com/github-bad1/agentic-distiller/>.

## Scope and license

- Brand: George O'Nair.
- License for this free repository: [MIT](LICENSE).
- Do not use the preflight result as legal advice. `DISTILL` only describes a detected license signal; verify provenance, obligations, and authorization for your use case.

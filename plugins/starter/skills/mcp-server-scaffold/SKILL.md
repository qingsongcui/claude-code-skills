---
name: mcp-server-scaffold
description: >
  Scaffold a minimal MCP (Model Context Protocol) server in TypeScript or Python
  with one tool, local stdio transport, and a smoke test. Use when the user wants
  to create an MCP server, add a tool for Claude Code or Cursor, connect an agent
  to a local script or API, or mentions MCP SDK, mcp.json, or Model Context Protocol.
---

# MCP server scaffold

Build the smallest server that Claude Code / Cursor can attach: stdio transport, one tool, no framework soup.

Official protocol docs: https://modelcontextprotocol.io

## Decide language

- TypeScript if the user already has Node 18+ and will publish to npm later.
- Python if the user already has a Python agent stack.

Default to TypeScript unless the repo is clearly Python.

## TypeScript scaffold

```
mcp-hello/
  package.json
  tsconfig.json
  src/index.ts
```

`package.json` essentials:

- `"type": "module"`
- dependency `@modelcontextprotocol/sdk`
- bin pointing at the compiled or tsx entry
- start command that runs on stdio (no HTTP server)

`src/index.ts` shape:

1. Create an MCP server instance with a stable `name` and `version`.
2. Register one tool (`hello`) with a JSON schema (`name: string`).
3. Handler returns text, not a thrown stack trace.
4. Connect via stdio transport.

Do not add OAuth, SSE, or a marketplace listing until this tool answers once.

## Python scaffold

```
mcp-hello/
  pyproject.toml
  src/mcp_hello/server.py
```

Use the official Python MCP SDK. Same contract: one tool, stdio, explicit error string on bad input.

## Wire it into Claude Code

Project `.mcp.json` (paths adjusted):

```json
{
  "mcpServers": {
    "hello": {
      "command": "npx",
      "args": ["tsx", "src/index.ts"]
    }
  }
}
```

Restart the session. Confirm the tool appears before writing a second tool.

## Smoke test

1. Start the server the same way Claude will (`npx tsx src/index.ts` or `python -m ...`).
2. It must not print logs to stdout (stdout is the protocol). Logs go to stderr.
3. Call `hello` with `{"name":"world"}` and expect a single text result.
4. Call it with missing `name` and expect a structured error, not a crash.

## Failure modes

| Symptom | Likely cause |
|---|---|
| Server shows up, tools empty | Tool not registered before connect |
| Session hangs | Process waiting on stdin incorrectly, or extra stdout logs |
| "command not found" | `command` in `.mcp.json` is a shell alias, not an executable |
| Works in terminal, not in Claude | Different cwd or env than `.mcp.json` |

## What to write for the user

Create the files in their repo (or a new folder they named). Print:

- how to run locally
- the `.mcp.json` snippet
- the first tool call to try
- what was intentionally omitted (auth, hosting, multiple transports)

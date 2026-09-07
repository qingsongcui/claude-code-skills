---
name: mcp-server-scaffold
description: >
  Scaffold and smoke-test a minimal local stdio MCP server with one tool in
  TypeScript or Python. Use when the user asks to build an MCP server, expose a
  local tool to Claude Code or Cursor, configure mcp.json, add Model Context
  Protocol tooling, debug a stdio MCP server, or connect an agent to a local API.
license: MIT
compatibility: TypeScript requires a current Node toolchain and the official MCP SDK. Python requires Python 3.10+ and MCP SDK 2.0+.
---

# MCP server scaffold

Build the smallest server that a host can attach to: **one tool, stdio transport, one observed success, one observed failure**. Do not start with OAuth, HTTP/SSE, database state, or a marketplace listing.

Use the current official build guide for SDK setup and API signatures: <https://modelcontextprotocol.io/docs/develop/build-server>.

## Select the language from the existing project

| Existing project | Default | Do not assume |
|---|---|---|
| Node/TypeScript project | TypeScript | Node version or package manager — inspect its manifest |
| Python project | Python | SDK version — inspect `pyproject.toml`/requirements |
| Empty directory | Ask before generating | The user’s runtime, deployment, and packaging needs |

Do not mix both SDKs into a single “starter.” One language, one executable entry point, one tool.

## Server contract

1. Give the server a stable name and version.
2. Register one tool with a narrow input schema.
3. Return a structured, user-readable error for invalid input; do not expose a stack trace as tool output.
4. Connect over stdio.
5. Send all diagnostics to **stderr**. Stdout is the JSON-RPC transport and any log line corrupts it.

The stdout rule is from the official MCP build guide: <https://modelcontextprotocol.io/docs/develop/build-server>.

## Minimal project shape

TypeScript:

```text
mcp-hello/
├── package.json
├── tsconfig.json
└── src/index.ts
```

Python:

```text
mcp-hello/
├── pyproject.toml
└── src/mcp_hello/server.py
```

Keep transport configuration outside the server implementation. Do not make application code depend on a developer’s absolute local path.

## Host configuration

Create `.mcp.json` only after the server can start by itself. Use the exact executable and arguments you just smoke-tested:

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

This is an example, not a command to cargo-cult. A Python server needs a Python/uv executable and its own tested path. Restart or reload the host after changing configuration, then confirm that **one tool appears** before adding another.

## Smoke-test checklist

1. Start the server with the same command configured in `.mcp.json`.
2. Confirm stdout contains only protocol messages; diagnostics go to stderr.
3. Call the happy path, for example `hello({"name":"world"})`; expect one text response.
4. Call missing or malformed input; expect a readable structured error, not a crash/hang.
5. Attach it through the target host and invoke the tool once.

## Failure modes

| Symptom | Likely cause | Recovery |
|---|---|---|
| Host finds server but lists zero tools | Registration ran after transport connect, or schema registration failed | Register the tool before connecting; run the server with SDK diagnostics |
| Host session hangs | Server writes logs to stdout or waits on stdin outside the transport | Move logs to stderr; use the SDK stdio transport only |
| `command not found` | `.mcp.json` uses a shell alias or a different environment | Use an executable path/command that passed the direct smoke test |
| Works in terminal but not host | Different cwd, env, or runtime version | Reproduce the host command exactly and record cwd/env |
| Tool throws raw stack trace | Input validation or handler errors are uncaught | Return a controlled user-facing error and log details to stderr |

## Deliverable format

Report:

- language and exact runtime/SDK version detected;
- server entry path and `.mcp.json` snippet;
- happy-path and invalid-input smoke-test output;
- the one capability deliberately excluded until the first tool works.

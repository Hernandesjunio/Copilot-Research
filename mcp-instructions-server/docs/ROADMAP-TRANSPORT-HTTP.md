# Roadmap: HTTP transport (alignment with corporate MCP templates)

## Current state

`corporate-instructions-mcp` ships as a **stdio** [Model Context Protocol](https://modelcontextprotocol.io/) server using FastMCP. This matches common **IDE-hosted** MCP setups (for example Visual Studio) and keeps the attack surface small (no network listener by default).

## Why HTTP may be needed

Many organizations standardize on **HTTP-based MCP** behind a gateway, to apply:

- TLS termination and corporate CA trust
- Authentication and authorization (API keys, OAuth2, mTLS)
- Rate limiting, request size limits, and audit logging at the edge
- Health/readiness probes for orchestrators (Kubernetes, ECS)

## Direction (no breaking change to stdio)

1. **Extract a pure-Python service layer** — indexing, search, and serialization already live mainly in `corporate_instructions_mcp.indexing` and tool handlers in `server.py`. A future refactor should move orchestration into a small module callable from both transports without duplicating business rules.
2. **Keep stdio as the default first-party artifact** for desktop IDE workflows.
3. **Add an optional HTTP entrypoint** (separate module or script) that:
   - reuses the same index and tool semantics;
   - exposes MCP over Streamable HTTP or the stack your organization uses;
   - runs only when explicitly installed/configured (so local stdio users are unaffected).

## Security note

HTTP deployment must **not** expose the corpus to unauthenticated callers. Treat the HTTP listener like any internal API: network policies, authN/Z, and secrets management are mandatory.

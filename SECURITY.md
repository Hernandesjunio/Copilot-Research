# Security policy

## Reporting a vulnerability

Please report security issues **privately** through this repository’s **Security** tab (GitHub Security Advisories), if available, or by contacting the maintainers via GitHub. Do not open a public issue for undisclosed vulnerabilities.

Include: affected component (e.g. `mcp-instructions-server`), version, reproduction steps, and impact assessment if possible.

## Supported versions

Security fixes are applied to the **latest released** `corporate-instructions-mcp` version on the default branch. Older tags may not receive backports unless agreed with maintainers.

## Threat model (high level)

The **Corporate Instructions MCP** server is a **local, read-only** process (default transport: **stdio**). It reads Markdown files only under the directory given by **`INSTRUCTIONS_ROOT`**, with the **same privileges as the OS user** running the process.

| Trust boundary | Assumption |
|----------------|------------|
| Corpus (`INSTRUCTIONS_ROOT`) | Treated as **organization-controlled** content. Do not point `INSTRUCTIONS_ROOT` at untrusted writable trees. |
| Host | Harden the machine and restrict who can change MCP configuration and environment variables. |
| Client | The MCP host (IDE) invokes the server; compromise of the host implies access to the corpus anyway. |

Risks mitigated in code include **path confinement** under `INSTRUCTIONS_ROOT` (including symlink resolution), **size limits** on files and frontmatter to reduce abuse of CPU/memory, and **dependency scanning** in CI. Remaining risks (malicious corpus placed by an attacker with filesystem access) are **operational** and must be addressed with access control and corpus governance.

For transport strategy (stdio vs HTTP) see [mcp-instructions-server/docs/ROADMAP-TRANSPORT-HTTP.md](mcp-instructions-server/docs/ROADMAP-TRANSPORT-HTTP.md).

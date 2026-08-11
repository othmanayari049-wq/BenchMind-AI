# Security model

## Implemented in V1

- File-extension allowlist and upload-size limits.
- Filename sanitization and path traversal protection through basename-only storage.
- No arbitrary shell or user-code execution on the host.
- Secrets are environment variables and `.env` is ignored.
- CORS is explicit and configurable.
- Tool APIs exposed through MCP are deterministic calculations/parsers only.

## Not implemented yet

BenchMind V1 does **not** execute arbitrary uploaded code. A future compiler/runtime feature must run in an isolated container or equivalent sandbox with resource, network, path, and timeout restrictions. The presence of a `sandbox` roadmap item must not be interpreted as existing isolation.

## Safety boundary

BenchMind is not safety certified. Recommendations involving mains voltage, batteries, high current, motors, machinery, high voltage, or other hazardous systems require qualified human verification.

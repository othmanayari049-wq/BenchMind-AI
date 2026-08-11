# Security Policy

## Reporting a vulnerability

Please do not disclose exploitable vulnerabilities in a public issue. Use GitHub's private vulnerability reporting feature for this repository when available.

Include the affected component, reproduction steps, impact, and any suggested mitigation. Do not include real credentials or private user data.

## Current security boundary

BenchMind V1 does not execute arbitrary uploaded source code or shell commands. Uploads are size-limited, extension-validated, and stored under sanitized basenames. Secrets belong in environment variables and must never be committed.

See [`docs/security.md`](docs/security.md) for the threat model and planned sandbox boundary.

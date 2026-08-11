# Contributing to BenchMind AI

Thank you for helping build evidence-grounded engineering diagnostics.

## Development setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cd frontend && npm install && cd ..
```

## Before opening a pull request

Run:

```bash
ruff format backend tests
ruff check backend tests
mypy backend/benchmind
pytest
PYTHONPATH=backend python benchmarks/evaluate.py
cd frontend && npm run typecheck && npm run build
```

## Engineering rules

- Prefer deterministic parsers/calculators when they can solve the task reliably.
- Every agent finding should identify its claim type and supporting evidence.
- Do not convert model confidence into a statement of fact.
- Do not add arbitrary host code execution.
- Do not document a feature as implemented before its code and tests exist.
- Add a benchmark fixture when introducing a new diagnostic rule.
- Keep specialist routing narrow; a new agent should not run on every case by default.

## Commit style

Use focused conventional commits such as:

```text
feat(core): add engineering case models
feat(agents): route firmware evidence
feat(rag): preserve PDF page provenance
feat(mcp): add deterministic power tool
test(benchmarks): add I2C mismatch fixture
docs(readme): document model configuration
```

# Benchmark methodology

`benchmarks/cases/*/case.json` defines deterministic fixture cases with known faults, expected evidence, and expected test-plan content.

The current cases test pipeline correctness, not real-world diagnostic accuracy. Run:

```bash
PYTHONPATH=backend python benchmarks/evaluate.py
```

The evaluator emits root-cause, evidence, and test-plan pass counts. These fixture results must not be presented as population-level accuracy.

Future evaluation should add blinded real hardware cases and measure root-cause accuracy, Top-K accuracy, false-diagnosis rate, evidence grounding, citation correctness, verifier success, tool selection, latency, and API cost.

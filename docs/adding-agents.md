# Adding an agent

1. Implement `SpecialistAgent.run(case) -> list[AgentFinding]`.
2. Return structured claims with evidence references; avoid prose-only internal contracts.
3. Register the agent in `BenchMindOrchestrator.specialists`.
4. Add routing criteria to `SupervisorAgent` only when that specialist is actually relevant.
5. Add unit and end-to-end tests proving the new agent changes a case correctly.
6. Update architecture docs and capabilities only after the feature exists.

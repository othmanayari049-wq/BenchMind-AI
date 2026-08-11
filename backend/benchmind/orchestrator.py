from __future__ import annotations

import asyncio
from time import perf_counter

from .agents import (
    DatasheetAgent,
    DiagnosisAgent,
    EngineeringToolAgent,
    FirmwareAgent,
    HardwareVisionAgent,
    ReportAgent,
    SupervisorAgent,
    TelemetryAgent,
    VerifierAgent,
)
from .models import AgentFinding, AgentTrace, EngineeringCase, EngineeringReport
from .providers.base import ModelProvider


class BenchMindOrchestrator:
    def __init__(self, provider: ModelProvider, max_parallel_agents: int = 4) -> None:
        self.supervisor = SupervisorAgent()
        self.diagnosis = DiagnosisAgent()
        self.verifier = VerifierAgent()
        self.reporter = ReportAgent()
        self.max_parallel_agents = max_parallel_agents
        self.specialists = {
            "hardware_vision": HardwareVisionAgent(provider),
            "firmware": FirmwareAgent(),
            "datasheet": DatasheetAgent(),
            "telemetry": TelemetryAgent(),
            "engineering_tools": EngineeringToolAgent(),
        }

    async def analyze(self, case: EngineeringCase) -> EngineeringReport:
        trace: list[AgentTrace] = []
        started = perf_counter()
        plan = self.supervisor.route(case)
        trace.append(AgentTrace(
            agent="supervisor", status="completed", duration_ms=(perf_counter() - started) * 1000,
            note="; ".join(f"{agent}: {plan.reasons[agent]}" for agent in plan.agents),
        ))

        semaphore = asyncio.Semaphore(self.max_parallel_agents)

        async def run_agent(name: str) -> tuple[list[AgentFinding], AgentTrace]:
            agent = self.specialists[name]
            t0 = perf_counter()
            try:
                async with semaphore:
                    findings = await agent.run(case)
                return findings, AgentTrace(agent=name, status="completed", duration_ms=(perf_counter() - t0) * 1000, note=f"{len(findings)} finding(s)")
            except Exception as exc:
                return [], AgentTrace(agent=name, status="failed", duration_ms=(perf_counter() - t0) * 1000, note=str(exc))

        results = await asyncio.gather(*(run_agent(name) for name in plan.agents))
        findings: list[AgentFinding] = []
        for batch, item_trace in results:
            findings.extend(batch)
            trace.append(item_trace)

        t0 = perf_counter()
        diagnosis = self.diagnosis.synthesize(case, findings)
        trace.append(AgentTrace(agent="diagnosis", status="completed", duration_ms=(perf_counter() - t0) * 1000))

        t0 = perf_counter()
        verification = self.verifier.verify(diagnosis)
        trace.append(AgentTrace(agent="verifier", status="completed", duration_ms=(perf_counter() - t0) * 1000))

        t0 = perf_counter()
        report = self.reporter.build(case, findings, diagnosis, verification, trace)
        trace.append(AgentTrace(agent="reporter", status="completed", duration_ms=(perf_counter() - t0) * 1000))
        report.agent_trace = trace
        return report

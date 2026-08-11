from ..models import EngineeringCase, EvidenceKind, RoutePlan


class SupervisorAgent:
    name = "supervisor"

    def route(self, case: EngineeringCase) -> RoutePlan:
        kinds = {item.kind for item in case.evidence}
        agents: list[str] = []
        reasons: dict[str, str] = {}

        def add(agent: str, reason: str) -> None:
            if agent not in agents:
                agents.append(agent)
                reasons[agent] = reason

        if kinds & {EvidenceKind.IMAGE, EvidenceKind.SCHEMATIC}:
            add("hardware_vision", "Image or schematic evidence is present")
        if kinds & {EvidenceKind.CODE, EvidenceKind.CONFIG}:
            add("firmware", "Code or configuration evidence is present")
        if kinds & {EvidenceKind.PDF, EvidenceKind.TEXT}:
            add("datasheet", "Document evidence may contain specifications or wiring facts")
        if kinds & {EvidenceKind.LOG, EvidenceKind.TELEMETRY}:
            add("telemetry", "Logs or telemetry are present")
        add("engineering_tools", "Deterministic cross-evidence checks are always inexpensive")
        return RoutePlan(agents=agents, reasons=reasons)

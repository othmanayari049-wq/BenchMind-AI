from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedPin:
    signal: str
    pin: str
    source: str


def voltage_divider(vin: float, r_top: float, r_bottom: float) -> float:
    if r_top <= 0 or r_bottom <= 0:
        raise ValueError("Resistances must be positive")
    return vin * r_bottom / (r_top + r_bottom)


def ohms_law(*, voltage: float | None = None, current: float | None = None, resistance: float | None = None) -> float:
    supplied = sum(value is not None for value in (voltage, current, resistance))
    if supplied != 2:
        raise ValueError("Provide exactly two of voltage, current, resistance")
    if voltage is None:
        assert current is not None and resistance is not None
        return current * resistance
    if current is None:
        if resistance == 0:
            raise ValueError("Resistance cannot be zero")
        assert resistance is not None
        return voltage / resistance
    if current == 0:
        raise ValueError("Current cannot be zero")
    return voltage / current


def electrical_power(*, voltage: float | None = None, current: float | None = None, resistance: float | None = None) -> float:
    if voltage is not None and current is not None:
        return voltage * current
    if voltage is not None and resistance is not None:
        if resistance <= 0:
            raise ValueError("Resistance must be positive")
        return voltage * voltage / resistance
    if current is not None and resistance is not None:
        if resistance < 0:
            raise ValueError("Resistance cannot be negative")
        return current * current * resistance
    raise ValueError("Provide voltage+current, voltage+resistance, or current+resistance")


PIN_PATTERNS = [
    re.compile(r"#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:GPIO)?(\d+)", re.I),
    re.compile(r"(?:const\s+)?(?:int|uint8_t|byte)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:GPIO)?(\d+)\s*;", re.I),
]
WIRING_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9_ -]{0,30})\s*(?:->|=>|:)\s*GPIO\s*(\d+)\b", re.I)


def parse_code_pins(text: str, source: str) -> list[ParsedPin]:
    pins: list[ParsedPin] = []
    for pattern in PIN_PATTERNS:
        for signal, pin in pattern.findall(text):
            pins.append(ParsedPin(signal=normalize_signal(signal), pin=pin, source=source))
    return _dedupe_pins(pins)


def parse_wiring_pins(text: str, source: str) -> list[ParsedPin]:
    return _dedupe_pins(
        [ParsedPin(signal=normalize_signal(signal), pin=pin, source=source) for signal, pin in WIRING_PATTERN.findall(text)]
    )


def normalize_signal(signal: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", signal).upper()
    for suffix in ("PIN", "GPIO"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned


def _dedupe_pins(pins: list[ParsedPin]) -> list[ParsedPin]:
    seen: set[tuple[str, str, str]] = set()
    output: list[ParsedPin] = []
    for pin in pins:
        key = (pin.signal, pin.pin, pin.source)
        if key not in seen:
            seen.add(key)
            output.append(pin)
    return output


def parse_i2c_addresses(text: str) -> list[str]:
    return sorted(set(match.upper() for match in re.findall(r"0x[0-9a-fA-F]{2}", text)))


def parse_serial_baud(text: str) -> list[int]:
    values = [int(v) for v in re.findall(r"Serial\.begin\s*\(\s*(\d+)\s*\)", text)]
    values += [int(v) for v in re.findall(r"(?:monitor[_ -]?baud|baud(?:rate)?)\s*[:=]\s*(\d+)", text, re.I)]
    return sorted(set(values))


def likely_error_lines(text: str, limit: int = 8) -> list[str]:
    lines = []
    for line in text.splitlines():
        lower = line.lower()
        if "error:" in lower or "fatal error" in lower or "exception" in lower or "traceback" in lower:
            lines.append(line.strip())
        if len(lines) >= limit:
            break
    return lines

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server import MCPServer

from .tools.engineering import (
    electrical_power,
    ohms_law,
    parse_i2c_addresses,
    parse_serial_baud,
    voltage_divider,
)


def build_server() -> MCPServer:
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "Install BenchMind with the 'mcp' extra: pip install -e '.[mcp]'"
        ) from exc

    mcp = MCPServer("BenchMind Engineering Tools")

    @mcp.tool()
    def calculate_voltage_divider(vin: float, r_top: float, r_bottom: float) -> float:
        """Calculate unloaded divider output voltage."""
        return voltage_divider(vin, r_top, r_bottom)

    @mcp.tool()
    def calculate_ohms_law(
        voltage: float | None = None,
        current: float | None = None,
        resistance: float | None = None,
    ) -> float:
        """Solve Ohm's law from exactly two supplied quantities."""
        return ohms_law(voltage=voltage, current=current, resistance=resistance)

    @mcp.tool()
    def calculate_power(
        voltage: float | None = None,
        current: float | None = None,
        resistance: float | None = None,
    ) -> float:
        """Calculate electrical power from a supported pair of quantities."""
        return electrical_power(voltage=voltage, current=current, resistance=resistance)

    @mcp.tool()
    def analyze_i2c_scan(text: str) -> list[str]:
        """Extract hexadecimal I2C addresses from scanner output."""
        return parse_i2c_addresses(text)

    @mcp.tool()
    def parse_serial_configuration(text: str) -> list[int]:
        """Extract serial baud rates from firmware or monitor configuration text."""
        return parse_serial_baud(text)

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()

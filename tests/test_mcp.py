from benchmind.mcp_server import build_server


async def test_mcp_server_registers_engineering_tools() -> None:
    server = build_server()
    assert server.name == "BenchMind Engineering Tools"

    tools = await server.list_tools()
    assert {tool.name for tool in tools} == {
        "analyze_i2c_scan",
        "calculate_ohms_law",
        "calculate_power",
        "calculate_voltage_divider",
        "parse_serial_configuration",
    }

import pytest

from benchmind.tools.engineering import (
    ohms_law,
    parse_code_pins,
    parse_i2c_addresses,
    parse_serial_baud,
    parse_wiring_pins,
    voltage_divider,
)


def test_voltage_divider() -> None:
    assert voltage_divider(5.0, 1000.0, 1000.0) == pytest.approx(2.5)


def test_ohms_law() -> None:
    assert ohms_law(voltage=5.0, resistance=1000.0) == pytest.approx(0.005)


def test_parse_pin_sources() -> None:
    code = parse_code_pins("#define ECHO_PIN 18\nconst int TRIG_PIN = 17;", "firmware.ino")
    wiring = parse_wiring_pins("ECHO -> GPIO5\nTRIG -> GPIO17", "wiring.txt")
    assert {(p.signal, p.pin) for p in code} == {("ECHO", "18"), ("TRIG", "17")}
    assert {(p.signal, p.pin) for p in wiring} == {("ECHO", "5"), ("TRIG", "17")}


def test_parse_i2c_and_baud() -> None:
    assert parse_i2c_addresses("Found 0x76 and 0x3C") == ["0X3C", "0X76"]
    assert parse_serial_baud("Serial.begin(115200); monitor_baud=9600") == [9600, 115200]

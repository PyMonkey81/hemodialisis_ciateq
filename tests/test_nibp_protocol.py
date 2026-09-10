# tests/test_nibp_protocol.py

"""Tests unitarios del protocolo NIBP (sin hardware)."""

from connection.nibp_protocol import (
    build_command,
    checksum_hex,
    parse_frame,
)


def test_checksum_hex_example_01():
    # 0x30 + 0x31 + 0x3B + 0x3B = 0xD7
    payload = bytes([0x30, 0x31, 0x3B, 0x3B])
    assert checksum_hex(payload) == "D7"


def test_build_command_01_matches_manual_example():
    assert build_command("01") == bytes.fromhex("02 30 31 3B 3B 44 37 03")


def test_parse_cuff_frame():
    frame = b"\x02" + b"035C0S3" + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed == {
        "type": "cuff",
        "pressure_mmhg": 35,
        "caution": 0,
        "status": 3,
    }


def test_parse_end_of_measurement_frame():
    frame = b"\x02" + b"999" + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed == {"type": "end"}


def test_parse_status_frame_ok():
    # El "D2" del ejemplo del manual es solo ilustrativo: no corresponde a la
    # suma mod 256 de "S1;A0;C03;M00;P125080090;R075;T0005;;" (da 0x40, no 0xD2).
    # Se recalcula aquí con el mismo algoritmo documentado en nibp_protocol.py.
    body = b"S1;A0;C03;M00;P125080090;R075;T0005;;"
    content = body + checksum_hex(body).encode("ascii")
    frame = b"\x02" + content + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "status"
    assert parsed["status_digit"] == 1
    assert parsed["patient_mode"] == 0
    assert parsed["cycle_min"] == 3
    assert parsed["message_code"] == 0
    assert parsed["sys"] == 125
    assert parsed["dia"] == 80
    assert parsed["map"] == 90
    assert parsed["hr"] == 75
    assert parsed["next_measure_s"] == 5
    assert parsed["error_code"] is None
    assert parsed["error_text"] is None
    assert parsed["checksum_ok"] is True


def test_parse_status_frame_error_m07_with_missing_pressures():
    body = b"S1;A0;C00;M07;P---------;R075;T0010;;"
    content = body + checksum_hex(body).encode("ascii")
    frame = b"\x02" + content + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "status"
    assert parsed["message_code"] == 7
    assert parsed["error_code"] == "07"
    assert parsed["error_text"] == "fuga de manguito"
    assert parsed["sys"] == -1
    assert parsed["dia"] == -1
    assert parsed["map"] == -1
    assert parsed["checksum_ok"] is True


def test_parse_status_frame_official_error_example_with_spaces_in_t_field():
    # Ejemplo oficial de error: <STX>S2;A0;C05;M07;P---------;R---;T    ;;....<ETX><CR>
    body = b"S2;A0;C05;M07;P---------;R---;T    ;;"
    content = body + checksum_hex(body).encode("ascii")
    frame = b"\x02" + content + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "status"
    assert parsed["status_digit"] == 2
    assert parsed["cycle_min"] == 5
    assert parsed["message_code"] == 7
    assert parsed["error_code"] == "07"
    assert parsed["error_text"] == "fuga de manguito"
    assert parsed["sys"] == -1
    assert parsed["dia"] == -1
    assert parsed["map"] == -1
    assert parsed["hr"] == -1
    assert parsed["next_measure_s"] == -1
    assert parsed["checksum_ok"] is True


def test_parse_status_frame_all_dashes():
    body = b"S0;A0;C--;M--;P---------;R---;T----;;"
    content = body + checksum_hex(body).encode("ascii")
    frame = b"\x02" + content + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "status"
    assert parsed["cycle_min"] == -1
    assert parsed["message_code"] == -1
    assert parsed["sys"] == -1
    assert parsed["dia"] == -1
    assert parsed["map"] == -1
    assert parsed["hr"] == -1
    assert parsed["next_measure_s"] == -1
    assert parsed["error_code"] is None
    assert parsed["error_text"] is None


def test_parse_unknown_frame_does_not_raise():
    frame = b"\x02" + b"\xFD\x01garbage" + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "unknown"
    assert isinstance(parsed["raw"], bytes)


def test_parse_frame_without_stx_returns_none():
    assert parse_frame(b"no stx here") is None

# tests/test_nibp_protocol.py

"""Tests unitarios del protocolo NIBP (sin hardware)."""

from connection.nibp_protocol import (
    build_command,
    checksum_hex,
    parse_frame,
    parse_spo2_packet,
)


def test_checksum_hex_example_01():
    # 0x30 + 0x31 + 0x3B + 0x3B = 0xD7
    payload = bytes([0x30, 0x31, 0x3B, 0x3B])
    assert checksum_hex(payload) == "D7"


def test_build_command_01_matches_manual_example():
    assert build_command("01") == bytes.fromhex("FD 30 31 3B 3B 44 37 FE 0D")


def test_build_command_31_spo2_on():
    assert build_command("31") == bytes.fromhex("FD 33 31 3B 3B 44 41 FE 0D")


def test_build_command_30_spo2_off():
    assert build_command("30") == bytes.fromhex("FD 33 30 3B 3B 44 39 FE 0D")


def test_parse_spo2_packet_real_bench_capture_no_finger():
    # Captura real de banco (sin dedo): 55 AA 07 6C 02 7F FF 00 F3
    frame = bytes.fromhex("55 AA 07 6C 02 7F FF 00 F3".replace(" ", ""))
    parsed = parse_spo2_packet(frame)
    assert parsed["type"] == "spo2"
    assert parsed["index"] == 0x6C
    assert parsed["no_finger"] is True
    assert parsed["sensor_off"] is False
    assert parsed["no_pulse"] is False
    assert parsed["searching"] is False
    assert parsed["signal_weak"] is False
    assert parsed["spo2"] is None
    assert parsed["pr"] is None
    assert parsed["pi"] is None
    assert parsed["checksum_ok"] is True


def test_parse_spo2_packet_synthetic_valid_reading():
    # status=0 (sin flags), spo2=98, pr=60, pi=20; checksum recalculado.
    n_field = 7
    body = bytes([0x01, 0x00, 98, 60, 20])
    checksum = (n_field + sum(body)) % 256
    frame = bytes([0x55, 0xAA, n_field]) + body + bytes([checksum])
    parsed = parse_spo2_packet(frame)
    assert parsed == {
        "type": "spo2",
        "index": 1,
        "status": 0,
        "sensor_off": False,
        "no_finger": False,
        "no_pulse": False,
        "searching": False,
        "signal_weak": False,
        "spo2": 98,
        "pr": 60,
        "pi": 20,
        "checksum_ok": True,
    }


def test_parse_spo2_packet_incomplete_returns_none():
    assert parse_spo2_packet(bytes.fromhex("55AA07")) is None
    assert parse_spo2_packet(bytes.fromhex("55AA076C027FFF00")) is None


def test_parse_spo2_packet_wrong_header_returns_none():
    assert parse_spo2_packet(bytes.fromhex("AA5507")) is None
    assert parse_spo2_packet(b"") is None


def test_parse_spo2_packet_bad_checksum():
    frame = bytes.fromhex("55AA076C027FFF0000")
    parsed = parse_spo2_packet(frame)
    assert parsed["type"] == "spo2_bad_checksum"


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


def test_parse_status_frame_real_bench_capture_with_spo2_delimiters():
    # Captura real de banco (NIBPWin V3.1, COM8, SpO2 ON):
    # <STX=0xFD>S1;A0;C00;M00;P101065076;R060;T    ;;{ck}<ETX=0xFE><CR>
    body = b"S1;A0;C00;M00;P101065076;R060;T    ;;"
    content = body + checksum_hex(body).encode("ascii")
    frame = b"\xFD" + content + b"\xFE\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "status"
    assert parsed["sys"] == 101
    assert parsed["dia"] == 65
    assert parsed["map"] == 76
    assert parsed["hr"] == 60
    assert parsed["checksum_ok"] is True
    assert parsed["error_code"] is None


def test_parse_unknown_frame_does_not_raise():
    frame = b"\x02" + b"\xFD\x01garbage" + b"\x03\x0D"
    parsed = parse_frame(frame)
    assert parsed["type"] == "unknown"
    assert isinstance(parsed["raw"], bytes)


def test_parse_frame_without_stx_returns_none():
    assert parse_frame(b"no stx here") is None

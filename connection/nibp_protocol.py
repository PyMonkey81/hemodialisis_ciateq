# connection/nibp_protocol.py

"""
Funciones puras para construir comandos y parsear tramas del baumanómetro
PAR Medizintechnik NIBP2020 UP (Combi Board con SpO2).

Protocolo (parte de presión, NIBPWin V3.1 / Technical Description Rev. 2.14):

Host -> módulo, 8 bytes:
    <STX=0x02> c0 c1 ';' ';' x0 x1 <ETX=0x03>
El checksum es la suma (mod 256) de TODOS los bytes después de STX y antes
de x0/x1 (es decir c0, c1, ';', ';'), representada como 2 dígitos HEX ASCII
mayúsculas.

Ejemplo (comando 01, start medición):
    build_command("01") == bytes.fromhex("02 30 31 3B 3B 44 37 03")
    porque 0x30 + 0x31 + 0x3B + 0x3B = 0xD7 -> "D7" -> 0x44 0x37 ('D','7')

Módulo -> host: tramas ASCII que empiezan en 0x02 y terminan en 0x03 0x0D
(<ETX><CR>). Tres formatos reconocidos:
    1) Presión de manguito en vivo: <STX> ddd C c S a <ETX><CR>
       ejemplo: <STX>035C0S3<ETX><CR>  (NO trae checksum)
    2) Fin de medición: <STX>999<ETX><CR>
    3) Status (respuesta a cmd 18):
       <STX>S{a};A{b};C{cc};M{mm};P{sys3}{dia3}{map3};R{hr3};T{t4};;{ck}<ETX><CR>
       ejemplo: <STX>S1;A0;C03;M00;P125080090;R075;T0005;;D2<ETX><CR>
       Valores ausentes vienen como "---" (o "---------" para el campo P).

Cualquier otra trama (por ejemplo SpO2 en FD/FE, aún no implementado) se
reporta como tipo "unknown" sin lanzar excepciones.
"""

from __future__ import annotations

import re
from typing import Optional

STX = 0x02
ETX = 0x03
CR = 0x0D

# --- Códigos de comando NIBP -------------------------------------------
CMD_START_MEASUREMENT = "01"
CMD_MANUAL_MODE = "03"
CMD_SOFTWARE_RESET = "16"
CMD_REQUEST_DATA = "18"
CMD_ADULT_MODE = "24"
CMD_NEONATAL_MODE = "25"
CMD_METHOD1_DEFLATION = "55"
CMD_METHOD2_IMT = "56"
CMD_METHOD3_ADAPTIVE = "65"
CMD_VERSION_28 = "28"
CMD_VERSION_29 = "29"
CMD_SERIAL_NUMBER = "71"

# 04..13 -> ciclos de 1/2/3/4/5/10/15/30/60/90 minutos
CYCLE_MINUTES_TO_CMD = {
    1: "04",
    2: "05",
    3: "06",
    4: "07",
    5: "08",
    10: "09",
    15: "10",
    30: "11",
    60: "12",
    90: "13",
}

# Presiones de arranque adulto (mmHg -> código de comando)
ADULT_START_PRESSURE_TO_CMD = {
    80: "30",
    100: "31",
    120: "32",
    140: "21",
    160: "22",
    180: "23",
    200: "33",
    220: "34",
    240: "35",
    280: "38",
}

# Textos en español para el dígito S{a} de la trama de status.
STATUS_TEXTS_ES = {
    0: "autotest",
    1: "standby",
    2: "error",
    3: "midiendo",
    4: "manómetro",
    5: "inicialización",
    6: "ciclo",
    7: "prueba de fuga",
    8: "inflando",
    9: "manteniendo presión (holding)",
}

# Textos de error en español para el campo M{mm} de la trama de status.
# M00/M03 se consideran OK (sin error); no aparecen en este diccionario.
ERROR_TEXTS_ES = {
    "02": "comando inválido (el módulo hace reset)",
    "06": "manguito flojo o no conectado / tiempo de inflado excedido",
    "07": "fuga de manguito",
    "08": "falla neumática",
    "09": "tiempo de medición excedido / pocas oscilaciones",
    "10": "valores fuera de rango",
    "11": "artefactos de movimiento",
    "12": "presión máxima excedida",
    "13": "amplitudes saturadas",
    "14": "fuga en test de fuga",
    "15": "error de sistema",
}

_CUFF_RE = re.compile(rb"^(\d{3})C([0-5])S([34789])$")
# T{4} acepta 4 dígitos, 4 guiones o 4 espacios (ejemplo oficial de error con "T    ").
_STATUS_RE = re.compile(
    rb"^S(\d);A(\d);C(\d{2}|-{2});M(\d{2}|-{2});"
    rb"P([\d-]{9});R([\d-]{3});T(\d{4}|-{4}| {4});;([0-9A-Fa-f]{2})$"
)


def checksum_hex(payload: bytes) -> str:
    """Suma módulo 256 de payload, formateada como 2 dígitos HEX ASCII mayúsculas."""
    return format(sum(payload) % 256, "02X")


def build_command(code: str) -> bytes:
    """
    Construye una trama de comando de 8 bytes para el módulo NIBP.

    code: cadena de 2 caracteres, por ejemplo "01", "18", "56".

    Test mental:
        build_command("01") == bytes.fromhex("02 30 31 3B 3B 44 37 03")
    """
    if not isinstance(code, str) or len(code) != 2:
        raise ValueError(f"Código de comando NIBP inválido: {code!r}")

    code_bytes = code.encode("ascii")
    payload = code_bytes + b";;"
    checksum = checksum_hex(payload).encode("ascii")
    return bytes([STX]) + payload + checksum + bytes([ETX])


def _field_to_int(value: bytes) -> int:
    """Convierte un campo numérico ASCII a int; -1 si el campo es de guiones o espacios (valor ausente)."""
    text = value.decode("ascii")
    if "-" in text or " " in text:
        return -1
    return int(text)


def parse_frame(data: bytes) -> Optional[dict]:
    """
    Interpreta una trama completa (incluyendo STX/ETX/CR si están presentes).

    Devuelve un dict con clave "type" en {"cuff", "end", "status", "unknown"},
    o None si data no contiene una trama reconocible (sin STX/ETX).
    """
    if not data or data[0] != STX:
        return None

    etx_index = data.find(bytes([ETX]), 1)
    if etx_index == -1:
        return None

    content = data[1:etx_index]

    # Fin de medición
    if content == b"999":
        return {"type": "end"}

    # Presión de manguito en vivo (sin checksum)
    cuff_match = _CUFF_RE.match(content)
    if cuff_match:
        pressure_mmhg = int(cuff_match.group(1))
        caution = int(cuff_match.group(2))
        status = int(cuff_match.group(3))
        return {
            "type": "cuff",
            "pressure_mmhg": pressure_mmhg,
            "caution": caution,
            "status": status,
        }

    # Status (respuesta a comando 18)
    status_match = _STATUS_RE.match(content)
    if status_match:
        s_digit, a_digit, c_field, m_field, p_field, r_field, t_field, checksum_recv = (
            status_match.groups()
        )
        # Checksum = suma mod 256 de todo el content ANTES de los 2 chars de
        # checksum (sin STX ni ETX), es decir desde 'S...' hasta el ';;' inclusive.
        # Ejemplo "S1;A0;C03;M00;P125080090;R075;T0005;;D2" del manual: el "D2"
        # ahí es solo ilustrativo y NO corresponde a esta suma (da 0x40, no 0xD2);
        # los tests usan el checksum recalculado con este mismo algoritmo.
        checksum_calc = checksum_hex(content[: status_match.start(8)])
        m_code = m_field.decode("ascii")
        is_error_code = m_code in ERROR_TEXTS_ES
        error_text = ERROR_TEXTS_ES.get(m_code) if is_error_code else None

        return {
            "type": "status",
            "status_digit": int(s_digit),
            "patient_mode": int(a_digit),
            "cycle_min": _field_to_int(c_field),
            "message_code": _field_to_int(m_field),
            "sys": _field_to_int(p_field[0:3]),
            "dia": _field_to_int(p_field[3:6]),
            "map": _field_to_int(p_field[6:9]),
            "hr": _field_to_int(r_field),
            "next_measure_s": _field_to_int(t_field),
            "checksum_received": checksum_recv.decode("ascii").upper(),
            "checksum_ok": checksum_recv.decode("ascii").upper() == checksum_calc,
            "error_code": m_code if is_error_code else None,
            "error_text": error_text,
        }

    return {"type": "unknown", "raw": bytes(content)}

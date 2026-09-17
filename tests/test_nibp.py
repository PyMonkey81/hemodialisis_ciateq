"""Prueba manual NIBP2020 UP. Cerrar NIBPWin antes."""
import os
import sys
import time
import serial
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from connection.nibp_protocol import build_command, parse_frame, parse_spo2_packet

PORT = "COM8"

def fd(code):
    inner = build_command(code)[1:-1]
    return bytes([0xFD]) + inner + bytes([0xFE, 0x0D])

def dump_human(data: bytes):
    i = 0
    while i < len(data):
        if data[i] == 0x55 and i + 1 < len(data) and data[i + 1] == 0xAA:
            if i + 2 >= len(data):
                break
            n = data[i + 2]
            total = 2 + n
            pkt = data[i:i + total]
            if len(pkt) < total:
                break
            parsed = parse_spo2_packet(pkt)
            if parsed and parsed.get("type") == "spo2":
                st = "Sin dedo" if parsed.get("no_finger") else (
                    "Sensor off" if parsed.get("sensor_off") else (
                    "Sin pulso" if parsed.get("no_pulse") else (
                    "Buscando" if parsed.get("searching") else (
                    "Señal débil" if parsed.get("signal_weak") else "OK"))))
                spo2 = parsed.get("spo2")
                pr = parsed.get("pr")
                print(f"  SpO2={spo2 if spo2 is not None else '--'}%  "
                      f"PR={pr if pr is not None else '--'}  {st}")
            i += total
            continue
        if data[i] == 0xFD:
            end = data.find(b"\xFE", i)
            if end < 0:
                break
            extra = 2 if end + 1 < len(data) and data[end + 1] == 0x0D else 1
            frame = data[i:end + extra]
            p = parse_frame(frame)
            if p:
                t = p.get("type")
                if t == "cuff":
                    print(f"  Manguito {p.get('pressure_mmhg')} mmHg")
                elif t == "end":
                    print("  Fin de toma (999)")
                elif t == "status":
                    print(
                        f"  SYS={p.get('sys')} DIA={p.get('dia')} "
                        f"MAP={p.get('map')} FC={p.get('hr')} "
                        f"err={p.get('error_code')}"
                    )
            i = end + extra
            continue
        i += 1

def main():
    app = QApplication(sys.argv)
    ser = serial.Serial(PORT, 19200, timeout=0.2)
    print("open", ser.is_open)

    def tx(code):
        frame = fd(code)
        ser.write(frame)
        print("TX", code)

    def rx():
        time.sleep(0.3)
        chunks = []
        for _ in range(20):
            piece = ser.read(512)
            if not piece:
                break
            chunks.append(piece)
        data = b"".join(chunks)
        print(f"RX {len(data)} bytes")
        dump_human(data)

    def shutdown():
        ser.close()
        app.quit()

    QTimer.singleShot(500, lambda: tx("16"))
    QTimer.singleShot(2500, lambda: tx("24"))
    QTimer.singleShot(2800, lambda: tx("56"))
    QTimer.singleShot(3100, lambda: tx("22"))
    QTimer.singleShot(3400, lambda: tx("31"))  # SpO2 on
    QTimer.singleShot(4000, lambda: tx("01"))
    QTimer.singleShot(20000, rx)
    QTimer.singleShot(45000, lambda: tx("18"))
    QTimer.singleShot(47000, rx)
    QTimer.singleShot(60000, shutdown)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
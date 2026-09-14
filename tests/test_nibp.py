# # tests/tes_nibp.py
# """Prueba manual NIBP2020 UP con marco FD/FE. Cerrar NIBPWin antes."""

from multiprocessing.dummy import shutdown
import os
import sys
import time

import serial
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from connection.nibp_par_communication import NibpParCommunication
from connection.nibp_protocol import build_command




PORT = "COM8"

def fd(code):
    inner = build_command(code)[1:-1]
    return bytes([0xFD]) + inner + bytes([0xFE, 0x0D])

def main():
    app = QApplication(sys.argv)
    ser = serial.Serial(PORT, 19200, timeout=0.2)
    print("open", ser.is_open)

    def tx(code):
        frame = fd(code)
        ser.write(frame)
        print("TX", code, frame.hex())

    def rx():
        
        time.sleep(0.3)
        chunks = []
        for _ in range(20):
            piece = ser.read(512)
            if not piece:
                break
            chunks.append(piece)
        data = b"".join(chunks)
        print("RX", len(data), data.hex())

    def shutdown():
            ser.close()
            app.quit()

    QTimer.singleShot(500, lambda: tx("16"))
    QTimer.singleShot(2500, lambda: tx("24"))
    QTimer.singleShot(2800, lambda: tx("56"))
    QTimer.singleShot(3100, lambda: tx("22"))
    QTimer.singleShot(3400, lambda: tx("01"))
    QTimer.singleShot(45000, lambda: tx("18"))
    QTimer.singleShot(47000, rx)
    QTimer.singleShot(60000, shutdown)

    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
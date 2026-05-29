import sys
import serial
import threading
import struct
import crcmod
import time
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QLabel, QComboBox, QSpinBox, QPushButton)

# Función CRC igual a la de tu HMI
crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF, rev=True, xorOut=0x0000)

status_map = {
    1: "INICIO CEBADO", 2: "LLENADO DE TANQUE", 3: "LLENADO DE LINEA",
    4: "LLENADO CÁMARA", 5: "CALENTAMIENTO", 6: "INFUSIÓN",
    7: "COLOCACIÓN DE FILTRO", 8: "DIÁLISIS", 9: "BYPASS", 10: "CERRADO",
    12: "ULTRAFILTRACIÓN OFF", 13: "LISTO PARA INICIAR TRATAMIENTO",
    14: "TRATAMIENTO INICIADO", 15: "PAUSA", 16: "TRATAMIENTO DETENIDO"
}

class Simulator(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        self.current_status = 1  # Estado por defecto
        self.status_index = 0    # IMPORTANTE: Índice en el ANALOG_MAP
        
        self.setup_ui()
        self.start_serial("COM4")  # Cambia esto al puerto virtual correspondiente

    def setup_ui(self):
        self.setWindowTitle("Simulador de Hardware - Hemodiálisis")
        self.resize(400, 250)
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Conectando...")
        self.info_label.setStyleSheet("font-weight: bold; color: blue;")
        layout.addWidget(self.info_label)

        layout.addWidget(QLabel("Selecciona el estado a simular:"))
        self.combo = QComboBox()
        for key, value in status_map.items():
            self.combo.addItem(f"{key}: {value}", key)
        self.combo.currentIndexChanged.connect(self.update_status)
        layout.addWidget(self.combo)

        layout.addWidget(QLabel("Índice de 'primingProcessStatus' en ANALOG_MAP (0-70):"))
        self.spin_index = QSpinBox()
        self.spin_index.setRange(0, 70)
        self.spin_index.setValue(0) # PON AQUÍ EL ÍNDICE CORRECTO DE TU MAPA
        self.spin_index.valueChanged.connect(self.update_index)
        layout.addWidget(self.spin_index)

    def update_status(self):
        self.current_status = float(self.combo.currentData())
        
    def update_index(self):
        self.status_index = self.spin_index.value()

    def start_serial(self, port_name):
        try:
            self.serial_port = serial.Serial(port_name, 115200, timeout=0.1)
            self.info_label.setText(f"Simulador escuchando en {port_name}")
            self.running = True
            threading.Thread(target=self.serial_loop, daemon=True).start()
        except Exception as e:
            self.info_label.setText(f"Error abriendo puerto: {e}")
            self.info_label.setStyleSheet("color: red;")

    def serial_loop(self):
        while self.running and self.serial_port.is_open:
            try:
                # Leer bytes del puerto
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(6) # Lee el comando + CRC
                    
                    if len(data) < 6:
                        continue
                        
                    # 1. ¿Es petición Booleana? (11 11 00 3C + CRC)
                    if data[:4] == b'\x11\x11\x00\x3c':
                        header = b'\x11\x11\x00'
                        payload = bytes([0] * 60) # 60 variables booleanas en 0
                        
                        resp = header + payload
                        crc = crc16(resp)
                        resp += bytes([crc >> 8, crc & 0xFF])
                        self.serial_port.write(resp)

                    # 2. ¿Es petición Analógica? (12 AA 00 47 + CRC)
                    elif data[:4] == b'\x12\xaa\x00\x47':
                        header = b'\x12\xaa\x00'
                        
                        # Crear arreglo de 71 doubles en 0.0
                        analog_values = [0.0] * 71
                        # INYECTAR EL ESTADO en la posición seleccionada
                        analog_values[self.status_index] = self.current_status 
                        
                        payload = b''
                        for val in analog_values:
                            payload += struct.pack('<d', val)
                            
                        resp = header + payload
                        crc = crc16(resp)
                        resp += bytes([crc >> 8, crc & 0xFF])
                        self.serial_port.write(resp)
                        
            except Exception as e:
                print(f"Error en comunicación: {e}")
                time.sleep(1)

    def closeEvent(self, event):
        self.running = False
        if self.serial_port:
            self.serial_port.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Simulator()
    window.show()
    sys.exit(app.exec())

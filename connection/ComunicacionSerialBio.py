import serial
import serial.tools.list_ports
import threading
import time
from PySide6.QtCore import QObject, Signal
from typing import Optional

class ComunicacionSerialB(QObject):
    # Señal para enviar el texto recibido a la interfaz o lógica
    respuesta_recibida = Signal(str)
    
    def __init__(self, port_name: str, baudrate: int = 9600):
        super().__init__()
        self.port_name = port_name
        self.baudrate = baudrate
        self.puerto: Optional[serial.Serial] = None
        self.ejecutando = False
        self.hilo: Optional[threading.Thread] = None
        self.conectado = False

    def conectar(self) -> bool:
        """Conexión directa al puerto especificado."""
        try:
            self.puerto = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=1.0
            )
            self.conectado = True
            print(f"[NUEVO DISPOSITIVO] Conectado en {self.port_name}")
            return True
        except Exception as e:
            print(f"[ERROR NUEVO] No se pudo abrir {self.port_name}: {e}")
            self.conectado = False
            return False

    def iniciar(self):
        if self.ejecutando: return
        self.ejecutando = True
        self.hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
        self.hilo.start()

    def enviar_ascii(self, palabra: str):
        """Envía una cadena ASCII simple."""
        if self.conectado and self.puerto:
            try:
                # Enviamos la palabra + un terminador de línea si es necesario
                self.puerto.write(f"{palabra}\n".encode('ascii'))
            except Exception as e:
                print(f"[ERROR ENVIO] {e}")
                self.conectado = False

    def _bucle_lectura(self):
        """Bucle paralelo simplificado."""
        while self.ejecutando:
            if not self.conectado:
                self.conectar()
                time.sleep(2.0)
                continue

            try:
                if self.puerto.in_waiting > 0:
                    # Lee hasta el salto de línea y decodifica ASCII
                    linea = self.puerto.readline().decode('ascii').strip()
                    if linea:
                        self.respuesta_recibida.emit(linea)
                
                time.sleep(0.1) # Respiro para el CPU
            except Exception as e:
                print(f"[ERROR LECTURA] {e}")
                self.conectado = False
                if self.puerto: self.puerto.close()
                time.sleep(1.0)

    def detener(self):
        self.ejecutando = False
        if self.puerto: self.puerto.close()
        if self.hilo: self.hilo.join()
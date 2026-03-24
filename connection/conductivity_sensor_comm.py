#connection/conductivity_sensor_comm.py
"""
Módulo para la comunicación y lectura del sensor patrón de conductividad.

Este módulo implementa la clase `PatternConductivity`, diseñada para interactuar
con un sensor de conductividad patrón (específicamente los modelos HDM18/HDM19
o similares con protocolo de comunicación ASCII) a través de un puerto serial.
Su función principal es leer los valores de conductividad y temperatura del
sensor, parsearlos y emitirlos como señales de Qt para su uso en la interfaz
de usuario o en el sistema de control.

Características principales:
-----------------------------
- **Comunicación Serial Directa**: Intenta conectarse a un puerto serial fijo
  (ej. "COM7") con parámetros predefinidos (baudrate, bits de datos, etc.).
- **Modo de Operación Asíncrono**: Ejecuta su lógica de comunicación en un
  hilo separado (`reader_thread`) para garantizar lecturas continuas y no
  bloqueantes, esencial para aplicaciones de monitoreo en tiempo real.
- **Protocolo de Consulta Específico**: Envía un comando de lectura predefinido
  (ej. `b'VALAR\\r'`) al sensor para solicitar los datos.
- **Parseo de Respuesta ASCII**: Procesa la cadena de respuesta ASCII del sensor
  para extraer los valores numéricos de conductividad (raw y compensada) y
  temperatura.
- **Emisión de Datos (Qt Signals)**: Emite la señal `data_received(tag: str, value: float)`
  cada vez que se obtiene y parsea un nuevo valor del sensor, utilizando tags
  descriptivos (ej. "patternCondSensor", "patternTempSensor").
- **Manejo de Errores y Reconexión**: Incluye lógica para detectar fallos de
  comunicación, errores de parseo y para intentar reconectar al sensor
  automáticamente.
- **Optimización de Lectura**: Incorpora pausas estratégicas para asegurar que
  el sensor tenga tiempo de responder antes de intentar leer, y para evitar la
  sobrecarga de lecturas.

Clase principal:
----------------
- `PatternConductivity`: Gestiona la conexión, el envío de comandos, la lectura
  y el parseo de respuestas del sensor patrón de conductividad.

Dependencias:
-------------
- `serial`: Biblioteca PySerial para el control del puerto serial.
- `serial.tools.list_ports`: Posiblemente para listar puertos (aunque usa un puerto fijo).
- `threading`: Para ejecutar la lógica de comunicación en un hilo separado.
- `time`: Para gestionar pausas y timeouts.
- `struct`: Mantenido para referencia, aunque no se usa directamente para este protocolo ASCII.
- `queue`: Para la gestión de una cola de comandos (aunque principalmente se usa un comando de lectura cíclica).
- `PySide6.QtCore.QObject`, `PySide6.QtCore.Signal`: Para la integración con el sistema de señales/slots de Qt.
- `core.variables_map.VARIABLES`: Para referencia o mapeo de tags, aunque no se usa directamente para la lectura.

Uso:
----
1.  **Instanciación**: Crear una instancia de `PatternConductivity` en el
    componente principal de la aplicación (ej. `HemodialysisHMI`).
2.  **Inicio del Hilo**: Llamar a `start()` para iniciar el hilo de comunicación.
3.  **Conexión de Señales**: Conectar la señal `data_received` a un slot
    de la GUI o del sistema de control para procesar los valores recibidos.
4.  **Detención**: Al cerrar la aplicación, llamar a `stop()` para finalizar
    el hilo y liberar el puerto serial de forma segura.
"""

import serial
import serial.tools.list_ports
import threading
import time
import struct  

from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal


from core.variables_map import VARIABLES


READ_COMMAND = bytes.fromhex("5641 4C41 520D")  # b'VALAR\r'
EXPECTED_MINIMUM_SIZE = 30


class PatternConductivity(QObject):
    """
    Clase para manejar el sensor patrón de conductividad (HDM18/19).
    Emite señales con tag y valor para integración con VARIABLES y UI.
    """
    data_received = Signal(str, float) 

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.command_queue = Queue()
        self.read_command = READ_COMMAND
        self.isConnected = False
        self.last_successful_comm = time.time()
    
    def connect(self) -> bool:
        """Intenta conectar directamente al puerto COM7"""
        target_port = "COM7"  # Puerto fijo 
    
        try:
            # Intentar abrir el puerto directamente
            self.serial_port = serial.Serial(
                port=target_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=0.5
            )
        
            # Esperar un momento para que el sensor se estabilice
            time.sleep(1.5)
        
            print(f"[Connected Conductivity sensor] Port: {target_port}")
            self.isConnected = True
            self.last_successful_comm = time.time()
            return True  # Conexión exitosa
        except serial.SerialException as e:
            # Error específico de pySerial
            print(f"[ERROR] Failed to open {target_port}: {e}")
        except Exception as e:
            # Otro error inesperado
            print(f"[ERROR] An unexpected error occurred while connecting: {e}")
    
        self.isConnected = False  # Marca como no conectado
        return False  # Conexión fallida


    def start(self):
        """Inicia el hilo de comunicación si no está corriendo"""
        if self.running:
            return
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        

    def stop(self):
        """Detiene el hilo y cierra el puerto"""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.isConnected = False
        print("[PatternConductivity] Stopped and port closed")

    def _send_command(self, command: bytes) -> bool:
        """Envía comando y retorna True si se envió correctamente"""
        if not self.serial_port or not self.serial_port.is_open:
            return False
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.serial_port.write(command)
            return True
        except Exception as e:
            
            return False

    def _read_response(self) -> str:
        """Lee la respuesta completa con timeout"""
        if not self.serial_port or not self.serial_port.is_open:
            return ""
        try:
            response = self.serial_port.read(100).decode('ascii', errors='ignore').rstrip('\r\n \x00')
            if response:
                print(f"[VALAR raw] '{response}' (len={len(response)})")
            return response
        except Exception as e:
            print(f"[ERROR] Read failed: {e}")
            return ""

    
    def _parse_response(self, raw: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Parsea: cond_raw, cond_compensada, temp"""
        if not raw or len(raw) < 20:  
            return None, None, None

        parts = [p.strip() for p in raw.split('/')]
        if len(parts) < 3:
            
            return None, None, None

        try:
            cond_raw = float(parts[0])
            cond_comp = float(parts[1])
            temp = float(parts[2])
            return cond_raw, cond_comp, temp
        except ValueError as e:
            
            return None, None, None

    def _communication_loop(self):
        while self.running:
            if not self.isConnected or not self.serial_port or not self.serial_port.is_open:
                self.isConnected = False
                if self.connect():
                    pass  
                else:
                    time.sleep(3.0)
                continue

            try:
                
                try:
                    command = self.command_queue.get_nowait()
                    is_read = False
                except Empty:
                    command = self.read_command
                    is_read = True

                if not self._send_command(command):
                    raise serial.SerialException("Failed to send")

                time.sleep(0.1)  # respiro corto para respuesta
                raw_response = self._read_response()

                if raw_response:
                    self.last_successful_comm = time.time()

                    if is_read:
                        cond_raw, cond_comp, temp = self._parse_response(raw_response)
                        if cond_comp is not None:
                            conductivity_comp = cond_comp 
                            self.data_received.emit("patternCondSensor", conductivity_comp)
                            print(f"[Emit] patternCondSensor → {cond_comp:.4f} mS/cm")

                        if cond_raw is not None:
                            conductivity_raw = cond_raw * 1000  # conversion a milisiemens 
                            self.data_received.emit("patternCondRaw", conductivity_raw)
                            print(f"[Emit] patternCondRaw → {cond_raw:.8f} mS/cm")  # más decimales para raw

                        if temp is not None:
                            self.data_received.emit("patternTempSensor", temp)
                            print(f"[Emit] patternTempSensor → {temp:.3f} °C")

                # Chequeo de comunicación saludable (opcional: si >10s sin respuesta, reconectar)
                if time.time() - self.last_successful_comm > 10:
                    self.isConnected = False
                    continue

                time.sleep(0.4)  # ~2-3 lecturas por segundo, ajusta 

            except serial.SerialException as e:
                print(f"[Serial error] {e} → Reintentando conexión")
                self.isConnected = False
                time.sleep(1.0)
            except Exception as e:                
                time.sleep(1.0)

        print("[PatternConductivity] Communication loop ended")
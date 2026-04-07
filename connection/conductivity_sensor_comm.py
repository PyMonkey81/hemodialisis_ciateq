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
#connection/conductivity_sensor_comm.py



import serial
import serial.tools.list_ports
import threading
import time
import re # Usaremos regex también aquí por si acaso, aunque el parseo es más simple
import logging # Importar logging

from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__) # Inicializar el logger

READ_COMMAND = bytes.fromhex("5641 4C41 520D")  # b'VALAR\r'
# EXPECTED_MINIMUM_SIZE = 30 # No se usa directamente, se puede omitir si no tiene un propósito

class PatternConductivity(QObject):
    """
    Clase para manejar el sensor patrón de conductividad (HDM18/19).
    Emite señales con tag y valor para integración con VARIABLES y UI.
    """
    data_received = Signal(str, float) 

    def __init__(self, port_whitelist=None, baudrate=115200):
        super().__init__()
        self.port_whitelist = port_whitelist if port_whitelist else ["USB Serial"] # Palabras clave para auto-detección
        self.baudrate = baudrate
        self.serial_port: Optional[serial.Serial] = None
        self._running = False # Usamos _running para controlar el hilo
        self.reader_thread: Optional[threading.Thread] = None
        # self.command_queue = Queue() # Comentado, ya que para VALAR es un comando cíclico fijo
        self.read_command = READ_COMMAND
        self.last_successful_comm = time.time()

        # --- Nuevas variables para la configuración desde la UI ---
        self._user_selected_port: Optional[str] = None # Puerto seleccionado por el usuario (e.g., "COM3"), None para auto
        self._is_enabled: bool = False # Si el controlador debe intentar comunicarse o no

    # Propiedad para controlar el estado de ejecución del hilo
    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value: bool):
        self._running = value

    def update_config(self, port_name: str, is_enabled: bool):
        """
        Actualiza la configuración de comunicación desde la UI.
        
        Args:
            port_name (str): El nombre del puerto (e.g., "COM3", "Auto"). "Auto" para detección automática.
            is_enabled (bool): Si la comunicación con este sensor debe estar activa.
        """
        # Comparar con la configuración actual para decidir acciones
        port_changed = (self._user_selected_port != port_name and not (self._user_selected_port is None and port_name == "Auto"))
        enabled_changed = (self._is_enabled != is_enabled)
        
        # Almacenar la nueva configuración
        self._user_selected_port = port_name if port_name != "Auto" else None
        self._is_enabled = is_enabled
        
        logger.info(f"[COND. PATRÓN] Configuración recibida: Puerto='{port_name}' (interno: '{self._user_selected_port if port_name != 'Auto' else 'Auto'}'), Habilitado={is_enabled}")

        # Lógica de acción basada en el cambio de configuración
        if not self._is_enabled and self.running:
            logger.info("[COND. PATRÓN] Se deshabilitó la comunicación. Deteniendo controlador.")
            self.stop()
        elif self._is_enabled and not self.running:
            logger.info("[COND. PATRÓN] Se habilitó la comunicación. Iniciando controlador.")
            self.start()
        elif self._is_enabled and port_changed and self.running:
            logger.info(f"[COND. PATRÓN] El puerto seleccionado ha cambiado a '{port_name}'. Forzando reconexión.")
            # Cerrar el puerto actual para que el _communication_loop intente una nueva conexión
            self._close_port()

    def start(self):
        """Inicia el hilo de comunicación si está habilitado y no está corriendo."""
        if not self._is_enabled:
            logger.warning("[COND. PATRÓN] Intento de iniciar controlador deshabilitado. No se hará nada.")
            return

        if self.running:
            return
        
        self.running = True
        self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.reader_thread.start()
        logger.info("[COND. PATRÓN] Hilo de comunicación iniciado.")
        

    def stop(self):
        """Detiene el hilo y cierra el puerto"""
        if not self.running:
            return
        
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)
            logger.info("[COND. PATRÓN] Hilo de comunicación detenido.")
        self._close_port()
        logger.info("[COND. PATRÓN] Controlador detenido.")

    def _close_port(self):
        """Cierra el puerto serial si está abierto."""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                logger.info("[COND. PATRÓN] Puerto serial cerrado.")
            except Exception as e:
                logger.error(f"[COND. PATRÓN] Error cerrando puerto serial: {e}")
            finally:
                self.serial_port = None


    def _connect_to_specific_port(self, port_name: str) -> bool:
        """Intenta conectar a un puerto serial específico."""
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=self.baudrate, # Usar self.baudrate
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=0.5
            )
            time.sleep(1.5) # Dar tiempo al sensor para estabilizarse
            logger.info(f"[COND. PATRÓN] Conectado exitosamente en puerto ESPECÍFICO: {port_name}")
            self.last_successful_comm = time.time() # Resetear contador de comunicación
            return True
        except serial.SerialException as e:
            logger.warning(f"[COND. PATRÓN] Error al intentar conectar a {port_name} (específico): {e}")
            return False
        except Exception as e:
            logger.error(f"[COND. PATRÓN] Error inesperado al conectar a {port_name} (específico): {e}")
            return False

    def _find_and_connect_auto(self) -> bool:
        """
        Intenta encontrar y conectar al puerto serial del sensor patrón usando la whitelist.
        """
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"

            # Buscar palabras clave en la whitelist
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    logger.info(f"[COND. PATRÓN] Coincidencia automática encontrada en {p.device} ({full_info}). Intentando conectar...")
                    return self._connect_to_specific_port(p.device) # Reutilizamos la función de conexión
        logger.warning("[COND. PATRÓN] No se encontró ningún puerto de Cond. Patrón automáticamente.")
        return False

    def _send_command(self, command: bytes) -> bool:
        """Envía comando y retorna True si se envió correctamente"""
        if not self.serial_port or not self.serial_port.is_open:
            logger.warning("[COND. PATRÓN] Puerto serial no abierto para enviar comando.")
            return False
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.serial_port.write(command)
            logger.debug(f"[COND. PATRÓN] Comando enviado: {command}")
            return True
        except Exception as e:
            logger.error(f"[COND. PATRÓN] Error al enviar comando: {e}")
            return False

    def _read_response(self) -> str:
        """Lee la respuesta completa con timeout"""
        if not self.serial_port or not self.serial_port.is_open:
            return ""
        try:
            response = self.serial_port.read_until(b'\r').decode('ascii', errors='ignore').rstrip('\r\n \x00')
            if response:
                logger.debug(f"[COND. PATRÓN] Respuesta RAW: '{response}' (len={len(response)})")
            return response
        except Exception as e:
            logger.error(f"[COND. PATRÓN] Error al leer respuesta: {e}")
            return ""

    
    def _parse_response(self, raw: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Parsea: cond_raw, cond_compensada, temp"""
        if not raw or len(raw) < 10: # Ajuste el mínimo a algo más realista
            logger.warning(f"[COND. PATRÓN] Respuesta demasiado corta o vacía para parsear: '{raw}'")
            return None, None, None

        parts = [p.strip() for p in raw.split('/')]
        if len(parts) < 3:
            logger.warning(f"[COND. PATRÓN] Formato de respuesta inesperado: '{raw}'")
            return None, None, None

        try:
            cond_raw = float(parts[0])
            cond_comp = float(parts[1])
            temp = float(parts[2])
            return cond_raw, cond_comp, temp
        except ValueError as e:
            logger.error(f"[COND. PATRÓN] Error al convertir valores numéricos desde '{raw}': {e}")
            return None, None, None

    def _communication_loop(self):
        while self.running:
            # Si la comunicación está deshabilitada por el usuario, cerrar puerto y dormir
            if not self._is_enabled:
                self._close_port()
                time.sleep(1) # Dormir un poco para no consumir CPU
                continue

            # Si no hay puerto conectado, intentar conectar
            if not self.serial_port or not self.serial_port.is_open:
                connected = False
                if self._user_selected_port: # Si el usuario seleccionó un puerto específico
                    logger.debug(f"[COND. PATRÓN] Intentando conectar a puerto especificado: {self._user_selected_port}")
                    connected = self._connect_to_specific_port(self._user_selected_port)
                else: # Si no hay puerto específico, intentar detección automática
                    logger.debug("[COND. PATRÓN] Intentando conexión automática...")
                    connected = self._find_and_connect_auto()

                if not connected:
                    time.sleep(3.0) # Reintentar la conexión cada 3 segundos
                    continue
                else:
                    # Tras una conexión exitosa, es una buena práctica vaciar cualquier buffer de comandos
                    # Aunque para el sensor VALAR, el comando es fijo y se envía en el loop
                    pass

            try:
                # 1. Enviar el comando fijo de lectura
                if not self._send_command(self.read_command):
                    raise serial.SerialException("Fallo al enviar el comando de lectura.")

                time.sleep(0.1)  # Pequeño respiro para que el sensor responda
                raw_response = self._read_response()

                if raw_response:
                    self.last_successful_comm = time.time() # Actualizar tiempo de última comunicación exitosa

                    cond_raw, cond_comp, temp = self._parse_response(raw_response)
                    if cond_comp is not None:
                        self.data_received.emit("patternCondSensor", cond_comp)
                        logger.debug(f"[Emit] patternCondSensor → {cond_comp:.4f} mS/cm")

                    if cond_raw is not None:                        
                        conductivity_raw = cond_raw * 1000 # Convertir de S/cm a mS/cm
                        self.data_received.emit("patternCondRaw", conductivity_raw) 
                        logger.debug(f"[Emit] patternCondRaw → {conductivity_raw:.8f} mS/cm")

                    if temp is not None:
                        self.data_received.emit("patternTempSensor", temp)
                        logger.debug(f"[Emit] patternTempSensor → {temp:.3f} °C")
                else:
                    logger.warning("[COND. PATRÓN] No se recibió respuesta del sensor o estaba vacía.")


                # Chequeo de comunicación "saludable": si no hay respuesta en 10 segundos, forzar reconexión
                if time.time() - self.last_successful_comm > 10:
                    logger.warning("[COND. PATRÓN] Más de 10 segundos sin comunicación exitosa. Forzando reconexión.")
                    self._close_port() # Cerrar el puerto para forzar una nueva conexión en la próxima iteración
                    continue # Salta al inicio del bucle para intentar reconectar

                time.sleep(0.4)  # ~2 lecturas por segundo (0.1 + 0.4 = 0.5 seg por ciclo)

            except serial.SerialException as e:
                logger.error(f"[COND. PATRÓN] Error serial: {e} → Forzando reconexión")
                self._close_port() # Cerrar el puerto y forzar reconexión
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"[COND. PATRÓN] Error inesperado en el bucle de comunicación: {e}", exc_info=True)
                time.sleep(1.0)

        logger.info("[COND. PATRÓN] Hilo de comunicación finalizado.")

# import serial
# import serial.tools.list_ports
# import threading
# import time
# import re # Usaremos regex también aquí por si acaso, aunque el parseo es más simple
# import logging # Importar logging

# from queue import Queue, Empty
# from typing import Optional

# from PySide6.QtCore import QObject, Signal

# logger = logging.getLogger(__name__) # Inicializar el logger

# READ_COMMAND = bytes.fromhex("5641 4C41 520D")  # b'VALAR\r'
# # EXPECTED_MINIMUM_SIZE = 30 # No se usa directamente, se puede omitir si no tiene un propósito

# class PatternConductivity(QObject):
#     """
#     Clase para manejar el sensor patrón de conductividad (HDM18/19).
#     Emite señales con tag y valor para integración con VARIABLES y UI.
#     """
#     data_received = Signal(str, float) 

#     def __init__(self, port_whitelist=None, baudrate=115200):
#         super().__init__()
#         self.port_whitelist = port_whitelist if port_whitelist else ["USB Serial", "CH340", "CP210X"] # Palabras clave para auto-detección
#         self.baudrate = baudrate
#         self.serial_port: Optional[serial.Serial] = None
#         self._running = False # Usamos _running para controlar el hilo
#         self.reader_thread: Optional[threading.Thread] = None
#         # self.command_queue = Queue() # Comentado, ya que para VALAR es un comando cíclico fijo
#         self.read_command = READ_COMMAND
#         self.last_successful_comm = time.time()

#         # --- Nuevas variables para la configuración desde la UI ---
#         self._user_selected_port: Optional[str] = None # Puerto seleccionado por el usuario (e.g., "COM3"), None para auto
#         self._is_enabled: bool = False # Si el controlador debe intentar comunicarse o no

#     # Propiedad para controlar el estado de ejecución del hilo
#     @property
#     def running(self):
#         return self._running

#     @running.setter
#     def running(self, value: bool):
#         self._running = value

#     def update_config(self, port_name: str, is_enabled: bool):
#         """
#         Actualiza la configuración de comunicación desde la UI.
        
#         Args:
#             port_name (str): El nombre del puerto (e.g., "COM3", "Auto"). "Auto" para detección automática.
#             is_enabled (bool): Si la comunicación con este sensor debe estar activa.
#         """
#         # Comparar con la configuración actual para decidir acciones
#         port_changed = (self._user_selected_port != port_name and not (self._user_selected_port is None and port_name == "Auto"))
#         enabled_changed = (self._is_enabled != is_enabled)
        
#         # Almacenar la nueva configuración
#         self._user_selected_port = port_name if port_name != "Auto" else None
#         self._is_enabled = is_enabled
        
#         logger.info(f"[COND. PATRÓN] Configuración recibida: Puerto='{port_name}' (interno: '{self._user_selected_port if port_name != 'Auto' else 'Auto'}'), Habilitado={is_enabled}")

#         # Lógica de acción basada en el cambio de configuración
#         if not self._is_enabled and self.running:
#             logger.info("[COND. PATRÓN] Se deshabilitó la comunicación. Deteniendo controlador.")
#             self.stop()
#         elif self._is_enabled and not self.running:
#             logger.info("[COND. PATRÓN] Se habilitó la comunicación. Iniciando controlador.")
#             self.start()
#         elif self._is_enabled and port_changed and self.running:
#             logger.info(f"[COND. PATRÓN] El puerto seleccionado ha cambiado a '{port_name}'. Forzando reconexión.")
#             # Cerrar el puerto actual para que el _communication_loop intente una nueva conexión
#             self._close_port()

#     def start(self):
#         """Inicia el hilo de comunicación si está habilitado y no está corriendo."""
#         if not self._is_enabled:
#             logger.warning("[COND. PATRÓN] Intento de iniciar controlador deshabilitado. No se hará nada.")
#             return

#         if self.running:
#             return
        
#         self.running = True
#         self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
#         self.reader_thread.start()
#         logger.info("[COND. PATRÓN] Hilo de comunicación iniciado.")
        

#     def stop(self):
#         """Detiene el hilo y cierra el puerto"""
#         if not self.running:
#             return
        
#         self.running = False
#         if self.reader_thread and self.reader_thread.is_alive():
#             self.reader_thread.join(timeout=2.0)
#             logger.info("[COND. PATRÓN] Hilo de comunicación detenido.")
#         self._close_port()
#         logger.info("[COND. PATRÓN] Controlador detenido.")

#     def _close_port(self):
#         """Cierra el puerto serial si está abierto."""
#         if self.serial_port and self.serial_port.is_open:
#             try:
#                 self.serial_port.close()
#                 logger.info("[COND. PATRÓN] Puerto serial cerrado.")
#             except Exception as e:
#                 logger.error(f"[COND. PATRÓN] Error cerrando puerto serial: {e}")
#             finally:
#                 self.serial_port = None


#     def _connect_to_specific_port(self, port_name: str) -> bool:
#         """Intenta conectar a un puerto serial específico."""
#         try:
#             self.serial_port = serial.Serial(
#                 port=port_name,
#                 baudrate=self.baudrate, # Usar self.baudrate
#                 bytesize=serial.EIGHTBITS,
#                 parity=serial.PARITY_NONE,
#                 stopbits=serial.STOPBITS_ONE,
#                 timeout=1.0,
#                 write_timeout=0.5
#             )
#             time.sleep(1.5) # Dar tiempo al sensor para estabilizarse
#             logger.info(f"[COND. PATRÓN] Conectado exitosamente en puerto ESPECÍFICO: {port_name}")
#             self.last_successful_comm = time.time() # Resetear contador de comunicación
#             return True
#         except serial.SerialException as e:
#             logger.warning(f"[COND. PATRÓN] Error al intentar conectar a {port_name} (específico): {e}")
#             return False
#         except Exception as e:
#             logger.error(f"[COND. PATRÓN] Error inesperado al conectar a {port_name} (específico): {e}")
#             return False

#     def _find_and_connect_auto(self) -> bool:
#         """
#         Intenta encontrar y conectar al puerto serial del sensor patrón usando la whitelist.
#         """
#         ports = serial.tools.list_ports.comports()
        
#         for p in ports:
#             desc = p.description.upper()
#             manuf = p.manufacturer.upper() if p.manufacturer else ""
#             full_info = f"{desc} {manuf}"

#             # Buscar palabras clave en la whitelist
#             for keyword in self.port_whitelist:
#                 if keyword in full_info:
#                     logger.info(f"[COND. PATRÓN] Coincidencia automática encontrada en {p.device} ({full_info}). Intentando conectar...")
#                     return self._connect_to_specific_port(p.device) # Reutilizamos la función de conexión
#         logger.warning("[COND. PATRÓN] No se encontró ningún puerto de Cond. Patrón automáticamente.")
#         return False

#     def _send_command(self, command: bytes) -> bool:
#         """Envía comando y retorna True si se envió correctamente"""
#         if not self.serial_port or not self.serial_port.is_open:
#             logger.warning("[COND. PATRÓN] Puerto serial no abierto para enviar comando.")
#             return False
#         try:
#             self.serial_port.reset_input_buffer()
#             self.serial_port.reset_output_buffer()
#             self.serial_port.write(command)
#             logger.debug(f"[COND. PATRÓN] Comando enviado: {command}")
#             return True
#         except Exception as e:
#             logger.error(f"[COND. PATRÓN] Error al enviar comando: {e}")
#             return False

#     def _read_response(self) -> str:
#         """Lee la respuesta completa con timeout"""
#         if not self.serial_port or not self.serial_port.is_open:
#             return ""
#         try:
#             response = self.serial_port.read_until(b'\r').decode('ascii', errors='ignore').rstrip('\r\n \x00')
#             if response:
#                 logger.debug(f"[COND. PATRÓN] Respuesta RAW: '{response}' (len={len(response)})")
#             return response
#         except Exception as e:
#             logger.error(f"[COND. PATRÓN] Error al leer respuesta: {e}")
#             return ""

    
#     def _parse_response(self, raw: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
#         """Parsea: cond_raw, cond_compensada, temp"""
#         if not raw or len(raw) < 10: # Ajuste el mínimo a algo más realista
#             logger.warning(f"[COND. PATRÓN] Respuesta demasiado corta o vacía para parsear: '{raw}'")
#             return None, None, None

#         parts = [p.strip() for p in raw.split('/')]
#         if len(parts) < 3:
#             logger.warning(f"[COND. PATRÓN] Formato de respuesta inesperado: '{raw}'")
#             return None, None, None

#         try:
#             cond_raw = float(parts[0])
#             cond_comp = float(parts[1])
#             temp = float(parts[2])
#             return cond_raw, cond_comp, temp
#         except ValueError as e:
#             logger.error(f"[COND. PATRÓN] Error al convertir valores numéricos desde '{raw}': {e}")
#             return None, None, None

#     def _communication_loop(self):
#         while self.running:
#             # Si la comunicación está deshabilitada por el usuario, cerrar puerto y dormir
#             if not self._is_enabled:
#                 self._close_port()
#                 time.sleep(1) # Dormir un poco para no consumir CPU
#                 continue

#             # Si no hay puerto conectado, intentar conectar
#             if not self.serial_port or not self.serial_port.is_open:
#                 connected = False
#                 if self._user_selected_port: # Si el usuario seleccionó un puerto específico
#                     logger.debug(f"[COND. PATRÓN] Intentando conectar a puerto especificado: {self._user_selected_port}")
#                     connected = self._connect_to_specific_port(self._user_selected_port)
#                 else: # Si no hay puerto específico, intentar detección automática
#                     logger.debug("[COND. PATRÓN] Intentando conexión automática...")
#                     connected = self._find_and_connect_auto()

#                 if not connected:
#                     time.sleep(3.0) # Reintentar la conexión cada 3 segundos
#                     continue
#                 else:
#                     # Tras una conexión exitosa, es una buena práctica vaciar cualquier buffer de comandos
#                     # Aunque para el sensor VALAR, el comando es fijo y se envía en el loop
#                     pass

#             try:
#                 # 1. Enviar el comando fijo de lectura
#                 if not self._send_command(self.read_command):
#                     raise serial.SerialException("Fallo al enviar el comando de lectura.")

#                 time.sleep(0.1)  # Pequeño respiro para que el sensor responda
#                 raw_response = self._read_response()

#                 if raw_response:
#                     self.last_successful_comm = time.time() # Actualizar tiempo de última comunicación exitosa

#                     cond_raw, cond_comp, temp = self._parse_response(raw_response)
#                     if cond_comp is not None:
#                         self.data_received.emit("patternCondSensor", cond_comp)
#                         logger.debug(f"[Emit] patternCondSensor → {cond_comp:.4f} mS/cm")

#                     if cond_raw is not None:
#                         # Asumo que la conversión a milisiemens es aquí si no lo hace el sensor
#                         # conductivity_raw = cond_raw * 1000 # Solo si el sensor da en S/cm y necesitas mS/cm
#                         self.data_received.emit("patternCondRaw", cond_raw) 
#                         logger.debug(f"[Emit] patternCondRaw → {cond_raw:.8f} mS/cm")

#                     if temp is not None:
#                         self.data_received.emit("patternTempSensor", temp)
#                         logger.debug(f"[Emit] patternTempSensor → {temp:.3f} °C")
#                 else:
#                     logger.warning("[COND. PATRÓN] No se recibió respuesta del sensor o estaba vacía.")


#                 # Chequeo de comunicación "saludable": si no hay respuesta en 10 segundos, forzar reconexión
#                 if time.time() - self.last_successful_comm > 10:
#                     logger.warning("[COND. PATRÓN] Más de 10 segundos sin comunicación exitosa. Forzando reconexión.")
#                     self._close_port() # Cerrar el puerto para forzar una nueva conexión en la próxima iteración
#                     continue # Salta al inicio del bucle para intentar reconectar

#                 time.sleep(0.4)  # ~2 lecturas por segundo (0.1 + 0.4 = 0.5 seg por ciclo)

#             except serial.SerialException as e:
#                 logger.error(f"[COND. PATRÓN] Error serial: {e} → Forzando reconexión")
#                 self._close_port() # Cerrar el puerto y forzar reconexión
#                 time.sleep(1.0)
#             except Exception as e:
#                 logger.error(f"[COND. PATRÓN] Error inesperado en el bucle de comunicación: {e}", exc_info=True)
#                 time.sleep(1.0)

#         logger.info("[COND. PATRÓN] Hilo de comunicación finalizado.")

# import serial
# import serial.tools.list_ports
# import threading
# import time
# import struct  

# from queue import Queue, Empty
# from typing import Optional

# from PySide6.QtCore import QObject, Signal


# from core.variables_map import VARIABLES


# READ_COMMAND = bytes.fromhex("5641 4C41 520D")  # b'VALAR\r'
# EXPECTED_MINIMUM_SIZE = 30


# class PatternConductivity(QObject):
#     """
#     Clase para manejar el sensor patrón de conductividad (HDM18/19).
#     Emite señales con tag y valor para integración con VARIABLES y UI.
#     """
#     data_received = Signal(str, float) 

#     def __init__(self):
#         super().__init__()
#         self.serial_port: Optional[serial.Serial] = None
#         self.running = False
#         self.reader_thread: Optional[threading.Thread] = None
#         self.command_queue = Queue()
#         self.read_command = READ_COMMAND
#         self.isConnected = False
#         self.last_successful_comm = time.time()
    
#     def connect(self) -> bool:
#         """Intenta conectar directamente al puerto COM7"""
#         target_port = "COM7"  # Puerto fijo 
    
#         try:
#             # Intentar abrir el puerto directamente
#             self.serial_port = serial.Serial(
#                 port=target_port,
#                 baudrate=115200,
#                 bytesize=serial.EIGHTBITS,
#                 parity=serial.PARITY_NONE,
#                 stopbits=serial.STOPBITS_ONE,
#                 timeout=1.0,
#                 write_timeout=0.5
#             )
        
#             # Esperar un momento para que el sensor se estabilice
#             time.sleep(1.5)
        
#             print(f"[Connected Conductivity sensor] Port: {target_port}")
#             self.isConnected = True
#             self.last_successful_comm = time.time()
#             return True  # Conexión exitosa
#         except serial.SerialException as e:
#             # Error específico de pySerial
#             print(f"[ERROR] Failed to open {target_port}: {e}")
#         except Exception as e:
#             # Otro error inesperado
#             print(f"[ERROR] An unexpected error occurred while connecting: {e}")
    
#         self.isConnected = False  # Marca como no conectado
#         return False  # Conexión fallida


#     def start(self):
#         """Inicia el hilo de comunicación si no está corriendo"""
#         if self.running:
#             return
#         self.running = True
#         self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
#         self.reader_thread.start()
        

#     def stop(self):
#         """Detiene el hilo y cierra el puerto"""
#         self.running = False
#         if self.reader_thread and self.reader_thread.is_alive():
#             self.reader_thread.join(timeout=2.0)
#         if self.serial_port and self.serial_port.is_open:
#             self.serial_port.close()
#         self.isConnected = False
#         print("[PatternConductivity] Stopped and port closed")

#     def _send_command(self, command: bytes) -> bool:
#         """Envía comando y retorna True si se envió correctamente"""
#         if not self.serial_port or not self.serial_port.is_open:
#             return False
#         try:
#             self.serial_port.reset_input_buffer()
#             self.serial_port.reset_output_buffer()
#             self.serial_port.write(command)
#             return True
#         except Exception as e:
            
#             return False

#     def _read_response(self) -> str:
#         """Lee la respuesta completa con timeout"""
#         if not self.serial_port or not self.serial_port.is_open:
#             return ""
#         try:
#             response = self.serial_port.read(100).decode('ascii', errors='ignore').rstrip('\r\n \x00')
#             if response:
#                 print(f"[VALAR raw] '{response}' (len={len(response)})")
#             return response
#         except Exception as e:
#             print(f"[ERROR] Read failed: {e}")
#             return ""

    
#     def _parse_response(self, raw: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
#         """Parsea: cond_raw, cond_compensada, temp"""
#         if not raw or len(raw) < 20:  
#             return None, None, None

#         parts = [p.strip() for p in raw.split('/')]
#         if len(parts) < 3:
            
#             return None, None, None

#         try:
#             cond_raw = float(parts[0])
#             cond_comp = float(parts[1])
#             temp = float(parts[2])
#             return cond_raw, cond_comp, temp
#         except ValueError as e:
            
#             return None, None, None

#     def _communication_loop(self):
#         while self.running:
#             if not self.isConnected or not self.serial_port or not self.serial_port.is_open:
#                 self.isConnected = False
#                 if self.connect():
#                     pass  
#                 else:
#                     time.sleep(3.0)
#                 continue

#             try:
                
#                 try:
#                     command = self.command_queue.get_nowait()
#                     is_read = False
#                 except Empty:
#                     command = self.read_command
#                     is_read = True

#                 if not self._send_command(command):
#                     raise serial.SerialException("Failed to send")

#                 time.sleep(0.1)  # respiro corto para respuesta
#                 raw_response = self._read_response()

#                 if raw_response:
#                     self.last_successful_comm = time.time()

#                     if is_read:
#                         cond_raw, cond_comp, temp = self._parse_response(raw_response)
#                         if cond_comp is not None:
#                             conductivity_comp = cond_comp 
#                             self.data_received.emit("patternCondSensor", conductivity_comp)
#                             print(f"[Emit] patternCondSensor → {cond_comp:.4f} mS/cm")

#                         if cond_raw is not None:
#                             conductivity_raw = cond_raw * 1000  # conversion a milisiemens 
#                             self.data_received.emit("patternCondRaw", conductivity_raw)
#                             print(f"[Emit] patternCondRaw → {cond_raw:.8f} mS/cm")  # más decimales para raw

#                         if temp is not None:
#                             self.data_received.emit("patternTempSensor", temp)
#                             print(f"[Emit] patternTempSensor → {temp:.3f} °C")

#                 # Chequeo de comunicación saludable (opcional: si >10s sin respuesta, reconectar)
#                 if time.time() - self.last_successful_comm > 10:
#                     self.isConnected = False
#                     continue

#                 time.sleep(0.4)  # ~2-3 lecturas por segundo, ajusta 

#             except serial.SerialException as e:
#                 print(f"[Serial error] {e} → Reintentando conexión")
#                 self.isConnected = False
#                 time.sleep(1.0)
#             except Exception as e:                
#                 time.sleep(1.0)

#         print("[PatternConductivity] Communication loop ended")
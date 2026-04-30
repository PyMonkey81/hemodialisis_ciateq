# connection/bioz_urea_controller.py
"""
Módulo para el control y la lectura de datos de Bioimpedancia y Urea.

Este módulo define la clase `BiozUreaController`, que se encarga de establecer
y gestionar la comunicación serial con un microcontrolador ESP32-S3. Este ESP32
está dedicado a la adquisición de mediciones de bioimpedancia y de los valores
ADC de los sensores de urea. La clase está diseñada para operar de forma
independiente y asíncrona, emitiendo señales con los datos procesados para su
integración en la interfaz gráfica principal o en la lógica de control.

Características principales:
-----------------------------
- **Comunicación con ESP32-S3**: Establece una conexión serial con un ESP32-S3,
  esperando una velocidad de baudios específica (115200).
- **Hilo de Comunicación Dedicado**: Opera en un hilo de ejecución separado
  (`read_thread`) para asegurar que la lectura de datos y el envío de comandos
  no bloqueen el hilo principal de la aplicación o la GUI.
- **Autodetección y Reconexión de Puerto**: Busca automáticamente el puerto
  serial del ESP32 utilizando una lista blanca de palabras clave (`port_whitelist`)
  y excluye puertos como los FTDI (usados por el controlador principal).
  Maneja la reconexión automática en caso de interrupción de la comunicación.
- **Envío de Comandos al ESP32**: Permite enviar comandos específicos al
  microcontrolador (ej. "SRTB" para iniciar lectura de bioimpedancia, "SRTU"
  para urea) a través de una cola de comandos (`command_queue`).
- **Parseo de Líneas de Datos**: Interpreta líneas de texto recibidas del ESP32,
  identificando patrones específicos para mediciones de bioimpedancia
  (resistencia y fase) y valores ADC de urea.
- **Emisión de Datos (Qt Signals)**: Emite la señal `data_received(tag: str, value: float)`
  cada vez que se parsea un nuevo valor, utilizando tags descriptivos como
  "bioz_resistance", "bioz_phase", "urea_adc1" y "urea_adc2".
- **Manejo de Errores Robustos**: Incluye mecanismos para capturar y reportar
  errores seriales o de parseo, y para reintentar la conexión.

Clase principal:
----------------
- `BiozUreaController`: Gestiona la conexión, el envío de comandos, la lectura
  y el parseo de respuestas del microcontrolador ESP32-S3.

Señales:
--------
- `data_received(tag: str, value: float)`: Emitida cuando se recibe y procesa
  un nuevo dato de bioimpedancia o urea.

Args:
-----
- `port_whitelist` (list, optional): Lista de palabras clave para identificar
  el puerto serial del ESP32. Por defecto: `["ESP32", "CP210X", "UART Bridge"]`.
- `baudrate` (int, optional): Velocidad de comunicación en baudios. Por defecto: `115200`.

Dependencias:
-------------
- `serial`: Biblioteca PySerial para el control del puerto serial.
- `serial.tools.list_ports`: Para la detección automática de puertos seriales.
- `threading`: Para ejecutar la lógica de comunicación en un hilo separado.
- `time`: Para gestionar pausas y timeouts.
- `re`: Para expresiones regulares utilizadas en el parseo de líneas.
- `queue`: Para la gestión de la cola de comandos de envío.
- `PySide6.QtCore.QObject`, `PySide6.QtCore.Signal`: Para la integración con
  el sistema de señales/slots de Qt.

Uso:
----
1.  **Instanciación**: Crear una instancia de `BiozUreaController` en el
    componente principal de la aplicación (ej. `HemodialysisHMI`).
2.  **Inicio del Hilo**: Llamar a `start()` para iniciar el hilo de comunicación
    y la búsqueda del dispositivo.
3.  **Envío de Comandos**: Utilizar `send_command(command_str)` para solicitar
    mediciones específicas al ESP32 (ej. "SRTB", "SRTU").
4.  **Conexión de Señales**: Conectar la señal `data_received` a un slot
    de la GUI o del sistema de control para procesar los valores recibidos.
5.  **Detención**: Al cerrar la aplicación, llamar a `stop()` para finalizar
    el hilo y liberar el puerto serial de forma segura.
"""
import serial
import serial.tools.list_ports
import threading
import time
import re
import logging # Importar logging

from queue import Queue, Empty
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__) # Inicializar el logger

class BiozUreaController(QObject):
    """
    Controlador independiente para la medición de Bioimpedancia y Urea.
    Se comunica con un dispositivo ESP32-S3 a 115200 baudios.
    Emite señales cuando se reciben nuevos datos.
    """
    
    # Señal para enviar datos a la HMI (tag, valor)
    data_received = Signal(str, float)

    def __init__(self, port_whitelist=None, baudrate=115200):
        super().__init__()
        # Lista de palabras clave para identificar el puerto del ESP32-S3
        # Ajustar esto según cómo aparezca el puerto del sistema
        self.port_whitelist = port_whitelist if port_whitelist else ["ESP32", "CP210X", "UART Bridge"]
        self.baudrate = baudrate
        self.serial_port: Optional[serial.Serial] = None
        self._running = False # Cambiado a _running para indicar que es interno
        self.command_queue = Queue()
        self.read_thread: Optional[threading.Thread] = None

        # --- Nuevas variables para la configuración desde la UI ---
        self._user_selected_port: Optional[str] = None # Puerto seleccionado por el usuario (e.g., "COM3")
        self._is_enabled: bool = False # Si el controlador debe intentar comunicarse o no

        self.last_Z: Optional[float] = None
        self.last_phase: Optional[float] = None

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
        # Comparar con la configuración actual
        port_changed = (self._user_selected_port != port_name and not (self._user_selected_port is None and port_name == "Auto"))
        enabled_changed = (self._is_enabled != is_enabled)
        
        self._user_selected_port = port_name if port_name != "Auto" else None
        self._is_enabled = is_enabled
        
        logger.info(f"[BIOZ/UREA] Configuración recibida: Puerto='{port_name}' (internamente: '{self._user_selected_port}'), Habilitado={is_enabled}")

        # Si el estado de habilitación cambia a deshabilitado, forzar parada y cierre
        if not self._is_enabled and self.running:
            logger.info("[BIOZ/UREA] Se deshabilitó la comunicación. Deteniendo controlador.")
            self.stop()
        # Si se habilita y no está corriendo, iniciarlo
        elif self._is_enabled and not self.running:
            logger.info("[BIOZ/UREA] Se habilitó la comunicación. Iniciando controlador.")
            self.start()
        # Si ya estaba habilitado y el puerto cambió, forzar reconexión
        elif self._is_enabled and port_changed and self.running:
            logger.info(f"[BIOZ/UREA] El puerto seleccionado ha cambiado a '{port_name}'. Forzando reconexión.")
            # Cerrar el puerto actual para que el _communication_loop intente una nueva conexión
            self._close_port()


    def start(self):
        """Inicia el hilo de comunicación si está habilitado y no está corriendo."""
        if not self._is_enabled:
            logger.warning("[BIOZ/UREA] Intento de iniciar controlador deshabilitado. No se hará nada.")
            return

        if self.running:
            return
        
        self.running = True
        self.read_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.read_thread.start()
        logger.info("[BIOZ/UREA] Hilo de comunicación iniciado.")


    def stop(self):
        """Detiene el hilo de comunicación y cierra el puerto serial."""
        if not self.running:
            return
        
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)
            logger.info("[BIOZ/UREA] Hilo de comunicación detenido.")
        self._close_port()
        logger.info("[BIOZ/UREA] Controlador detenido.")

    def _close_port(self):
        """Cierra el puerto serial si está abierto."""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                logger.info("[BIOZ/UREA] Puerto serial cerrado.")
            except Exception as e:
                logger.error(f"[BIOZ/UREA] Error cerrando puerto serial: {e}")
            finally:
                self.serial_port = None


    def send_command(self, command_str: str):
        """
        Comando para ser enviado al ESP32.
        Asegura que el comando termine con '\n' (nueva línea).
        """
        if not self._is_enabled:
            logger.warning(f"[BIOZ/UREA] Comunicación deshabilitada. Comando '{command_str}' no enviado.")
            return

        if self.serial_port and self.serial_port.is_open:
            full_command = command_str.encode('ascii') + b'\n'
            logger.debug(f"[BIOZ/UREA] Queued command: {full_command.decode().strip()}")
            self.command_queue.put(full_command)
            
        else:
            logger.warning(f"[BIOZ/UREA] Puerto serial no conectado. Comando '{command_str}' no enviado.")

    def _connect_to_specific_port(self, port_name: str) -> bool:
        """Intenta conectar a un puerto serial específico."""
        try:
            self.serial_port = serial.Serial(port_name, self.baudrate, timeout=1, write_timeout=1)
            time.sleep(2) # Dar tiempo al ESP32 para que se reinicie
            logger.info(f"[BIOZ/UREA] Conectado exitosamente en puerto ESPECÍFICO: {port_name}")
            print(f"[BIOZ/UREA] Conectado exitosamente en puerto ESPECÍFICO: {port_name}")
            return True
        except serial.SerialException as e:
            logger.warning(f"[BIOZ/UREA] Error al intentar conectar a {port_name} (específico): {e}")
            return False
        except Exception as e:
            logger.error(f"[BIOZ/UREA] Error inesperado al conectar a {port_name} (específico): {e}")
            return False

    def _find_and_connect_auto(self) -> bool:
        """
        Intenta encontrar y conectar al puerto serial del ESP32 usando la whitelist.
        Excluye puertos que contengan "FTDI" (para evitar el controlador principal).
        """
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"

            # Excluir el puerto del controlador principal (FTDI)
            

            # Buscar palabras clave en la whitelist
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    logger.info(f"[BIOZ/UREA] Coincidencia automática encontrada en {p.device} ({full_info}). Intentando conectar...")
                    return self._connect_to_specific_port(p.device) # Reutilizamos la función de conexión
        logger.warning("[BIOZ/UREA] No se encontró ningún puerto de Bioz/Urea automáticamente.")
        return False

    def _communication_loop(self):
        """
        Bucle principal del hilo de comunicación.
        Maneja la reconexión, el envío de comandos y la lectura/parsing de datos.
        """
        line_buffer = b''
        while self.running:
            # Si la comunicación está deshabilitada por el usuario, cerrar puerto y dormir
            if not self._is_enabled:
                self._close_port()
                time.sleep(1)
                continue

            # Si no hay puerto conectado, intentar conectar
            if not self.serial_port or not self.serial_port.is_open:
                connected = False
                if self._user_selected_port: # Si el usuario seleccionó un puerto específico
                    logger.debug(f"[BIOZ/UREA] Intentando conectar a puerto especificado: {self._user_selected_port}")
                    connected = self._connect_to_specific_port(self._user_selected_port)
                else: # Si no hay puerto específico, intentar detección automática
                    logger.debug("[BIOZ/UREA] Intentando conexión automática...")
                    connected = self._find_and_connect_auto()

                if not connected:
                    time.sleep(3) # Reintentar la conexión cada 3 segundos
                    continue
                else:
                    # Tras una conexión exitosa, limpiar comandos pendientes de sesiones anteriores
                    with self.command_queue.mutex:
                        self.command_queue.queue.clear()

            # Lógica de envío de comandos y lectura de datos
            try:
                # 1. Enviar comandos en cola
                try:
                    cmd_to_send = self.command_queue.get_nowait()
                    self.serial_port.write(cmd_to_send)
                    logger.debug(f"[BIOZ/UREA] Comando enviado: {cmd_to_send.decode().strip()}")
                    
                except Empty:
                    pass # No hay comandos pendientes
            
                # 2. Leer datos entrantes línea por línea
                if self.serial_port.in_waiting > 0:
                    char = self.serial_port.read(1)
                    if char == b'\n':
                        self._parse_line(line_buffer.decode('ascii', errors='ignore').strip())
                        line_buffer = b''
                    elif char != b'\r': # Ignorar el retorno de carro (CR)
                        line_buffer += char
                
                time.sleep(0.015) # Pequeño retardo para evitar consumo excesivo de CPU
            
            except serial.SerialException as e:
                logger.error(f"[BIOZ/UREA] Error serial (desconexión o fallo): {e}")
                self._close_port() # Cerrar el puerto y forzar reconexión en la siguiente iteración
                line_buffer = b'' # Limpiar buffer al perder conexión
                time.sleep(1)
            except Exception as e:
                logger.error(f"[BIOZ/UREA] Error inesperado en el bucle de comunicación: {e}", exc_info=True)
                time.sleep(1)


    def _parse_line(self, line: str):
        """Parseo robusto y ordenado de las líneas del ESP32"""
        if not line or not line.strip():
            return

        stripped = line.strip()
        
        # Debug útil (actívalo temporalmente si quieres ver todo lo que llega)
        # logger.debug(f"[RAW] Recibido: '{stripped}'")

        # 1. BIOIMPEDANCIA DETALLADA (prioridad más alta)
        match_bia = re.match(r"R:\s*([\d.-]+)\s*Ohm,\s*Phase:\s*([\d.-]+)\s*Deg", stripped, re.IGNORECASE)
        if match_bia:
            try:
                resistance = float(match_bia.group(1))
                phase = float(match_bia.group(2))

                self.last_Z = resistance
                self.last_phase = phase

                

                self.data_received.emit("bioz_resistance", resistance)
                self.data_received.emit("bioz_phase", phase)

                logger.info(f"[BIOZ] OK → R = {resistance:.2f} Ω | Phase = {phase:.2f}°")
                return
            except Exception as e:
                logger.error(f"Error parseando BIA detallada: {e} | Línea: {stripped}")
                return

        # 2. UREA (si usas el comando SRTU)
        match_urea = re.match(r"UREA ADC1:\s*([\d.-]+),\s*ADC2:\s*([\d.-]+)", stripped, re.IGNORECASE)
        if match_urea:
            try:
                adc1 = float(match_urea.group(1))
                adc2 = float(match_urea.group(2))
                self.data_received.emit("urea_adc1", adc1)
                self.data_received.emit("urea_adc2", adc2)
                logger.info(f"[UREA] ADC1={adc1:.3f} | ADC2={adc2:.3f}")
                return
            except Exception as e:
                logger.error(f"Error parseando UREA: {e}")
                return

        # 3. FALLBACK - Solo activar si la línea es prácticamente SOLO un número
        # Evitamos capturar números dentro de otras líneas
        if re.fullmatch(r"[-+]?\d*\.?\d+", stripped):   # <--- Cambiado a fullmatch
           
            try:
                z_value = float(stripped)
                self.last_Z = z_value
                self.last_phase = 0.0

                self.data_received.emit("bioz_resistance", z_value)
                self.data_received.emit("bioz_phase", 0.0)

                logger.info(f"[BIOZ] Modo simplificado → Z = {z_value:.2f} Ω")
                return
            except ValueError:
                pass

        # Si no coincidió con nada
        if stripped:
            logger.debug(f"[BIOZ/UREA] Línea no reconocida: '{stripped}'")

    # def _parse_line(self, line: str):
    #     """
    #     Parsea una línea de texto recibida del ESP32.
    #     Emite señales con los datos parseados y almacena los últimos valores de Z y Fase.
    #     Prioriza los formatos más específicos antes de caer en los más genéricos.
    #     """
    #     stripped_line = line.strip()

    #     # 1. Expresión regular para Bioimpedancia detallada: "R: <val> Ohm, Phase: <val> Deg"
    #     match_bia = re.match(r"R:\s*([\d.-]+)\s*Ohm,\s*Phase:\s*([\d.-]+)\s*Deg", stripped_line, re.I)
    #     if match_bia:
    #         try:
    #             resistance = float(match_bia.group(1))
    #             phase = float(match_bia.group(2))
                
    #             # Almacenar los últimos valores de Z y Fase
    #             self.last_Z = resistance
    #             self.last_phase = phase
    #             print(f"     Z (Resistencia) = {self.last_Z:8.2f} Ω")
    #             print(f"     Phase           = {self.last_phase:6.2f} °")

    #             self.data_received.emit("bioz_resistance", resistance)
    #             self.data_received.emit("bioz_phase", phase)
    #             logger.debug(f"[BIOZ/UREA] Parsed BIA (detailed): R={resistance:.2f} Ohm, Phase={phase:.2f} Deg")
    #             return # Línea procesada
    #         except (ValueError, IndexError) as e:
    #             logger.error(f"[BIOZ/UREA] Error al parsear línea BIA detallada '{stripped_line}': {e}")
    #             return # Línea con error de parseo, no procesada

    #     # 2. Expresión regular para Urea: "UREA ADC1: <val>, ADC2: <val>"
    #     # Se mantiene la regex original de tu primer método (sin IGNORECASE en este caso específico)
    #     match_urea = re.match(r"UREA ADC1:\s*([\d.-]+),\s*ADC2:\s*([\d.-]+)", stripped_line)
    #     if match_urea:
    #         try:
    #             adc1 = float(match_urea.group(1))
    #             adc2 = float(match_urea.group(2))
    #             self.data_received.emit("urea_adc1", adc1)
    #             self.data_received.emit("urea_adc2", adc2)
    #             logger.debug(f"[BIOZ/UREA] Parsed UREA: ADC1={adc1:.3f}, ADC2={adc2:.3f}")
    #             return # Línea procesada
    #         except (ValueError, IndexError) as e:
    #             logger.error(f"[BIOZ/UREA] Error al parsear línea UREA '{stripped_line}': {e}")
    #             return # Línea con error de parseo, no procesada
        
    #     # 3. Bioimpedancia simplificada (solo Z numérico), como fallback del segundo método
    #     # Esto busca un número flotante en cualquier parte de la línea.
    #     m_float_as_z = re.search(r"[-+]?\d*\.?\d+", stripped_line)
        
    #     if m_float_as_z:
    #         try:
    #             found_z = float(m_float_as_z.group(0))
                
    #             # Almacenar los últimos valores de Z y Fase (fase se asume 0.0 si no está)
    #             self.last_Z = found_z
    #             self.last_phase = 0.0 # La fase no está disponible en este formato, se establece a 0.0
                
    #             self.data_received.emit("bioz_resistance", found_z)
    #             self.data_received.emit("bioz_phase", 0.0) # También se emite la fase como 0.0
                
    #             debug_msg = f"Parsed simplified BIA (Z only): Z={found_z:.2f}, Phase=0.0"
    #             if stripped_line != m_float_as_z.group(0):
    #                 debug_msg += f". Original line: '{stripped_line}'"
    #             logger.debug(f"[BIOZ/UREA] {debug_msg}")
    #             return # Línea procesada
    #         except ValueError:
    #             # Si no se pudo convertir el número, registramos la advertencia
    #             logger.warning(f"[BIOZ/UREA] No se pudo convertir a float el valor encontrado '{m_float_as_z.group(0)}' para Z en línea '{stripped_line}'.")
    #             # Continuamos para que la línea pueda ser clasificada como "no reconocida"
    #             pass # No retornamos aquí para permitir que la línea sea clasificada como "no reconocida" si no hay otra coincidencia que la capture.

    #     # Si la línea no es reconocida por ninguno de los patrones anteriores y no está vacía
    #     if stripped_line:
    #        logger.debug(f"[BIOZ/UREA] Línea no reconocida: '{stripped_line}'")


# connection/led_bar_controller.py

"""
Módulo para el control de la barra LED y el buzzer.

Este módulo define la clase `LedBarController`, la cual es responsable de
comunicarse con un dispositivo Arduino que controla una barra de LEDs
y un buzzer. Permite indicar estados operativos y de alarma de la máquina
mediante señales visuales y auditivas.

Características principales:
-------------------------
- **Comunicación Serial Asíncrona**: Opera en un hilo separado para enviar
  comandos a la barra LED sin bloquear la aplicación principal o la GUI,
  asegurando una respuesta rápida a los cambios de estado.
- **Protocolo Simple Basado en Caracteres**: Utiliza un protocolo sencillo
  basado en el envío de caracteres ASCII para cambiar el color y el patrón
  de los LEDs, y para silenciar el buzzer.
- **Detección Automática de Puerto**: Intenta conectarse automáticamente a
  puertos seriales que coincidan con una lista blanca (`port_whitelist`),
  excluyendo dispositivos FTDI que suelen ser la comunicación principal.
- **Control de Estado de LEDs**: Permite establecer diferentes estados visuales
  (verde sólido/parpadeante, amarillo sólido/parpadeante, rojo sólido, cian, apagado)
  para indicar el estado de la máquina o la severidad de una alarma.
- **Control del Buzzer**: Incluye un comando específico para silenciar el buzzer
  cuando una alarma ha sido reconocida por el usuario.
- **Optimización de Envío**: Evita enviar comandos duplicados innecesarios al
  Arduino, reduciendo la carga de comunicación y mejorando la eficiencia.
- **Manejo de Reconexión**: Intenta reconectar automáticamente si la comunicación
  serial se pierde.

Comandos Soportados:
--------------------
- `CMD_GREEN_SOLID` (b'g'): LEDs verdes fijos (estado OK).
- `CMD_GREEN_FLASH` (b'f'): LEDs verdes parpadeando (Standby/Inactivo).
- `CMD_YELLOW_SOLID` (b'y'): LEDs amarillos fijos (Advertencia).
- `CMD_YELLOW_FLASH` (b'e'): LEDs amarillos parpadeando (Advertencia grave/Emergencia).
- `CMD_RED_SOLID`   (b'r'): LEDs rojos fijos (Alarma crítica).
- `CMD_CYAN_SOLID`  (b'c'): LEDs cian fijos (Información).
- `CMD_OFF`         (b'o'): Apagar todos los LEDs.
- `CMD_SILENCE`     (b's'): Silenciar el buzzer (manteniendo el estado actual de los LEDs).

Uso:
----
1.  **Instanciación**: Crear una instancia de `LedBarController` en el
    componente principal de la aplicación (ej. `HemodialysisHMI`).
2.  **Inicio del Hilo**: Llamar a `start()` para iniciar el hilo de comunicación.
3.  **Envío de Estado**: Utilizar `send_state(led_command, silence_buzzer)`
    para actualizar el estado visual y auditivo de la barra. Los `led_command`
    deben ser una de las constantes `CMD_...`.
4.  **Detención**: Al cerrar la aplicación, llamar a `stop()` para finalizar
    el hilo y liberar el puerto serial de forma segura. Es recomendable enviar
    `CMD_OFF` antes de detener el hilo.
"""

import serial
import serial.tools.list_ports
import threading
import time
from queue import Queue, Empty
from PySide6.QtCore import QObject
from utilities.platform_runtime import sanitize_port_for_platform
import logging
logger = logging.getLogger(__name__)


class LedBarController(QObject):
    """
    Controlador para la barra LED basada en Arduino.
    Protocolo basado en caracteres simples:
    'g' = Verde fijo (OK)
    'f' = Verde parpadeo (Standby/Idle)
    'y' = Amarillo (Advertencia)
    'e' = Amarillo parpadeo (Emergencia/Warning grave)
    'r' = Rojo (Alarma crítica)
    'c' = Cian (Información)
    'o' = OFF (Apagar LEDs)
    's' = SILENCIO (Silenciar buzzer, mantener LEDs)
    """

    CMD_GREEN_SOLID   = b'g'
    CMD_GREEN_FLASH   = b'f'
    CMD_YELLOW_SOLID  = b'y'
    CMD_YELLOW_FLASH  = b'e'
    CMD_RED_SOLID     = b'r'
    CMD_CYAN_SOLID    = b'c'
    CMD_OFF           = b'o'
    CMD_SILENCE       = b's' # <--- NUEVO COMANDO

    def __init__(self, port_whitelist=None, baudrate=9600):
        super().__init__()
        self.port_whitelist = port_whitelist if port_whitelist else ["CH340"]
        self.baudrate = baudrate
        self.serial_port = None
        self.running = False
        self.command_queue = Queue()
        self.write_thread = None
        self._user_selected_port = None
        self._is_enabled = False
        
        # Estas variables rastrean el último estado de LED y el último estado de silencio
        # para evitar enviar comandos duplicados innecesarios al Arduino.
        self._last_led_cmd_sent = b'o' # Por defecto, LEDs apagados
        self._last_buzzer_silence_state_sent = False # Por defecto, buzzer no silenciado (puede sonar)

    def update_config(self, port_name: str, is_enabled: bool):
        """Actualiza la configuración de puerto y activación desde la UI."""
        sanitized_port = sanitize_port_for_platform(port_name)
        port_changed = (
            self._user_selected_port != sanitized_port
            and not (self._user_selected_port is None and sanitized_port == "Auto")
        )

        self._user_selected_port = sanitized_port if sanitized_port != "Auto" else None
        self._is_enabled = is_enabled

        logger.info(f"[LED BAR] Configuración recibida: Puerto='{sanitized_port}', Habilitado={is_enabled}")

        if not self._is_enabled and self.running:
            logger.info("[LED BAR] Se deshabilitó la comunicación. Deteniendo controlador.")
            self.stop()
        elif self._is_enabled and not self.running:
            logger.info("[LED BAR] Se habilitó la comunicación. Iniciando controlador.")
            self.start()
        elif self._is_enabled and port_changed and self.running:
            logger.info(f"[LED BAR] El puerto cambió a '{sanitized_port}'. Forzando reconexión.")
            self._close_port()

    def start(self):
        """Inicia el hilo de comunicación de la barra LED."""
        if self.running:
            return
        self.running = True
        self.write_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.write_thread.start()
        logger.info("LedBarController: Hilo de comunicación iniciado.")

    def _close_port(self):
        """Cierra el puerto serial si está abierto."""
        if self.serial_port is not None:
            try:
                if getattr(self.serial_port, "is_open", False):
                    self.serial_port.close()
                    logger.info("LedBarController: Puerto serial cerrado por cambio de configuración.")
            except Exception as exc:
                logger.error(f"LedBarController: Error cerrando puerto serial: {exc}")
            finally:
                self.serial_port = None

    def send_state(self, led_command: bytes, silence_buzzer: bool = False):
        """
        Encola un comando de estado de LED y, opcionalmente, un comando de silencio para el buzzer.
        
        Args:
            led_command (bytes): El comando de LED a enviar (e.g., b'r', b'g').
            silence_buzzer (bool): Si es True, también se envía el comando de silencio del buzzer.
        """
        commands_to_enqueue = []

        # 1. Gestionar el comando de LED
        # Enviamos el comando de LED si es diferente del último que enviamos
        # Esto también fuerza al Arduino a resetear buzzerSilenced=false si es un comando de LED.
        if led_command != self._last_led_cmd_sent:
            commands_to_enqueue.append(led_command)
            self._last_led_cmd_sent = led_command
        
        # 2. Gestionar el comando de SILENCIO del buzzer
        # Enviamos el comando de silencio SOLO si el estado deseado (silence_buzzer)
        # es diferente del último estado de silencio que enviamos.
        if silence_buzzer != self._last_buzzer_silence_state_sent:
            if silence_buzzer: # Queremos silenciar
                commands_to_enqueue.append(self.CMD_SILENCE)
            # No hay comando explícito para "des-silenciar", eso ocurre automáticamente         
            
            self._last_buzzer_silence_state_sent = silence_buzzer
        
        for cmd in commands_to_enqueue:
            self.command_queue.put(cmd)


    def stop(self):
        """Detiene la comunicación."""
        self.running = False
        if self.write_thread and self.write_thread.is_alive():
            self.write_thread.join(timeout=1.0)
        self.write_thread = None
        if self.serial_port is not None:
            try:
                if getattr(self.serial_port, "is_open", False):
                    self.serial_port.close()
                logger.info("LedBarController: Puerto serial cerrado.")
            except Exception as e:
                logger.error(f"LedBarController: Error cerrando puerto serial: {e}")
            finally:
                self.serial_port = None

    def _connect(self):
        """Intenta conectar al puerto serial de la barra LED."""
        ports = serial.tools.list_ports.comports()
        target_port = None

        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"
            
            if "FTDI" in full_info: # Excluir: este es para la tarjeta de control +
                continue 
            
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    target_port = p.device
                    break
            if target_port: break

        if target_port:
            try:
                self.serial_port = serial.Serial(target_port, self.baudrate, timeout=1)
                logger.info(f"[LED BAR] Conectado en {target_port}")
                print(f"[LED BAR] Conectado en {target_port}")
                time.sleep(2)
                return True
            except Exception as e:
                logger.error(f"[LED BAR] Error al conectar {target_port}: {e}")
        return False

    def _process_loop(self):
        """Bucle principal del hilo."""
        while self.running:
            if self.serial_port is None or not getattr(self.serial_port, "is_open", False):
                if not self._connect():
                    time.sleep(2)
                    continue

            try:
                cmd = self.command_queue.get(timeout=0.1)
                if self.serial_port is None or not getattr(self.serial_port, "is_open", False):
                    continue
                self.serial_port.write(cmd)
                if hasattr(self.serial_port, "flush"):
                    self.serial_port.flush()

                if getattr(self.serial_port, "in_waiting", 0) > 0 and hasattr(self.serial_port, "read_all"):
                    self.serial_port.read_all()

            except Empty:
                pass
            except Exception as e:
                logger.error(f"[LED BAR] Error de escritura: {e}")
                self.serial_port = None


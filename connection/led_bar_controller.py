# connection/led_bar_controller.py

import serial
import serial.tools.list_ports
import threading
import time
from queue import Queue, Empty
from PySide6.QtCore import QObject

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
        self.port_whitelist = port_whitelist if port_whitelist else ["CH340", "USB-SERIAL", "ARDUINO", "USB SERIAL"]
        self.baudrate = baudrate
        self.serial_port = None
        self.running = False
        self.command_queue = Queue()
        self.write_thread = None
        
        # Estas variables rastrean el último estado de LED y el último estado de silencio
        # para evitar enviar comandos duplicados innecesarios al Arduino.
        self._last_led_cmd_sent = b'o' # Por defecto, LEDs apagados
        self._last_buzzer_silence_state_sent = False # Por defecto, buzzer no silenciado (puede sonar)


    def start(self):
        """Inicia el hilo de comunicación de la barra LED."""
        if self.running:
            return
        self.running = True
        self.write_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.write_thread.start()

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
            # en el Arduino cuando recibe un comando de LED.
            
            self._last_buzzer_silence_state_sent = silence_buzzer
        
        # Poner los comandos en la cola, en orden
        # Es importante que el comando de LED vaya primero y el de SILENCIO segundo, si ambos se envían.
        # Si queremos silenciar y también cambiar el LED, el Arduino primero recibirá el LED (buzzerSilenced=false)
        # y luego inmediatamente el SILENCIO (buzzerSilenced=true).
        for cmd in commands_to_enqueue:
            self.command_queue.put(cmd)


    def stop(self):
        """Detiene la comunicación."""
        self.running = False
        if self.write_thread:
            self.write_thread.join(timeout=1.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def _connect(self):
        """Intenta conectar al puerto serial de la barra LED."""
        ports = serial.tools.list_ports.comports()
        target_port = None

        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"
            
            if "FTDI" in full_info: # Excluir el PLC principal
                continue 
            
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    target_port = p.device
                    break
            if target_port: break

        if target_port:
            try:
                self.serial_port = serial.Serial(target_port, self.baudrate, timeout=1)
                print(f"[LED BAR] Conectado en {target_port}")
                time.sleep(2)
                return True
            except Exception as e:
                print(f"[LED BAR] Error al conectar {target_port}: {e}")
        return False

    def _process_loop(self):
        """Bucle principal del hilo."""
        while self.running:
            if not self.serial_port or not self.serial_port.is_open:
                if not self._connect():
                    time.sleep(2)
                    continue

            try:
                cmd = self.command_queue.get(timeout=0.1)
                self.serial_port.write(cmd)
                self.serial_port.flush()
                #print(f"[LED BAR] Enviado: {cmd.decode().strip()}")

                # Leer el eco del Arduino para vaciar el buffer (tu Arduino hace Serial.write(receivedChar))
                if self.serial_port.in_waiting > 0:
                    self.serial_port.read_all()
                    
            except Empty:
                pass
            except Exception as e:
                print(f"[LED BAR] Error de escritura: {e}")
                self.serial_port = None



# # connection/led_bar_controller.py

# import serial
# import serial.tools.list_ports
# import threading
# import time
# from queue import Queue, Empty
# from PySide6.QtCore import QObject

# class LedBarController(QObject):
#     """
#     Controlador para la barra LED basada en Arduino.
#     Protocolo basado en caracteres simples:
#     'g' = Verde fijo (OK)
#     'f' = Verde parpadeo (Standby/Idle)
#     'y' = Amarillo (Advertencia)
#     'e' = Amarillo parpadeo (Emergencia/Warning grave)
#     'r' = Rojo (Alarma crítica)
#     'c' = Cian (Información)
#     'o' = apagado
#     """

#     # Comandos definidos según tu código Arduino
#     CMD_GREEN_SOLID   = b'g'
#     CMD_GREEN_FLASH   = b'f'
#     CMD_YELLOW_SOLID  = b'y'
#     CMD_YELLOW_FLASH  = b'e'
#     CMD_RED_SOLID     = b'r'
#     CMD_CYAN_SOLID    = b'c'
#     CMD_OFF = b'o'
#     CMD_SILENCE = b's' 
    
#     # Comando de apagado (no definido en tu arduino, enviamos 'f' o 'g' como default safe)
#     CMD_SAFE_MODE     = b'f' 

#     def __init__(self, port_whitelist=None, baudrate=9600):
#         super().__init__()
#         # Lista de nombres comunes para Arduinos chinos u originales
#         self.port_whitelist = port_whitelist if port_whitelist else ["CH340", "USB-SERIAL", "ARDUINO", "USB SERIAL"]
#         self.baudrate = baudrate
#         self.serial_port = None
#         self.running = False
#         self.command_queue = Queue()
#         self.write_thread = None
        
#         # Para evitar enviar el mismo comando repetidamente
#         self.last_sent_cmd = None

#     def start(self):
#         """Inicia el hilo de comunicación."""
#         if self.running:
#             return
#         self.running = True
#         self.write_thread = threading.Thread(target=self._process_loop, daemon=True)
#         self.write_thread.start()

#     def send_state(self, command: bytes):
#         """
#         Encola un comando de estado. 
#         Solo lo encola si es diferente al último enviado para no saturar el Arduino.
#         """
#         if command != self.last_sent_cmd:
#             # Vaciamos la cola para que el nuevo estado tenga prioridad inmediata
#             with self.command_queue.mutex:
#                 self.command_queue.queue.clear()
            
#             self.command_queue.put(command)

#     def stop(self):
#         """Detiene la comunicación limpiamente."""
#         self.running = False
#         if self.write_thread:
#             self.write_thread.join(timeout=1.0)
#         if self.serial_port and self.serial_port.is_open:
#             self.serial_port.close()

#     def _find_and_connect(self):
#         """Busca un puerto que NO sea el de la máquina (FTDI) y coincida con la whitelist."""
#         ports = serial.tools.list_ports.comports()
        
#         for p in ports:
#             desc = p.description.upper()
#             manuf = p.manufacturer.upper() if p.manufacturer else ""
#             full_info = f"{desc} {manuf}"

#             # IGNORAR el puerto de la máquina principal
#             if "FTDI" in full_info:
#                 continue

#             # BUSCAR coincidencias con Arduino
#             for keyword in self.port_whitelist:
#                 if keyword in full_info:
#                     try:
#                         self.serial_port = serial.Serial(p.device, self.baudrate, timeout=1)
#                         time.sleep(2) # Esperar reset del Arduino
#                         print(f"[LED BAR] Conectado exitosamente en: {p.device}")
#                         return True
#                     except Exception as e:
#                         print(f"[LED BAR] Error al intentar conectar {p.device}: {e}")
        
#         return False

#     def _process_loop(self):
#         """Bucle principal de escritura."""
#         while self.running:
#             # 1. Gestión de Conexión
#             if not self.serial_port or not self.serial_port.is_open:
#                 if not self._find_and_connect():
#                     time.sleep(2) # Reintentar cada 2 segs si no encuentra puerto
#                     continue

#             # 2. Envío de Comandos
#             try:
#                 # Esperar comando (bloqueante con timeout para permitir checkear self.running)
#                 cmd = self.command_queue.get(timeout=0.5)
                
#                 self.serial_port.write(cmd)
#                 self.serial_port.flush()
#                 self.last_sent_cmd = cmd
                
#                 # Leer el eco del Arduino (tu código Arduino hace Serial.write(leido))
#                 # Esto es importante para vaciar el buffer de entrada del PC
#                 if self.serial_port.in_waiting > 0:
#                     self.serial_port.read_all()
                    
#             except Empty:
#                 pass # No hay comandos nuevos, mantener estado actual
#             except Exception as e:
#                 print(f"[LED BAR] Error de comunicación: {e}")
#                 self.serial_port = None # Forzar reconexión
#                 self.last_sent_cmd = None

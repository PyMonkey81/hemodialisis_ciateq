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
    """

    # Comandos definidos según tu código Arduino
    CMD_GREEN_SOLID   = b'g'
    CMD_GREEN_FLASH   = b'f'
    CMD_YELLOW_SOLID  = b'y'
    CMD_YELLOW_FLASH  = b'e'
    CMD_RED_SOLID     = b'r'
    CMD_CYAN_SOLID    = b'c'
    
    # Comando de apagado (no definido en tu arduino, enviamos 'f' o 'g' como default safe)
    CMD_SAFE_MODE     = b'f' 

    def __init__(self, port_whitelist=None, baudrate=9600):
        super().__init__()
        # Lista de nombres comunes para Arduinos chinos u originales
        self.port_whitelist = port_whitelist if port_whitelist else ["CH340", "USB-SERIAL", "ARDUINO", "USB SERIAL"]
        self.baudrate = baudrate
        self.serial_port = None
        self.running = False
        self.command_queue = Queue()
        self.write_thread = None
        
        # Para evitar enviar el mismo comando repetidamente
        self.last_sent_cmd = None

    def start(self):
        """Inicia el hilo de comunicación."""
        if self.running:
            return
        self.running = True
        self.write_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.write_thread.start()

    def send_state(self, command: bytes):
        """
        Encola un comando de estado. 
        Solo lo encola si es diferente al último enviado para no saturar el Arduino.
        """
        if command != self.last_sent_cmd:
            # Vaciamos la cola para que el nuevo estado tenga prioridad inmediata
            with self.command_queue.mutex:
                self.command_queue.queue.clear()
            
            self.command_queue.put(command)

    def stop(self):
        """Detiene la comunicación limpiamente."""
        self.running = False
        if self.write_thread:
            self.write_thread.join(timeout=1.0)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def _find_and_connect(self):
        """Busca un puerto que NO sea el de la máquina (FTDI) y coincida con la whitelist."""
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            desc = p.description.upper()
            manuf = p.manufacturer.upper() if p.manufacturer else ""
            full_info = f"{desc} {manuf}"

            # IGNORAR el puerto de la máquina principal
            if "FTDI" in full_info:
                continue

            # BUSCAR coincidencias con Arduino
            for keyword in self.port_whitelist:
                if keyword in full_info:
                    try:
                        self.serial_port = serial.Serial(p.device, self.baudrate, timeout=1)
                        time.sleep(2) # Esperar reset del Arduino
                        print(f"[LED BAR] Conectado exitosamente en: {p.device}")
                        return True
                    except Exception as e:
                        print(f"[LED BAR] Error al intentar conectar {p.device}: {e}")
        
        return False

    def _process_loop(self):
        """Bucle principal de escritura."""
        while self.running:
            # 1. Gestión de Conexión
            if not self.serial_port or not self.serial_port.is_open:
                if not self._find_and_connect():
                    time.sleep(2) # Reintentar cada 2 segs si no encuentra puerto
                    continue

            # 2. Envío de Comandos
            try:
                # Esperar comando (bloqueante con timeout para permitir checkear self.running)
                cmd = self.command_queue.get(timeout=0.5)
                
                self.serial_port.write(cmd)
                self.serial_port.flush()
                self.last_sent_cmd = cmd
                
                # Leer el eco del Arduino (tu código Arduino hace Serial.write(leido))
                # Esto es importante para vaciar el buffer de entrada del PC
                if self.serial_port.in_waiting > 0:
                    self.serial_port.read_all()
                    
            except Empty:
                pass # No hay comandos nuevos, mantener estado actual
            except Exception as e:
                print(f"[LED BAR] Error de comunicación: {e}")
                self.serial_port = None # Forzar reconexión
                self.last_sent_cmd = None


    # ────────────────────────────────────────────────
    #              LED Bar Logic
    # ────────────────────────────────────────────────
    def update_led_bar_state(self):
        """
        Determina el color de la barra LED según la prioridad:
        1. Desconexión Máquina -> Amarillo Parpadeo ('e')
        2. Alarma Roja -> Rojo Fijo ('r')
        3. Alarma Naranja -> Amarillo Parpadeo ('e')
        4. Alarma Amarilla -> Amarillo Fijo ('y')
        5. Alarma Cian -> Cian Fijo ('c')
        6. Sin Alarmas -> Verde Fijo ('g')
        """
        # Prioridad 1: Error de comunicación con la máquina principal
        if not self.serial_comm or not self.serial_comm.is_connected:
            self.led_bar.send_state(self.led_bar.CMD_YELLOW_FLASH) # O CMD_RED_SOLID según prefieras
            return

        # Prioridad 2: Alarmas Activas
        if self.active_alarms:
            # Mapeo de prioridades (Mayor número = Mayor prioridad)
            priority_map = {"rojo": 4, "naranja": 3, "amarillo": 2, "cian": 1}
            
            # Obtener la alarma con mayor prioridad
            # active_alarms es una lista de tuplas: (name, value, level)
            top_alarm = max(self.active_alarms, key=lambda x: priority_map.get(x[2], 0))
            level = top_alarm[2]

            if level == "rojo":
                self.led_bar.send_state(self.led_bar.CMD_RED_SOLID) # 'r'
            elif level == "naranja":
                self.led_bar.send_state(self.led_bar.CMD_YELLOW_FLASH) # 'e' (Emergencia en tu arduino)
            elif level == "amarillo":
                self.led_bar.send_state(self.led_bar.CMD_YELLOW_SOLID) # 'y'
            elif level == "cian":
                self.led_bar.send_state(self.led_bar.CMD_CYAN_SOLID)   # 'c'
        
        else:
            # Prioridad 3: Operación Normal
            # Puedes cambiar a CMD_GREEN_FLASH ('f') si prefieres efecto "respiración"
            self.led_bar.send_state(self.led_bar.CMD_GREEN_SOLID) # 'g'

# # connection/serial_communication.py
import serial
import serial.tools.list_ports
import threading
import time
import struct
import crcmod
from queue import Queue, Empty
from typing import Optional

# IMPORTANTE: Importamos librerías de Qt para las señales
from PySide6.QtCore import QObject, Signal
from core.variables_map import VARIABLES, ANALOG_MAP 

# CRC16 Modbus 
crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF, rev=True, xorOut=0x0000)

# Comandos fijos (Lectura)
COMANDO_LEER_BOOLEANOS = bytes.fromhex("11 11 00 3C")
COMANDO_LEER_ANALOGICOS = bytes.fromhex("12 AA 00 47")

# Tamaño de respuesta esperado (incluye 2 bytes de CRC)
TAMAÑO_RESPUESTA_BOOLEANOS = 65 # 3 Bytes header + 60 Bytes datos + 2 bytes  CRC
TAMAÑO_RESPUESTA_ANALOGICOS = 573 # 3 bytes header + 71 doubles* 8 bytes/double + 2 bytes CRC
TAMAÑO_RESPUESTA_ESCRITURA = 6 # 3 bytes header + 1 byte respuesta + 2 bytes CRC

# HEREDA DE QObject
class ComunicacionSerial(QObject):
    # Definimos la señal: envía (nombre_variable, valor)
    data_received = Signal(str, float)
    
    def __init__(self): 
        super().__init__()
        self.puerto: Optional[serial.Serial] = None
        self.ejecutando = False
        self.hilo: Optional[threading.Thread] = None
        self.cola_comandos = Queue()
        self.siguiente_comando_lectura = COMANDO_LEER_BOOLEANOS
        self.conectado = False
        self.ultimo_ok = time.time() # detecta desconexión

    def conectar(self) -> bool:
        """Intenta conectar al dispositivo FTDI."""
        for p in serial.tools.list_ports.comports():
            if p.manufacturer and "FTDI" in p.manufacturer.upper():
                try:
                    self.puerto = serial.Serial(
                        port=p.device,
                        baudrate=115200,
                        timeout=1.0,
                        write_timeout=0.5
                    )
                    time.sleep(1.5)
                    self.conectado = True
                    print(f"[OK] Conectado a {p.device}")
                    return True
                except Exception as e:
                    print(f"[ERROR] Fallo al abrir puerto {p.device}: {e}")
        print("[ERROR] No se encontró dispositivo FTDI")
        self.conectado = False
        return False

    def iniciar_lectura(self):
        if self.ejecutando:
            return
        self.ejecutando = True
        self.hilo = threading.Thread(target=self._bucle_principal, daemon=True) 
        self.hilo.start()

    def _bucle_principal(self):
        """Bucle principal de comunicación lectura/comandos en cola"""
        while self.ejecutando:
            if not self.conectado or not self.puerto or not self.puerto.is_open: # Reconexion
                self.conectado = False
                if self.conectar():
                    self.ultimo_ok = time.time()
                time.sleep(2.0)
                continue

            try:  # el comando de escritura tiene prioridad
                try:
                    comando = self.cola_comandos.get_nowait()
                    es_escritura = True
                except Empty:
                    comando = self.siguiente_comando_lectura
                    es_escritura = False

                if not self._enviar_comando(comando): # envia comando
                    raise serial.SerialException("Fallo al enviar comando")
                # Verifica el tamaño de la respuesta
                tamaño = ( 
                    TAMAÑO_RESPUESTA_ESCRITURA if es_escritura
                    else TAMAÑO_RESPUESTA_BOOLEANOS if comando == COMANDO_LEER_BOOLEANOS
                    else TAMAÑO_RESPUESTA_ANALOGICOS
                )

                datos = self._leer_respuesta(tamaño)
                if not datos:
                    raise TimeoutError("Timeout lectura")
                # Validación de datos recibidos - CRC
                crc_rec = (datos[-2] << 8) | datos[-1]
                crc_calc = crc16(datos[:-2])
                if crc_rec != crc_calc:
                    raise ValueError("Error CRC")

                self.ultimo_ok = time.time()
                payload = datos[:-2]
                
                if es_escritura:
                    if len(payload) >= 4 and payload[3] == 0xFF:
                        print("[OK] Escritura confirmada")
                else:
                    self._procesar_lectura(payload)

                if not es_escritura:
                    self.siguiente_comando_lectura = (
                        COMANDO_LEER_ANALOGICOS if comando == COMANDO_LEER_BOOLEANOS else COMANDO_LEER_BOOLEANOS
                    )
                
                # IMPORTANTE: Pausa pequeña para no saturar la CPU
                time.sleep(0.05) 

            except Exception as e:
                if self.ejecutando:
                    self.conectado = False
                    if self.puerto:
                        try: self.puerto.close()
                        except: pass
                    self.puerto = None
                time.sleep(1.0)
        
    def _enviar_comando(self, comando: bytes) -> bool:
        if not self.puerto or not self.puerto.is_open: return False
        try:
            crc = crc16(comando)
            trama = comando + bytes([crc >> 8, crc & 0xFF]) 
            self.puerto.reset_input_buffer()
            self.puerto.write(trama)
            return True
        except: return False

    def _leer_respuesta(self, tamaño: int) -> Optional[bytes]:
        if not self.puerto or not self.puerto.is_open: return None
        try:
            datos = self.puerto.read(tamaño)
            return datos if len(datos) == tamaño else None
        except: return None

    def _procesar_lectura(self, payload: bytes):
        # === BOOLEANOS ===
        if payload.startswith(b'\x11\x11\x00') and len(payload) >= 63:
            if 0x01 in VARIABLES:
                for i in range(60):
                    byte_val = payload[3 + i]
                    valor = 1.0 if byte_val else 0.0
                    if i in VARIABLES[0x01]:
                        nombre = VARIABLES[0x01][i]["tag"]
                        # EMITIMOS SEÑAL 
                        self.data_received.emit(nombre, valor)

        # === ANALÓGICOS ===
        elif payload.startswith(b'\x12\xAA\x00') and len(payload) >= 571:
            for idx in range(71):
                grupo, addr = ANALOG_MAP[idx]
                if grupo in VARIABLES and addr in VARIABLES[grupo]:
                    offset = 3 + idx * 8
                    try:
                        valor = struct.unpack_from('<d', payload, offset)[0]
                        nombre = VARIABLES[grupo][addr]["tag"]
                        # EMITIMOS SEÑAL
                        self.data_received.emit(nombre, valor)
                    except: pass

    # ... métodos escribir_booleano y escribir_double ...
    def escribir_booleano(self, addr: int, valor: bool):
        cmd = bytes([0x21, 0x11, addr, 0x01 if valor else 0x00])
        self.cola_comandos.put(cmd)

    # def escribir_double(self, addr: int, valor: float):
    #     cmd = bytes([0x22, 0xAA, addr]) + struct.pack('<d', valor)
    #     self.cola_comandos.put(cmd)
    
    def escribir_double(self, group_code: int, var_id_in_group: int, valor: float):
        """
        Genera y encola el comando para escribir un valor double en una variable.
        El 'group_code' se codifica en el primer byte del comando.
        """
        # El primer byte del comando será 0x20 (para escritura) OR con el código del grupo
        command_byte = 0x20 | group_code # Ejemplo: 0x20 | 0x03 = 0x23
        
        # El comando se construye: [Comando_con_Grupo, Tipo_Analog, ID_en_Grupo] + datos
        cmd = bytes([command_byte, 0xAA, var_id_in_group]) + struct.pack('<d', valor)
        self.cola_comandos.put(cmd)



    def detener(self):
        self.ejecutando = False
        puerto_local = self.puerto 
        if puerto_local and puerto_local.is_open:
            try: puerto_local.close() 
            except: pass
        if self.hilo and self.hilo.is_alive():
            self.hilo.join(timeout=2.0)
        self.puerto = None
        print("[INFO] Serial detenido")

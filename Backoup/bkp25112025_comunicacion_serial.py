# comunicacion_serial.py
import serial
import serial.tools.list_ports
import threading
import time
import struct
import crcmod
from queue import Queue, Empty
from typing import Callable, Optional
from resources.variables_map_respaldo import VARIABLES, ANALOG_MAP

# from variables_map import VARIABLES
# from variables_map import ANALOG_MAP

# === CONFIG ===
BAUD_RATE = 115200
TIMEOUT = 1.0
MAX_RETRIES = 3
RETRY_DELAY = 0.2

# CRC Modbus RTU
crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF, rev=True)

# === COMANDOS FIJOS ===
COMMAND_BOOLEAN_READ = bytes.fromhex("11 11 00 3C")  # 60 booleanos
COMMAND_ANALOG_READ  = bytes.fromhex("12 AA 00 47")  # 71 doubles

# === TAMAÑOS ===
RESP_BOOL_SIZE   = 65
RESP_ANALOG_SIZE = 573

class ComunicacionSerial:
    def __init__(self, callback: Callable[[str, float], None]):
        self.callback = callback
        self.conn: Optional[serial.Serial] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.cola = Queue()
        self.siguiente = COMMAND_BOOLEAN_READ

    def conectar(self):
        """
        Esta función busca el puerto serial de la tarjeta de control de la máquina de hemodiálisis, en particular busca donde esta conectado
        el FTDI, y realiza la conexión con los parámetros descritos. si todo esta correcto envia un true si no, imprime que no se conecto y 
        regresa un false
        """
        for p in serial.tools.list_ports.comports():
            if "FTDI" in p.manufacturer or "USB" in p.description:
                try:
                    self.conn = serial.Serial(p.device, BAUD_RATE, timeout=TIMEOUT)
                    print(f"[OK] Conectado a {p.device}")
                    return True
                except: pass
        print("[ERROR] Puerto no encontrado")
        return False

    def iniciar_lectura(self):
        if not self.conn: return False
        self.running = True
        self.thread = threading.Thread(target=self._bucle, daemon=True)
        self.thread.start()
        return True

    def _bucle(self):
        while self.running and self.conn.is_open:
            try:
                # 1. Prioridad: escritura
                try:
                    cmd = self.cola.get_nowait()
                    size = 6
                except Empty:
                    cmd = self.siguiente
                    size = RESP_BOOL_SIZE if cmd == COMMAND_BOOLEAN_READ else RESP_ANALOG_SIZE

                # 2. ENVÍO: CRC en Hi Lo (como LabVIEW)
                crc = crc16(cmd)
                frame = cmd + bytes([crc >> 8, crc & 0xFF])  # Hi Lo
                print(f"[TX] {frame.hex(' ').upper()}")

                self.conn.reset_input_buffer()
                self.conn.write(frame)

                # 3. LECTURA
                data = self._leer(size)
                if not data:
                    print("[TIMEOUT] Sin respuesta")
                    continue

                # 4. VALIDAR CRC: RECIBIDO EN Hi Lo
                crc_rec = (data[-2] << 8) | data[-1]  # Hi Lo
                crc_calc = crc16(data[:-2])
                if crc_calc != crc_rec:
                    print(f"[CRC ERROR] Calc: {crc_calc:04X}, Rec: {crc_rec:04X}")
                    continue

                # 5. PROCESAR
                if len(data) == 6:
                    if data[3] == 0xFF:
                        print("[OK] Escritura confirmada")
                else:
                    self._procesar_lectura(data[:-2])  # Sin CRC

                # 6. ALTERNAR
                if cmd in (COMMAND_BOOLEAN_READ, COMMAND_ANALOG_READ):
                    self.siguiente = COMMAND_ANALOG_READ if cmd == COMMAND_BOOLEAN_READ else COMMAND_BOOLEAN_READ

                time.sleep(0.1)
            except Exception as e:
                print(f"[EX] {e}")
                break

    def _leer(self, size):
        for _ in range(MAX_RETRIES):
            data = self.conn.read(size)
            if len(data) == size:
                return data
            time.sleep(RETRY_DELAY)
        return None

    def _procesar_lectura(self, payload: bytes):
        print(f"[RX] {payload[:10].hex(' ').upper()}... ({len(payload)} bytes)")

        # === BOOLEANOS (0x01) ===
        if payload.startswith(b'\x11\x11\x00'):
            if 0x01 not in VARIABLES:
                print("[ERROR] Falta grupo 0x01 en VARIABLES")
                return
            for i, b in enumerate(payload[3:63]):  # 60 bytes
                if i not in VARIABLES[0x01]:
                    continue
                nombre = VARIABLES[0x01][i]["name"]
                self.callback(nombre, 1.0 if b else 0.0)

        # === ANALÓGICOS (bloque continuo de 71 doubles) ===
        elif payload.startswith(b'\x12\xAA\x00'):
            if len(ANALOG_MAP) != 71:
                print(f"[ERROR] ANALOG_MAP tiene {len(ANALOG_MAP)} elementos, debe ser 71")
                return
            for idx in range(71):
                start = 3 + idx * 8
                if start + 8 > len(payload):
                    print(f"[WARNING] Datos incompletos en índice {idx}")
                    break
                valor = struct.unpack('<d', payload[start:start+8])[0]
                grupo, addr = ANALOG_MAP[idx]
                if grupo not in VARIABLES or addr not in VARIABLES[grupo]:
                    continue
                nombre = VARIABLES[grupo][addr]["name"]
                self.callback(nombre, valor)

    # === ESCRITURA ===
    def escribir_booleano(self, addr: int, valor: bool):
        cmd = bytes([0x21, 0x11, addr, 0x01 if valor else 0x00])
        self.cola.put(cmd)

    def escribir_double(self, addr: int, valor: float):
        cmd = bytes([0x22, 0xAA, addr]) + struct.pack('<d', valor)
        self.cola.put(cmd)

    def detener(self):
        self.running = False
        if self.thread: self.thread.join()
        if self.conn: self.conn.close()
        print("[INFO] Puerto cerrado")


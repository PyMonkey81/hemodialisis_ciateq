# # connection/comunicacion_serial.py
# import serial
# import serial.tools.list_ports
# import threading
# import time
# import struct
# import crcmod
# from queue import Queue, Empty
# from typing import Callable, Optional

# from core.variables_map import VARIABLES, ANALOG_MAP 

# # CRC16 Modbus
# # Implementación correcta del CRC16-Modbus
# crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF, rev=True, xorOut=0x0000)

# # Comandos fijos (Lectura)
# COMANDO_LEER_BOOLEANOS = bytes.fromhex("11 11 00 3C")
# COMANDO_LEER_ANALOGICOS = bytes.fromhex("12 AA 00 47")

# # Tamaños de respuesta esperados (incluyendo 2 bytes de CRC)
# TAMAÑO_RESPUESTA_BOOLEANOS = 65  # 3 bytes de cabecera + 60 bytes de datos + 2 bytes de CRC
# TAMAÑO_RESPUESTA_ANALOGICOS = 573 # 3 bytes de cabecera + (71 doubles * 8 bytes/double) + 2 bytes de CRC
# TAMAÑO_RESPUESTA_ESCRITURA = 6    # 3 bytes de cabecera + 1 byte de respuesta + 2 bytes de CRC

# class ComunicacionSerial:
#     def __init__(self, callback: Callable[[str, float], None]):
#         self.callback = callback
#         self.puerto: Optional[serial.Serial] = None
#         self.ejecutando = False
#         self.hilo: Optional[threading.Thread] = None
#         self.cola_comandos = Queue()
#         # Inicia leyendo booleanos
#         self.siguiente_comando_lectura = COMANDO_LEER_BOOLEANOS
#         self.conectado = False
#         self.ultimo_ok = time.time()  # para detectar desconexión (timeout manual)

#     def conectar(self) -> bool:
#         """Intenta conectar al dispositivo FTDI enumerando los puertos disponibles."""
#         for p in serial.tools.list_ports.comports():
#             # Búsqueda sensible a mayúsculas/minúsculas de FTDI
#             if p.manufacturer and "FTDI" in p.manufacturer.upper():
#                 try:
#                     self.puerto = serial.Serial(
#                         port=p.device,
#                         baudrate=115200,
#                         timeout=1.0, # Timeout de lectura
#                         write_timeout=0.5 # Timeout de escritura
#                     )
#                     time.sleep(1.5) # Tiempo de espera para que el puerto se inicialice correctamente
#                     self.conectado = True
#                     print(f"[OK] Conectado a {p.device}")
#                     return True
#                 except Exception as e:
#                     print(f"[ERROR] Fallo al abrir puerto {p.device}: {e}")
#         print("[ERROR] No se encontró dispositivo FTDI")
#         self.conectado = False
#         return False

#     def iniciar_lectura(self):
#         """Inicia el bucle de lectura/escritura en un hilo separado."""
#         if self.ejecutando:
#             return
#         self.ejecutando = True
#         self.hilo = threading.Thread(target=self._bucle_principal, daemon=True) 
#         self.hilo.start()

#     def _bucle_principal(self):
#         """Bucle principal de comunicación que alterna entre lectura y comandos en cola."""
#         while self.ejecutando:
#             # === Lógica de Reconexión ===
#             if not self.conectado or not self.puerto or not self.puerto.is_open:
#                 self.conectado = False
#                 print("[RECONECTANDO] Buscando dispositivo FTDI...")
#                 if self.conectar():
#                     self.ultimo_ok = time.time()
#                 time.sleep(2.0)
#                 continue

#             try:
#                 # === Selección de Comando (Prioridad: Cola de Escritura) ===
#                 try:
#                     comando = self.cola_comandos.get_nowait()
#                     es_escritura = True
#                 except Empty:
#                     comando = self.siguiente_comando_lectura
#                     es_escritura = False

#                 # === Enviar Comando ===
#                 if not self._enviar_comando(comando):
#                     # Si falla el envío (p. ej., puerto no válido después de una reconexión fallida)
#                     raise serial.SerialException("Fallo al enviar comando")

#                 # === Determinar Tamaño de Respuesta ===
#                 tamaño = (
#                     TAMAÑO_RESPUESTA_ESCRITURA if es_escritura
#                     else TAMAÑO_RESPUESTA_BOOLEANOS if comando == COMANDO_LEER_BOOLEANOS
#                     else TAMAÑO_RESPUESTA_ANALOGICOS
#                 )

#                 # === Leer Respuesta ===
#                 datos = self._leer_respuesta(tamaño)
#                 if not datos:
#                     # Si _leer_respuesta devuelve None por timeout o por puerto no válido/cerrado
#                     raise TimeoutError(f"Sin respuesta, se esperaban {tamaño} bytes.")

#                 # === Validar CRC (Dos últimos bytes) ===
#                 crc_rec = (datos[-2] << 8) | datos[-1]
#                 crc_calc = crc16(datos[:-2])
#                 if crc_rec != crc_calc:
#                     raise ValueError(f"Error de CRC: Calculado {crc_calc:04X} vs Recibido {crc_rec:04X}")

#                 self.ultimo_ok = time.time()  # Comunicación confirmada

#                 payload = datos[:-2]
#                 print(f"[DEBUG] Recibido comando: {payload[:3].hex(' ')} → {len(payload)} bytes datos")
                
#                 # === Procesar Respuesta ===
#                 if es_escritura:
#                     # Una respuesta de escritura simple tiene 3 bytes de cabecera y 1 byte de confirmación (0xFF)
#                     if len(payload) >= 4 and payload[3] == 0xFF:
#                         print("[OK] Escritura confirmada")
#                     else:
#                         print(f"[ADVERTENCIA] Respuesta de escritura inesperada: {payload.hex()}")
#                 else:
#                     self._procesar_lectura(payload)

#                 # === Alternar el Siguiente Comando de Lectura ===
#                 if not es_escritura:
#                     self.siguiente_comando_lectura = (
#                         COMANDO_LEER_ANALOGICOS
#                         if comando == COMANDO_LEER_BOOLEANOS
#                         else COMANDO_LEER_BOOLEANOS
#                     )

#                 time.sleep(0.05) # Pequeña pausa entre transacciones

#             except serial.SerialException as e:
#                 # Modificación aquí: Solo terminar el bucle si 'detener' lo ha solicitado.
#                 if self.ejecutando:
#                     # Fallo del puerto (desconexión o error irrecuperable) mientras el bucle está activo.
#                     print(f"[ERROR COM] Fallo fatal del puerto ({e}). Forzando reconexión.")
#                     # Marcar como desconectado, pero NO establecer self.ejecutando = False.
#                     self.conectado = False
#                     if self.puerto:
#                         try: self.puerto.close()
#                         except: pass
#                     self.puerto = None
#                 else:
#                     # El puerto fue cerrado intencionalmente por detener(). Salir.
#                     print(f"[INFO COM] Serial cerrado intencionalmente o durante el cierre: {e}")
                
#                 # Pausa antes del siguiente ciclo, ya sea para reintentar o para salir.
#                 time.sleep(1.0) 
                
#                 # Si self.ejecutando es False, el 'while' no se repetirá.
#                 # No necesitamos el 'break' a menos que queramos salir inmediatamente de un bucle 'while True'.
#                 # Pero como el bucle es 'while self.ejecutando', el ciclo terminará por sí solo 
#                 # en la próxima iteración si self.ejecutando es False, lo cual es más limpio.
#                 # Sin embargo, dado el 'break' anterior, es más seguro mantener la lógica 
#                 # de salida explícita para el caso de cierre limpio:
#                 if not self.ejecutando:
#                     break # Salida limpia si detener() fue llamado.

#             except Exception as e:
#                 # Manejo de errores de timeout, CRC o de procesamiento, incluyendo el 'hEvent' si ocurre.
#                 if self.ejecutando:
#                     print(f"[ERROR COM] {e} → Forzando reconexión para recuperar...")
#                     self.conectado = False
#                     # Cierra y anula el puerto para forzar una reconexión limpia.
#                     if self.puerto:
#                         try: self.puerto.close()
#                         except: pass
#                     self.puerto = None
#                 else:
#                     # Si el error ocurre durante el proceso de cierre (ejecutando = False)
#                     # Esto incluye el error 'NoneType' object has no attribute 'hEvent'.
#                     print(f"[INFO COM] Error de comunicación durante el cierre: {e}")
#                     break # Rompe el bucle para asegurar que el hilo termine.
#                 time.sleep(1.0) # Espera antes de reintentar la conexión
        
#         print("[INFO] Bucle de lectura serial finalizado.")


#     def _enviar_comando(self, comando: bytes) -> bool:
#         """Calcula el CRC y envía la trama completa."""
#         if not self.puerto or not self.puerto.is_open:
#             return False
            
#         try:
#             crc = crc16(comando)
#             # El CRC se anexa en formato High-Byte | Low-Byte (Big-Endian)
#             trama = comando + bytes([crc >> 8, crc & 0xFF]) 
#             print(f"[TX] {trama.hex(' ').upper()}")
#             self.puerto.reset_input_buffer()
#             self.puerto.write(trama)
#             return True
#         except:
#             return False

#     def _leer_respuesta(self, tamaño: int) -> Optional[bytes]:
#         """Intenta leer el tamaño esperado con reintentos."""
#         # FIX: Añadir comprobación de estado para prevenir posibles errores de acceso
#         # si el puerto es cerrado o anulado por otro hilo, lo cual puede causar el error 'hEvent'.
#         if not self.puerto or not self.puerto.is_open:
#             return None
            
#         for _ in range(3):
#             # Esta es la línea que bloquea y lanza una excepción al cerrar el puerto.
#             datos = self.puerto.read(tamaño)
#             if len(datos) == tamaño:
#                 return datos
#             # Si se lee menos, espera un poco por si llega el resto
#             time.sleep(0.1) 
#         return None

#     def _procesar_lectura(self, payload: bytes):
#         """Decodifica los datos booleanos o analógicos y llama al callback."""
#         print(f"[RX] Procesando payload: {payload[:20].hex(' ').upper()}... ({len(payload)} bytes)")

#         # === BOOLEANOS: 11 11 00 + 60 bytes + CRC ===
#         # Se espera: Cabecera (3 bytes) + 60 bytes de datos = 63 bytes de payload
#         if payload.startswith(b'\x11\x11\x00') and len(payload) >= 63:
#             # Se asume que VARIABLES[0x01] contiene el mapeo de booleanos
#             if 0x01 not in VARIABLES:
#                 print("[ADVERTENCIA] No hay mapeo definido para variables booleanas (0x01).")
#                 return
            
#             # Los datos comienzan en el índice 3 del payload
#             for i in range(60):
#                 byte_val = payload[3 + i]
#                 valor = 1.0 if byte_val else 0.0 # Se convierte a float para el callback
                
#                 if i in VARIABLES[0x01]:
#                     nombre = VARIABLES[0x01][i]["name"]
#                     self.callback(nombre, valor)

#         # === ANALÓGICOS: 12 AA 00 + 71 doubles (568 bytes) + CRC ===
#         # Se espera: Cabecera (3 bytes) + (71 * 8) = 571 bytes de payload
#         elif payload.startswith(b'\x12\xAA\x00') and len(payload) >= 571:
#             if len(ANALOG_MAP) != 71:
#                 print(f"[ERROR] ANALOG_MAP debe tener 71 entradas, tiene {len(ANALOG_MAP)}")
#                 return

#             # Los datos de los doubles comienzan en el índice 3
#             for idx in range(71):
#                 grupo, addr = ANALOG_MAP[idx]
                
#                 if grupo not in VARIABLES or addr not in VARIABLES[grupo]:
#                     continue

#                 offset = 3 + idx * 8
#                 try:
#                     # Desempaqueta un double de 8 bytes, little-endian ('<d')
#                     valor = struct.unpack_from('<d', payload, offset)[0]
#                     nombre = VARIABLES[grupo][addr]["name"]
#                     self.callback(nombre, valor)
#                 except struct.error as e:
#                     print(f"[ERROR] Fallo al desempaquetar double en índice {idx} (offset {offset}): {e}")
#                     break

#     def escribir_booleano(self, addr: int, valor: bool):
#         """Genera y encola el comando de escritura para un booleano."""
#         # Formato: [0x21, 0x11, addr, valor(0x01/0x00)]
#         cmd = bytes([0x21, 0x11, addr, 0x01 if valor else 0x00])
#         self.cola_comandos.put(cmd)

#     def escribir_double(self, addr: int, valor: float):
#         """Genera y encola el comando de escritura para un double."""
#         # Formato: [0x22, 0xAA, addr] + 8 bytes de double
#         cmd = bytes([0x22, 0xAA, addr]) + struct.pack('<d', valor)
#         self.cola_comandos.put(cmd)

#     def detener(self):
#         """
#         Detiene el hilo de forma segura.
#         CRÍTICO: El puerto DEBE cerrarse ANTES de hacer join para desbloquear
#         la operación .read() en el hilo de trabajo.
#         Se añade la anulación explícita de la referencia self.puerto para mitigar
#         posibles 'Segmentation faults' en la destrucción de objetos C de pyserial.
#         """
#         self.ejecutando = False
        
#         puerto_local = self.puerto # Guardamos una referencia para el cierre

#         # 1. CERRAR EL PUERTO SERIAL (DESBLOQUEA EL HILO)
#         if puerto_local and puerto_local.is_open:
#             try:
#                 # Cierra el puerto para forzar la excepción SerialException en el hilo.
#                 puerto_local.close() 
#                 self.conectado = False
#             except Exception as e:
#                 print(f"[ERROR DETENER] Fallo al cerrar puerto: {e}")
        
#         # 2. ESPERAR A QUE EL HILO FINALICE
#         if self.hilo and self.hilo.is_alive():
#             # Espera a que el bucle termine después de la excepción forzada.
#             self.hilo.join(timeout=5.0) 
            
#         # 3. ELIMINAR REFERENCIA AL PUERTO SERIAL
#         # Esto asegura que el objeto pyserial.Serial se destruya después
#         # de que el hilo haya terminado, previniendo posibles segfaults.
#         self.puerto = None
            
#         print("[INFO] Comunicación serial detenida")


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

    def escribir_double(self, addr: int, valor: float):
        cmd = bytes([0x22, 0xAA, addr]) + struct.pack('<d', valor)
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

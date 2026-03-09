# #connection/conductivity_sensor_comm.py

# import serial 
# import serial.tools.list_ports
# import threading
# import time 
# import struct
# import crcmod
# from queue import Queue, Empty
# from typing import Optional

# from PySide6.QtCore import QObject, Signal
# from core.variables_map import VARIABLES

# READ_COMMAND  = bytes.fromhex("5641 4C41 520D")
# EXPECTED_MINIMUN_SIZE = 33

# class patternConductivity(QObject):
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

#         def connect(self) -> bool:
#             for port_info in serial.tools.list_ports.comports():
#                 if port_info.manufacturer and "Cond" in port_info.manufacturer.upper():
#                     try:
#                         self.serial_port = serial.Serial(
#                             port=port_info.device,
#                             baudrate=115200,
#                             timeout=1.0,
#                             write_timeout=0.5
#                         )
#                         time.sleep(1.5)
#                         self.isConnected = True
#                         print("[Connected Conductivity sensor] Port: {port_info.device}")
#                         return True
#                     except Exception as e:
#                         print("[ERROR] Failed to open port")
#             print("[ERROR] No sensor detected")
#             self.isConnected = False
#             return False
        
#         def start_read(self):
#             if self.running:
#                 return
#             self.running = True
#             self.reader_thread = threading.Thread(target=self._communication_loop, daemon=True)
#             self.reader_thread.start()

#         def _communication_loop(self):
#             while self.running:
#                 if not self.isConnected or not self.serial_port or not self.serial_port.is_open:
#                     self.isConnected = False
#                     if self.connect():
#                         self.last_successful_comm = time.time()
#                     time.sleep(2.0)
#                     continue
#                 try:

#                     try:
#                         command = self.command_queue.get_nowait()
#                         is_write = True
#                     except Empty:
#                         command = self.read_command
#                         is_write = False

#                     if not self._send_command(command):
#                         raise serial.SerialException("Failed to send command")
                    
#                     expected_size = (
#                         EXPECTED_MINIMUN_SIZE if is_write
#                     )


# import serial
# import time

# # Configuración del puerto
# ser = serial.Serial(
#     port='COM3', # Cambiar al puerto real de tu máquina
#     baudrate=115200,
#     bytesize=serial.EIGHTBITS,
#     parity=serial.PARITY_NONE,
#     stopbits=serial.STOPBITS_ONE,
#     timeout=0.2 # 200ms timeout
# )

# def send_command(command):
#     """Envía un comando y limpia la respuesta"""
#     full_command = command + "\r\n" # El protocolo ASCII suele requerir retorno de carro
#     ser.write(full_command.encode('ascii'))
#     response = ser.readline().decode('ascii').strip()
#     return response

# def initialize_sensor():
#     print("Inicializando sensor HDM18/19...")
    
#     # 1. Verificar presencia
#     serial_num = send_command("SYSSNR")
#     if "99" in serial_num or not serial_num:
#         raise Exception("Error: Sensor no detectado")
#     print(f"Sensor conectado. SN: {serial_num}")

#     # 2. Configurar Auto-rango para conductividad (Comando SCTARW)
#     # Argumento 1 = Enable
#     resp = send_command("SCTARW 1")
#     if "01" not in resp:
#         print("Advertencia: No se pudo activar autorango")

#     # 3. Limpiar errores previos
#     send_command("SYSERR")
    
#     print("Inicialización completa.")

# def reading_loop():
#     try:
#         while True:
#             # --- PASO 1: LEER VALORES ---
#             # VALAR devuelve todos los canales separados por "/"
#             # Eje respuesta: "13.98/36.50" (mS/cm / °C)
#             data_str = send_command("VALAR")
            
#             # --- PASO 2: LEER ESTADO (CALIDAD DEL DATO) ---
#             # VALASTR devuelve estados separados por "/"
#             # 1 = Ready/OK. Cualquier otro valor es error/warning.
#             status_str = send_command("VALASTR")

#             # --- PASO 3: PROCESAMIENTO ---
#             if "99" in data_str or "99" in status_str:
#                 print("Error de comunicación (Protocol Error)")
#                 continue

#             try:
#                 # Separar los valores (asumiendo formato Cond/Temp)
#                 values = data_str.split('/')
#                 states = status_str.split('/')

#                 if len(values) >= 2:
#                     cond_val = float(values[0])
#                     temp_val = float(values[1])
                    
#                     cond_state = states[0]
#                     temp_state = states[1]

#                     # Verificar si el dato es válido (Estado '1')
#                     if cond_state == '1' and temp_state == '1':
#                         print(f"LECTURA OK -> Cond: {cond_val} mS/cm | Temp: {temp_val} °C")
#                         # AQUÍ ENVIARÍAS LOS DATOS A LA UI DE LA MÁQUINA DE DIÁLISIS
#                     else:
#                         print(f"ALERTA: Datos inestables o error. Estado: {status_str}")
#                         # Mires la tabla de 'Measuring value states' en tu doc:
#                         # 0=Not init, 2=Overflow, 6=HW Error, etc.
                
#             except ValueError:
#                 print(f"Error parseando datos: {data_str}")

#             # Frecuencia de muestreo. 
#             # El módulo responde rápido, pero en diálisis 500ms suele ser suficiente.
#             time.sleep(0.5) 

#     except KeyboardInterrupt:
#         print("Deteniendo lectura...")
#         ser.close()

# # Ejecutar
# initialize_sensor()
# reading_loop()

import serial
import serial.tools.list_ports
import threading
import time
import re
import sys
from queue import Queue, Empty
from typing import Optional


def heitmann(Z, H, W, G, E):
    """
    Calcula el Agua Corporal Total (TBW) y su porcentaje usando la fórmula de Heitmann et al.

    Parámetros:
    Z (float): Impedancia o resistencia en Ohmios.
    H (float): Altura del paciente en cm.
    W (float): Peso del paciente en kg.
    G (int): Género del paciente (1 = hombre, 0 = mujer).
    E (int): Edad del paciente en años.

    Retorna:
    tuple[float, float] | tuple[None, None]: TBW en Litros y %TBW del peso, o (None, None) si Z es inválido.
    """
    a = 0.266
    b = 0.186
    c = 4.702
    d = 0.081
    k = 12.44

    if Z <= 0:
        return None, None

    # Fórmula de Heitmann
    TBW = (a * (H ** 2) / Z) + b * W + c * G - d * E - k
    pct = (TBW / W * 100) if W > 0 else None

    return round(TBW, 2), round(pct, 2) if pct is not None else None


class BiozTester:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self.read_thread: Optional[threading.Thread] = None

 
        self.patient = {
            "altura_cm": 170.0,
            "peso_kg": 70.0,
            "genero": 1,       # 1 = hombre, 0 = mujer
            "edad": 40
        }

  
        self.last_Z: Optional[float] = None
        self.last_phase: Optional[float] = None

 
        self.port_keywords = ["ESP32", "CP210X", "UART Bridge", "Silicon Labs"]

    def find_port(self) -> Optional[str]:
        """Busca y retorna el puerto serial de un dispositivo compatible."""
        ports = serial.tools.list_ports.comports()
        print("\nPuertos detectados:")
        if not ports:
            print("  Ningún puerto serial detectado.")
            return None
        for p in ports:
            print(f"  {p.device:8} | {p.description[:50]}")

        for p in ports:
            full = (p.description or "" + (p.manufacturer or "")).upper()
            if "FTDI" in full: 
                continue
            for kw in self.port_keywords:
                if kw.upper() in full:
                    return p.device
        return None

    def connect(self) -> bool:
        """Intenta conectar al puerto serial detectado."""
        port = self.find_port()
        if not port:
            print("No se encontró un puerto ESP32 o compatible.")
            return False

        try:
            self.serial_port = serial.Serial(port, self.baudrate, timeout=1)
            time.sleep(2.5) 
            print(f"Conectado → {port} @ {self.baudrate} baudios\n")
            return True
        except Exception as e:
            print(f"Error conectando a {port}: {e}")
            return False

    def start(self):
        """Inicia el hilo de lectura del puerto serial."""
        if self.running:
            return
        if not self.connect():
            return

        self.running = True
        self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.read_thread.start()
        print("Lectura de puerto serial iniciada. Esperando comandos...\n")

    def stop(self):
        """Detiene el hilo de lectura y cierra la conexión serial."""
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        print("Conexión serial cerrada.")

    def send(self, cmd: str):
        """Envía un comando al dispositivo serial."""
        if not self.serial_port or not self.serial_port.is_open:
            print("Sin conexión serial activa. No se puede enviar el comando.")
            return
        full_cmd = cmd.strip().upper() + "\n"
        try:
            self.serial_port.write(full_cmd.encode('ascii'))
            print(f"→ Enviado: {cmd.strip().upper()}")
        except Exception as e:
            print(f"Error enviando comando '{cmd.strip().upper()}': {e}")

    def _reader_loop(self):
        """Hilo de lectura continua del puerto serial."""
        buffer = b""
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    byte = self.serial_port.read(1)
                    if byte == b'\n': 
                        line = buffer.decode('ascii', errors='ignore').strip()
                        if line:
                            self._parse_line(line)
                        buffer = b""
                    elif byte != b'\r': 
                        buffer += byte
                time.sleep(0.015) 
            except serial.SerialException as e:
                print(f"Error crítico en el puerto serial (hilo de lectura): {e}")
                self.running = False 
                break
            except Exception as e:
                print(f"Error inesperado en el hilo de lectura: {e}")
                self.running = False
                break

    def _parse_line(self, line: str):
        """
        Analiza las líneas recibidas del dispositivo.
        Almacena el último Z y Phase, pero no calcula Heitmann automáticamente.
        """
        stripped_line = line.strip()

        
        m_detailed_bioz = re.match(r"R:\s*([\d.-]+)\s*Ohm,\s*Phase:\s*([\d.-]+)\s*Deg", stripped_line, re.I)
        if m_detailed_bioz:
            self.last_Z = float(m_detailed_bioz.group(1))
            self.last_phase = float(m_detailed_bioz.group(2))

            print("\n" + "═" * 50)
            print(f"  BIOIMPEDANCIA RECIBIDA:")
            print(f"     Z (Resistencia) = {self.last_Z:8.2f} Ω")
            print(f"     Phase           = {self.last_phase:6.2f} °")
            print("═" * 50 + "\n")
            return

        # 2. INTENTAR COINCIDIR CON EL FORMATO DE LECTURAS DE UREA (X.XXX,Y.YYY)
        m_urea_readings = re.match(r"([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)", stripped_line)
        if m_urea_readings:
            urea_val1 = float(m_urea_readings.group(1))
            urea_val2 = float(m_urea_readings.group(2))

            print("\n" + "─" * 50)
            print(f"  LECTURAS DE SENSORES DE UREA RECIBIDAS:")
            print(f"     Sensor 1        = {urea_val1:8.3f}")
            print(f"     Sensor 2        = {urea_val2:8.3f}")
            print("─" * 50 + "\n")
          
            return

 
        m_float_as_z = re.search(r"[-+]?\d*\.?\d+", stripped_line)
        if m_float_as_z:
            try:
                found_z = float(m_float_as_z.group(0))
    
                self.last_Z = found_z
                self.last_phase = 0.0 

                print("\n" + "═" * 50)
                print(f"  BIOIMPEDANCIA RECIBIDA (Solo Z numérico, fase no disponible):")
                print(f"     Z (Resistencia) = {self.last_Z:8.2f} Ω")
                print(f"     Phase           = No disponible (0.0°) ")
                if stripped_line != str(found_z):
                     print(f"     Línea original:  '{stripped_line}'")
                print("═" * 50 + "\n")
                return
            except ValueError:
                pass
        
        if stripped_line:
            print(f"  [DISPOSITIVO] {stripped_line}")




    def calculate_heitmann_with_last_Z(self):
        """
        Calcula la fórmula de Heitmann usando el último valor de Z almacenado
        y los datos actuales del paciente.
        """
        if self.last_Z is None:
            print("\n!!! No hay un valor de Z disponible para calcular Heitmann. "
                  "Por favor, envía un comando como 'SRTB' y espera a que el dispositivo "
                  "responda con un valor de Z (Resistencia) antes de intentar calcular. !!!\n")
            return

        print("\n" + "#" * 60)
        print("  CALCULANDO FÓRMULA DE HEITMANN:")
        print(f"    Z                 = {self.last_Z:8.2f} Ω")
        print(f"    Altura (H)        = {self.patient['altura_cm']:8.2f} cm")
        print(f"    Peso (W)          = {self.patient['peso_kg']:8.2f} kg")
        print(f"    Género (G)        = {self.patient['genero']:8d} (1=Hombre, 0=Mujer)")
        print(f"    Edad (E)          = {self.patient['edad']:8d} años")

        tbw, pct = heitmann(self.last_Z, self.patient["altura_cm"], self.patient["peso_kg"],
                           self.patient["genero"], self.patient["edad"])
        if tbw is not None:
            print(f"    TBW (Heitmann)    = {tbw:8.2f} L")
            print(f"    %TBW / peso       = {pct:6.2f} %")
        else:
            print("    → TBW no calculado (Z inválido o datos de paciente incorrectos).")
        print("#" * 60 + "\n")


def main():
    tester = BiozTester()

    print("=== Bioimpedancia + Calculadora Heitmann ===\n")

    
    print("ingresa los datos del paciente (presiona Enter para usar los valores por defecto):")
    try:
        h_input = input(f"  Altura (cm)     [{tester.patient['altura_cm']}]: ")
        w_input = input(f"  Peso (kg)       [{tester.patient['peso_kg']}]: ")
        g_input = input(f"  Género (1=H, 0=M)[{tester.patient['genero']}]: ")
        e_input = input(f"  Edad            [{tester.patient['edad']}]: ")

        
        tester.patient.update({
            "altura_cm": float(h_input) if h_input else tester.patient['altura_cm'],
            "peso_kg": float(w_input) if w_input else tester.patient['peso_kg'],
            "genero": int(g_input) if g_input else tester.patient['genero'],
            "edad": int(e_input) if e_input else tester.patient['edad']
        })
        print("Datos del paciente actualizados.\n")
    except ValueError:
        print("¡Error en la entrada de datos! Se usarán los valores por defecto para el paciente.\n")
    except Exception as e:
        print(f"Ocurrió un error al procesar los datos del paciente: {e}. Se usarán los valores por defecto.\n")

    tester.start() # Intentar iniciar la conexión serial

    if not tester.running:
        print("No se pudo establecer la conexión con el dispositivo. Saliendo del programa.")
        return

    print("\nComandos disponibles:")
    print("  SRTB       → Start BIA measurement (returns average)")
    print("  SRTU       → Read both ADC channels (Urea Sensors)")
    print("  CALCULATE  → Aplica la fórmula de Heitmann con el ÚLTIMO Z recibido del dispositivo.")
    print("  STOP       → Stop current measurement")
    print("  STATUS     → Pide el estado actual del dispositivo.")
    print("  q / quit   → Salir del programa.")
    print("  Cualquier otro texto → Se envía como comando directamente al dispositivo.\n")

    try:
        while tester.running:
            cmd = input("> ").strip()
            if cmd.lower() in ("q", "quit", "exit"):
                break
            elif cmd.lower() == "calculate":
                tester.calculate_heitmann_with_last_Z()
            elif cmd: # Si se ingresó cualquier otro comando, enviarlo al dispositivo
                tester.send(cmd)
    except KeyboardInterrupt:
        print("\nInterrupción por el usuario (Ctrl+C). Cerrando el programa...")
    finally:
        tester.stop() # Asegurarse de cerrar el puerto al salir
        print("\n¡Programa finalizado! ¡Hasta la próxima!\n")


if __name__ == "__main__":
    main()

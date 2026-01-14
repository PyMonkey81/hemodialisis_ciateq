# hemodialisis.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import time
#from core.alarmas import SistemaAlarmas
from core.alarmas import SistemaAlarmas
from connection.comunicacion_serial import ComunicacionSerial
from core.variables_map import VARIABLES
from tkinter import messagebox


# === IMPORTAR MÓDULOS LOCALES ===
try:
    from core.alarmas import SistemaAlarmas
    SISTEMA_ALARMAS_EXISTE = True
except ImportError as e:
    print(f"[ERROR] alarmas.py no encontrado: {e}")
    SISTEMA_ALARMAS_EXISTE = False

try:
    from connection.comunicacion_serial import ComunicacionSerial
    SERIAL_EXISTE = True
except ImportError as e:
    print(f"[ERROR] comunicacion_serial.py no encontrado: {e}")
    SERIAL_EXISTE = False

try:
    from core.variables_map import VARIABLES
    MAPA_EXISTE = True
except ImportError as e:
    print(f"[INFO] variables_map.py no encontrado. Usando valores por defecto.")
    MAPA_EXISTE = False


# === VENTANA DETALLES ===
class VentanaDetalles:
    def __init__(self, parent, sistema):
        self.sistema = sistema
        self.parent = parent

        self.window = tk.Toplevel(parent)
        self.window.title("DETALLES DE VARIABLES")
        self.window.geometry("1200x800")
        self.window.configure(bg="#f0f0f0")

        # === TABLA ===
        cols = ("#", "Grupo", "Nombre", "Tipo", "Valor", "Límites", "Unidad", "Estado", "RW")
        self.tabla = ttk.Treeview(self.window, columns=cols, show="headings", height=30)
        for col in cols:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=120, anchor="center")
        self.tabla.column("#", width=50)
        self.tabla.column("Grupo", width=80)
        self.tabla.column("Nombre", width=320)
        self.tabla.column("Valor", width=100)
        self.tabla.column("Estado", width=100)
        self.tabla.column("RW", width=60)
        self.tabla.pack(pady=10, padx=10, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        tk.Button(self.window, text="CERRAR", command=self.window.destroy,
                  bg="#d32f2f", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

        self.actualizar()

    def actualizar(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        idx = 0
        for grupo_key, vars in VARIABLES.items():
            grupo_name = f"0x{grupo_key:02X}"
            for addr, v in sorted(vars.items()):
                nombre = v["name"]
                tipo = v["type"]
                rw = "R/W" if v.get("rw", False) else "R"
                valor = self.sistema.valores[idx] if idx < len(self.sistema.valores) else 0.0
                limites = v.get("limites", (0, 100))
                unidad = v.get("unit", "")
                activa = self.sistema.ultimo_estado[idx] if idx < len(self.sistema.ultimo_estado) else False
                estado = "ACTIVA" if activa else "NORMAL"

                limites_str = f"{limites[0]}-{limites[1]}" if tipo == "double" else "-"

                self.tabla.insert("", "end", values=(
                    idx + 1, grupo_name, nombre, tipo.upper(), f"{valor:.3f}",
                    limites_str, unidad, estado, rw
                ))
                idx += 1

        self.window.after(1000, self.actualizar)


# === APP PRINCIPAL ===
class AppHemodialisis:
    def __init__(self, root):
        self.root = root
        self.root.title("HEMODIÁLISIS - MONITOR DE CONTROL")
        self.root.geometry("1600x900")
        self.root.configure(bg="#f4f4f4")

        self.leds = []
        self.labels_nombre = []

        # === CARGAR ALARMAS DESDE MAPA ===
        if SISTEMA_ALARMAS_EXISTE and MAPA_EXISTE:
            nombres, limites, tipos, niveles = self._cargar_desde_mapa()
        else:
            nombres = ["Presión Arterial", "Presión Venosa", "Flujo Sangre", "Conductividad", "Aire"]
            limites = [(50, 200), (20, 150), (200, 400), (13.5, 14.5), (0, 0)]
            tipos = ["double"] * 4 + ["bool"]
            niveles = ["rojo", "rojo", "amarillo", "amarillo", "rojo"]

        self.sistema = SistemaAlarmas(
            nombres=nombres,
            limites=limites,
            tipos=tipos,
            niveles=niveles,
            on_alarma=self.manejar_alarma,
            on_registro=self.registrar_evento
        ) if SISTEMA_ALARMAS_EXISTE else None

        # === SERIAL ===
        self.serial = None
        if SERIAL_EXISTE:
            self.serial = ComunicacionSerial(self.actualizar_desde_serial)
            if self.serial.conectar():
                self.serial.iniciar_lectura()
                print("[OK] Comunicación iniciada.")
            else:
                messagebox.showwarning("Serial", "No se encontró puerto FTDI/USB.")

        self.crear_interfaz_principal()

    def _cargar_desde_mapa(self):
        nombres, limites, tipos, niveles = [], [], [], []
        for grupo, vars in VARIABLES.items():
            for addr, v in sorted(vars.items()):
                nombres.append(v["name"])
                tipos.append("bool" if v["type"] == "bool" else "double")
                limites.append((0, 0) if v["type"] == "bool" else v.get("limites", (0, 100)))
                niveles.append(v.get("nivel", "cian"))
        return nombres, limites, tipos, niveles

    def crear_interfaz_principal(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.leds.clear()
        self.labels_nombre.clear()

        # === HEADER ===
        header = tk.Frame(self.root, bg="#f4f4f4")
        header.pack(pady=15)
        tk.Label(header, text="MONITOR DE HEMODIÁLISIS", font=("Arial", 26, "bold"), bg="#f4f4f4").pack()

        btn_frame = tk.Frame(header, bg="#f4f4f4")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="VER DETALLES", command=self.abrir_detalles,
                  bg="#1976d2", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="REINICIAR", command=self.reiniciar,
                  bg="#d32f2f", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        # === BOTONES DE CONTROL ===
        if self.serial:
            # Bomba Sangre
            tk.Button(btn_frame, text="BOMBA SANGRE ON",
                      command=lambda: self.serial.escribir_booleano(1, 0x00, True),
                      bg="#4caf50", fg="white", font=("Arial", 10)).pack(side="left", padx=3)
            tk.Button(btn_frame, text="BOMBA OFF",
                      command=lambda: self.serial.escribir_booleano(1, 0x01, True),
                      bg="#f44336", fg="white", font=("Arial", 10)).pack(side  ="left", padx=3)

            # Heparina
            tk.Button(btn_frame, text="HEPARINA ON",
                      command=lambda: self.serial.escribir_booleano(1, 0x06, True),
                      bg="#2196f3", fg="white", font=("Arial", 10)).pack(side="left", padx=3)
            tk.Button(btn_frame, text="HEPARINA OFF",
                      command=lambda: self.serial.escribir_booleano(1, 0x07, True),
                      bg="#d32f2f", fg="white", font=("Arial", 10)).pack(side="left", padx=3)

            # Iniciar / Parar
            tk.Button(btn_frame, text="INICIAR DIÁLISIS",
                      command=lambda: self.serial.escribir_booleano(1, 0x27, True),
                      bg="#8bc34a", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)
            tk.Button(btn_frame, text="PARAR DIÁLISIS",
                      command=lambda: self.serial.escribir_booleano(1, 0x28, True),
                      bg="#f44336", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)

            # Setpoint Flujo
            tk.Button(btn_frame, text="FLUJO 300",
                      command=lambda: self.serial.escribir_double(4, 0x00, 300.0),
                      bg="#ff9800", fg="white", font=("Arial", 10)).pack(side="left", padx=3)

        # === GRID DE LEDS (8 COLUMNAS) ===
        grid = tk.Frame(self.root, bg="#f4f4f4")
        grid.pack(pady=20)
        cols = 8

        for i in range(self.sistema.num_alarmas):
            frame = tk.Frame(grid, bg="white", relief="raised", bd=2, width=180, height=100)
            frame.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="n")
            frame.pack_propagate(False)

            # LED
            canvas = tk.Canvas(frame, width=50, height=50, bg="white", highlightthickness=0)
            canvas.pack(pady=10)
            led = canvas.create_oval(10, 10, 40, 40, fill="#888", outline="#666")
            self.leds.append(canvas)

            # NOMBRE
            nombre = self.sistema.nombres[i]
            label = tk.Label(frame, text=nombre, font=("Arial", 9, "bold"), bg="white", wraplength=160, justify="center")
            label.pack()
            self.labels_nombre.append(label)

        for i in range(cols):
            grid.grid_columnconfigure(i, weight=1)

    def abrir_detalles(self):
        if self.sistema:
            VentanaDetalles(self.root, self.sistema)

    def manejar_alarma(self, idx, activa, valor, nombre, nivel, limites):
        self.root.after(0, lambda: self.actualizar_led(idx, activa))

    def actualizar_led(self, idx, activa):
        if idx >= len(self.leds): return
        canvas = self.leds[idx]
        led = canvas.find_all()[0]
        color = "#d32f2f" if activa else "#4caf50"
        canvas.itemconfig(led, fill=color, outline=color)

    def registrar_evento(self, evento, valor, hora):
        print(f"[{hora}] {evento} | Valor: {valor}")

    def actualizar_desde_serial(self, nombre, valor):
        if not self.sistema: return
        try:
            idx = self.sistema.nombres.index(nombre)
            self.sistema.actualizar_valor(idx, valor)
        except ValueError:
            pass

    def reiniciar(self):
        if self.sistema:
            self.sistema.reset()
        self.crear_interfaz_principal()

    def cerrar(self):
        if self.serial:
            self.serial.detener()
        if self.sistema:
            self.sistema.detener()
        self.root.destroy()


# === INICIAR ===
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AppHemodialisis(root)
        root.protocol("WM_DELETE_WINDOW", app.cerrar)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("ERROR CRÍTICO", f"{e}")
        print(f"ERROR: {e}")
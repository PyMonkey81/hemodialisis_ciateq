# alarmas.py
import threading
import time
import json
import os
from typing import List, Tuple, Callable

class SistemaAlarmas:
    def __init__(self, nombres, limites, niveles, on_alarma=None, on_registro=None, tipos=None, trigger_booleano=None):
        self.nombres = nombres
        self.limites = limites
        self.niveles = niveles
        self.on_alarma = on_alarma or (lambda *args: None)
        self.on_registro = on_registro or (lambda *args: None)

        # === TIPOS Y TRIGGER ===
        self.tipos = tipos or ["numerico"] * len(nombres)
        self.trigger_booleano = trigger_booleano or [True] * len(nombres)

        self.num_alarmas = len(nombres)
        self.valores = [0.0] * self.num_alarmas
        self.ultimo_estado = [False] * self.num_alarmas
        self.historial = []
        self.lock = threading.Lock()
        self.hilo = None
        self.corriendo = False

        self._ajustar_tamanos()
        self.iniciar_monitoreo()

    def _ajustar_tamanos(self):
        n = len(self.nombres)
        self.tipos += ["numerico"] * (n - len(self.tipos))
        self.trigger_booleano += [True] * (n - len(self.trigger_booleano))
        self.limites += [(0, 100)] * (n - len(self.limites))
        self.niveles += ["rojo"] * (n - len(self.niveles))

    def actualizar_valor(self, idx: int, valor: float):
        if 0 <= idx < self.num_alarmas:
            with self.lock:
                self.valores[idx] = valor

    def _monitoreo(self):
        while self.corriendo:
            with self.lock:
                valores = self.valores.copy()
            for i in range(self.num_alarmas):
                valor = valores[i]
                if self.tipos[i] == "numerico":
                    minv, maxv = self.limites[i]
                    fuera = valor < minv or valor > maxv
                else:
                    fuera = (valor != 0) == self.trigger_booleano[i]

                if fuera != self.ultimo_estado[i]:
                    self.ultimo_estado[i] = fuera
                    hora = time.strftime("%H:%M:%S")
                    evento = f"{'ACTIVADA' if fuera else 'DESACTIVADA'} - {self.nombres[i]}"
                    self.historial.append((evento, valor, hora))

                    # === SOLUCIÓN: Usa queue para GUI ===
                    if self.on_registro:
                        self.on_registro(evento, valor, hora)
                    if self.on_alarma:
                        self.on_alarma(i, fuera, valor, self.nombres[i], self.niveles[i], self.limites[i])
            time.sleep(0.5)

    def iniciar_monitoreo(self):
        if not self.corriendo:
            self.corriendo = True
            self.ultimo_estado = [False] * self.num_alarmas
            self.hilo = threading.Thread(target=self._monitoreo, daemon=True)
            self.hilo.start()

    def detener(self):
        self.corriendo = False
        if self.hilo and self.hilo.is_alive():
            self.hilo.join(timeout=1)

    def reset(self):
        with self.lock:
            self.valores = [0.0] * self.num_alarmas
            self.ultimo_estado = [False] * self.num_alarmas
            self.historial.clear()

    def configurar(self, nombres=None, limites=None, niveles=None, tipos=None, trigger_booleano=None):
        with self.lock:
            if nombres is not None: self.nombres = nombres
            if limites is not None: self.limites = limites
            if niveles is not None: self.niveles = niveles
            if tipos is not None: self.tipos = tipos
            if trigger_booleano is not None: self.trigger_booleano = trigger_booleano
            self._ajustar_tamanos()
            self.num_alarmas = len(self.nombres)
            self.valores = [0.0] * self.num_alarmas
            self.ultimo_estado = [False] * self.num_alarmas
            self.guardar_config()

    def guardar_config(self):
        config = {
            "nombres": self.nombres,
            "limites": self.limites,
            "niveles": self.niveles,
            "tipos": self.tipos,
            "trigger_booleano": self.trigger_booleano
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def cargar_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.configurar(**config)
            except Exception as e:
                print(f"Error cargando config: {e}")

    def obtener_historial(self):
        with self.lock:
            return self.historial.copy()
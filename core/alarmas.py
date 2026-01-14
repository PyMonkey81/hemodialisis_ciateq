# core/alarmas.py
import threading
import time
import json
import os
from typing import List, Tuple, Callable, Optional, Any

# 1. IMPORTAMOS LIBRERÍA DE QT
from PySide6.QtCore import QObject, Signal 

# 2. HEREDAMOS DE QObject
class SistemaAlarmas(QObject):
    """
    Sistema de monitoreo de alarmas numéricas y booleanas con soporte multi-hilo.

    Detecta cambios de estado y notifica mediante callbacks (ideal para GUI).

    Args:
        mnombre (list[str]):nombres para mostrar 
        tags (List[str]): tags de las alarmas. (logica)
        limites (List[Tuple[float, float]], optional): Límites (mín, máx) para alarmas numéricas.
        niveles (List[str], optional): Nivel de severidad ("rojo", "amarillo", etc.).
        on_alarma (Callable, optional): Se llama al activar/desactivar una alarma.
        on_registro (Callable, optional): Se llama al registrar un evento en el historial.
        tipos (List[str], optional): "numerico" o "booleano".
        trigger_booleano (List[bool], optional): Para booleanas:
            True  → activa cuando valor ≠ 0
            False → activa cuando valor == 0
    """
    # 3. DEFINIMOS LA SEÑAL (idx, activada, valor, nombre, nivel, limite)
    # 'object' se usa para el limite porque es una tupla (min, max)
    cambio_alarma = Signal(int, bool, float, str, str, object)
    
    # Señal para el historial (evento, valor, hora)
    nuevo_evento = Signal(str, float, str)

    def __init__(
        self,
        nombres: list[str],
        tags: List[str],        
        limites: Optional[List[Tuple[float, float]]] = None,
        niveles: Optional[List[str]] = None,
        
        tipos: Optional[List[str]] = None,
        trigger_booleano: Optional[List[bool]] = None,
    ):
        super().__init__() # Init de QObject

        if not tags or not nombres:
            raise ValueError("La lista de tags y nombres no puede estar vacía") 
        
        if len(tags) != len(nombres):
            raise ValueError("El número de tags y nombres no coincide")

        self.tags = tags
        self.nombres = nombres
        self.num_alarmas = len(tags)

        self.limites = self._completar_lista(limites, (0.0, 100.0), self.num_alarmas)
        self.niveles = self._completar_lista(niveles, "rojo", self.num_alarmas)
        self.tipos = self._completar_lista(tipos, "numerico", self.num_alarmas)
        self.trigger_booleano = self._completar_lista(trigger_booleano, True, self.num_alarmas)

        self.valores = [0.0] * self.num_alarmas
        self.ultimo_estado = [False] * self.num_alarmas
        self.historial: List[Tuple[str, float, str]] = []
        self.bloqueo = threading.Lock()
        self.hilo: Optional[threading.Thread] = None
        self.ejecutando = False

        self.iniciar_monitoreo()

    @staticmethod
    def _completar_lista(lista, valor_defecto, tamaño):
        if lista is None: return [valor_defecto] * tamaño
        if len(lista) >= tamaño: return lista[:tamaño]
        return lista + [valor_defecto] * (tamaño - len(lista))

    def actualizar_valor(self, idx: int, valor: float) -> None:
        if 0 <= idx < self.num_alarmas:
            with self.bloqueo:
                self.valores[idx] = valor

    def _monitoreo(self) -> None:
        while self.ejecutando:
            with self.bloqueo:
                valores_actuales = self.valores.copy()

            for i in range(self.num_alarmas):
                valor = valores_actuales[i]
                tipo = self.tipos[i]
                
                # Lógica de detección
                if tipo == "numerico":
                    minv, maxv = self.limites[i]
                    activada = valor < minv or valor > maxv
                else: 
                    condicion = (valor != 0)
                    activada = condicion if self.trigger_booleano[i] else not condicion

                if activada != self.ultimo_estado[i]:
                    self.ultimo_estado[i] = activada
                    hora = time.strftime("%H:%M:%S")
                    estado_texto = "ACTIVADA" if activada else "DESACTIVADA"
                    evento = f"{estado_texto} - {self.nombres[i]}"
                    
                    self.historial.append((evento, valor, hora))

                    # 4. EMITIMOS SEÑALES EN LUGAR DE LLAMAR FUNCIONES
                    self.nuevo_evento.emit(evento, valor, hora)
                    
                    self.cambio_alarma.emit(
                        i, activada, valor,
                        self.nombres[i], self.niveles[i], self.limites[i]
                    )

            time.sleep(0.5)

    def iniciar_monitoreo(self) -> None:
        if not self.ejecutando:
            self.ejecutando = True
            self.ultimo_estado = [False] * self.num_alarmas
            self.hilo = threading.Thread(target=self._monitoreo, daemon=True)
            self.hilo.start()

    def detener(self) -> None:
        self.ejecutando = False
        if self.hilo and self.hilo.is_alive():
            self.hilo.join(timeout=2.0)
        self.hilo = None
        print("[INFO] Sistema de alarmas detenido.")

    def reset(self) -> None:
        """Reinicia todos los valores y el historial (mantiene configuración)."""
        with self.bloqueo:
            self.valores = [0.0] * self.num_alarmas
            self.ultimo_estado = [False] * self.num_alarmas
            self.historial.clear()

    def configurar(self, tags=None,nombres=None, limites=None, niveles=None, tipos=None, trigger_booleano=None):
        with self.bloqueo:
            if tags and nombres: 
                if len(tags) != len(nombres):
                    print("[ERROR] Tags y Nombres deben coincidir en longitud al configurar.")
                    return
                self.tags = tags
                self.nombres = nombres
                self.num_alarmas = len(tags)

            self.limites = self._completar_lista(limites, (0.0, 100.0), self.num_alarmas)
            self.niveles = self._completar_lista(niveles, "rojo", self.num_alarmas)
            self.tipos = self._completar_lista(tipos, "numerico", self.num_alarmas)
            self.trigger_booleano = self._completar_lista(trigger_booleano, True, self.num_alarmas)
            self.valores = [0.0] * self.num_alarmas
            self.ultimo_estado = [False] * self.num_alarmas
            self.guardar_config()
            

    def guardar_config(self):
        # Guardamos también los nombres
        config = {
            "tags": self.tags, 
            "nombres": self.nombres,
            "limites": self.limites, 
            "niveles": self.niveles, 
            "tipos": self.tipos, 
            "trigger_booleano": self.trigger_booleano
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f: json.dump(config, f, indent=2)
        except: pass

    def cargar_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f: 
                    self.configurar(**json.load(f))
            except: pass

    def obtener_historial(self):
        with self.bloqueo: return self.historial.copy()

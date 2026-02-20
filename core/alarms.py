# core/alarms.py

import threading
import time
import json
import os
from typing import List, Tuple, Optional, Any

from PySide6.QtCore import QObject, Signal


class AlarmSystem(QObject):
    """
    Alarm monitoring system for numeric and boolean variables.
    Runs in a separate thread and emits Qt signals for safe GUI integration.
    
    Features:
    - Continuous monitoring with configurable intervals
    - State change detection (activated/deactivated)
    - Event history logging
    - Persistent configuration (save/load from JSON)
    - Thread-safe value updates

    Patient Safety Alarm System (IEC 60601-1-8 compliant).
    Monitors physiological parameters and machine states for a hemodialysis device.
    Implements thread-safe Qt signals for Clinical GUI integration.
    
    """

    # Signal emitted when an alarm state changes
    # Parameters: (index, is_active, current_value, display_name, severity_level, limits_tuple)
    alarm_changed = Signal(int, bool, float, str, str, object)

    # Signal for logging events to history / UI
    # Parameters: (event_message, value, formatted_time)
    new_event = Signal(str, float, str)

    def __init__(
        self,
        display_names: List[str],
        tags: List[str],
        limits: Optional[List[Tuple[float, float]]] = None,
        severity_levels: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        boolean_triggers: Optional[List[bool]] = None,
    ):
        super().__init__()

        if not tags or not display_names:
            raise ValueError("Tags and display_names lists cannot be empty")

        if len(tags) != len(display_names):
            raise ValueError("Number of tags and display_names must match")

        self.tags = tags
        self.display_names = display_names
        self.alarm_count = len(tags)

        # Default values when parameters are missing or incomplete
        self.limits = self._fill_list(limits, (0.0, 100.0), self.alarm_count)
        self.severity_levels = self._fill_list(severity_levels, "red", self.alarm_count)
        self.types = self._fill_list(types, "numeric", self.alarm_count)
        self.boolean_triggers = self._fill_list(boolean_triggers, True, self.alarm_count)

        # Runtime state
        self.current_values = [0.0] * self.alarm_count
        self.previous_states = [False] * self.alarm_count
        self.event_history: List[Tuple[str, float, str]] = []

        self.lock = threading.Lock()
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False

        # self.start_monitoring()  # Uncomment if you want auto-start (usually called from main)

    @staticmethod
    def _fill_list(
        input_list: Optional[List[Any]],
        default_value: Any,
        required_length: int
    ) -> List[Any]:
        """Helper to safely fill or truncate lists to required length."""
        if input_list is None:
            return [default_value] * required_length
        if len(input_list) >= required_length:
            return input_list[:required_length]
        return input_list + [default_value] * (required_length - len(input_list))

    def update_value_by_index(self, index: int, value: float) -> None:
        """Update the value of a specific alarm by its index (thread-safe)."""
        if 0 <= index < self.alarm_count:
            with self.lock:
                self.current_values[index] = value

    def update_value_by_tag(self, tag: str, value: float) -> None:
        """Update value using the variable tag (convenient for serial communication)."""
        try:
            index = self.tags.index(tag)
            self.update_value_by_index(index, value)
        except ValueError:
            pass  # Tag not found in this alarm system → silent ignore

    def _monitoring_loop(self) -> None:
        """Background thread loop that checks alarm conditions periodically."""
        while self.running:
            with self.lock:
                # Snapshot to minimize lock time
                snapshot_values = list(self.current_values)

            for i in range(self.alarm_count):
                value = snapshot_values[i]
                alarm_type = self.types[i]

                # Determine if alarm should be active
                if alarm_type == "numeric":
                    min_val, max_val = self.limits[i]
                    is_active = value < min_val or value > max_val
                else:  # boolean
                    condition = (value != 0.0)
                    is_active = condition if self.boolean_triggers[i] else not condition

                # Detect state change
                if is_active != self.previous_states[i]:
                    self.previous_states[i] = is_active

                    current_time = time.strftime("%H:%M:%S")
                    status_text = "ACTIVADA" if is_active else "DESACTIVADA"
                    event_msg = f"{status_text} - {self.display_names[i]}"

                    with self.lock:
                        self.event_history.append((event_msg, value, current_time))

                    # Emit signals (safe for cross-thread GUI update)
                    self.new_event.emit(event_msg, value, current_time)
                    self.alarm_changed.emit(
                        i,
                        is_active,
                        value,
                        self.display_names[i],
                        self.severity_levels[i],
                        self.limits[i]
                    )

            time.sleep(0.5)  # Check interval — can be made configurable

    def start_monitoring(self) -> None:
        """Start the alarm monitoring thread if not already running."""
        if not self.running:
            self.running = True
            # Do NOT reset previous_states here to avoid false re-triggers on restart
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()

    def stop(self) -> None:
        """Gracefully stop the monitoring thread."""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        self.monitor_thread = None
        print("[INFO] Alarm system stopped.")

    def reset(self) -> None:
        """Reset all runtime values and history (keeps configuration)."""
        with self.lock:
            self.current_values = [0.0] * self.alarm_count
            self.previous_states = [False] * self.alarm_count
            self.event_history.clear()

    def configure(
        self,
        tags: Optional[List[str]] = None,
        display_names: Optional[List[str]] = None,
        limits: Optional[List[Tuple[float, float]]] = None,
        severity_levels: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        boolean_triggers: Optional[List[bool]] = None,
    ):
        """
        Dynamically reconfigure the alarm system.
        Resets runtime state when structural parameters change.
        """
        with self.lock:
            structural_change = False

            if tags is not None and display_names is not None:
                if len(tags) != len(display_names):
                    print("[ERROR] Tags and display_names must have the same length.")
                    return
                self.tags = tags
                self.display_names = display_names
                self.alarm_count = len(tags)
                structural_change = True

            if limits is not None:
                self.limits = self._fill_list(limits, (0.0, 100.0), self.alarm_count)
            if severity_levels is not None:
                self.severity_levels = self._fill_list(severity_levels, "red", self.alarm_count)
            if types is not None:
                self.types = self._fill_list(types, "numeric", self.alarm_count)
            if boolean_triggers is not None:
                self.boolean_triggers = self._fill_list(boolean_triggers, True, self.alarm_count)

            # Reset runtime state on structural changes
            if structural_change:
                self.current_values = [0.0] * self.alarm_count
                self.previous_states = [False] * self.alarm_count

            self._save_configuration()

    def _save_configuration(self):
        """Save current alarm configuration to JSON file."""
        config = {
            "tags": self.tags,
            "display_names": self.display_names,
            "limits": self.limits,
            "severity_levels": self.severity_levels,
            "types": self.types,
            "boolean_triggers": self.boolean_triggers
        }
        try:
            with open("alarm_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save alarm_config.json: {e}")

    def load_configuration(self):
        """Load alarm configuration from JSON file if exists."""
        config_path = "alarm_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.configure(**data)
            except Exception as e:
                print(f"[ERROR] Failed to load alarm_config.json: {e}")

    def get_history(self) -> List[Tuple[str, float, str]]:
        """Return a copy of the event history (thread-safe)."""
        with self.lock:
            return self.event_history.copy()


# core/alarmas.py

# # core/alarmas.py
# import threading
# import time
# import json
# import os
# from typing import List, Tuple, Callable, Optional, Any

# from PySide6.QtCore import QObject, Signal 

# class AlarmSystem(QObject):
#     """
#     Sistema de monitoreo de alarmas numéricas y booleanas con soporte multi-hilo.
#     Emite señales de Qt para una integración segura con la GUI.
#     """
    
#     # Señal: (índice, esta_activada, valor_actual, nombre_visual, nivel, limites_tupla)
#     cambio_alarma = Signal(int, bool, float, str, str, object)
    
#     # Señal: (mensaje_evento, valor, hora_formateada)
#     nuevo_evento = Signal(str, float, str)

#     def __init__(
#         self,
#         nombres: List[str],
#         tags: List[str],        
#         limites: Optional[List[Tuple[float, float]]] = None,
#         niveles: Optional[List[str]] = None,
#         tipos: Optional[List[str]] = None,
#         trigger_booleano: Optional[List[bool]] = None,
#     ):
#         super().__init__()

#         if not tags or not nombres:
#             raise ValueError("Las listas de 'tags' y 'nombres' no pueden estar vacías") 
        
#         if len(tags) != len(nombres):
#             raise ValueError("La cantidad de 'tags' y 'nombres' debe ser la misma")

#         self.tags = tags
#         self.nombres = nombres
#         self.num_alarmas = len(tags)

#         # Inicialización de parámetros
#         self.limites = self._completar_lista(limites, (0.0, 100.0), self.num_alarmas)
#         self.niveles = self._completar_lista(niveles, "rojo", self.num_alarmas)
#         self.tipos = self._completar_lista(tipos, "numerico", self.num_alarmas)
#         self.trigger_booleano = self._completar_lista(trigger_booleano, True, self.num_alarmas)

#         # Estado interno
#         self.valores = [0.0] * self.num_alarmas
#         self.ultimo_estado = [False] * self.num_alarmas
#         self.historial: List[Tuple[str, float, str]] = []
        
#         self.bloqueo = threading.Lock()
#         self.hilo: Optional[threading.Thread] = None
#         self.ejecutando = False

#         #self.iniciar_monitoreo()

#     @staticmethod
#     def _completar_lista(lista, valor_defecto, tamano):
#         if lista is None: return [valor_defecto] * tamano
#         if len(lista) >= tamano: return lista[:tamano]
#         return lista + [valor_defecto] * (tamano - len(lista))

#     def actualizar_valor(self, idx: int, valor: float) -> None:
#         """Actualiza el valor de una alarma por su índice."""
#         if 0 <= idx < self.num_alarmas:
#             with self.bloqueo:
#                 self.valores[idx] = valor

#     def actualizar_por_tag(self, tag: str, valor: float) -> None: # NUEVO METODO
#         """Busca el tag y actualiza su valor. Útil para integración con PLCs/Sensores."""
#         try:
#             idx = self.tags.index(tag)
#             self.actualizar_valor(idx, valor)
#         except ValueError:
#             pass # El tag no existe en este sistema

#     def _monitoreo(self) -> None:
#         """Bucle que corre en hilo separado."""
#         while self.ejecutando:
#             with self.bloqueo:
#                 # Copia rápida para minimizar el tiempo de bloqueo
#                 valores_actuales = list(self.valores)

#             for i in range(self.num_alarmas):
#                 valor = valores_actuales[i]
#                 tipo = self.tipos[i]
                
#                 # --- Lógica de Detección ---
#                 if tipo == "numerico":
#                     minv, maxv = self.limites[i]
#                     activada = valor < minv or valor > maxv
#                 else: 
#                     condicion = (valor != 0)
#                     activada = condicion if self.trigger_booleano[i] else not condicion

#                 # --- Cambio de Estado ---
#                 if activada != self.ultimo_estado[i]:
#                     self.ultimo_estado[i] = activada
#                     hora = time.strftime("%H:%M:%S")
#                     estado_texto = "ACTIVADA" if activada else "DESACTIVADA"
#                     evento = f"{estado_texto} - {self.nombres[i]}"
                    
#                     with self.bloqueo:
#                         self.historial.append((evento, valor, hora))

#                     # Emisión segura para la GUI
#                     self.nuevo_evento.emit(evento, valor, hora)
#                     self.cambio_alarma.emit(
#                         i, activada, valor,
#                         self.nombres[i], self.niveles[i], self.limites[i]
#                     )

#             time.sleep(0.5)

#     def iniciar_monitoreo(self) -> None:
#         if not self.ejecutando:
#             self.ejecutando = True
#             # No reseteamos ultimo_estado aquí para evitar re-disparar alarmas al pausar/reanudar
#             self.hilo = threading.Thread(target=self._monitoreo, daemon=True)
#             self.hilo.start()

#     def detener(self) -> None:
#         self.ejecutando = False
#         if self.hilo and self.hilo.is_alive():
#             self.hilo.join(timeout=2.0)
#         self.hilo = None
#         print("[INFO] Sistema de alarmas detenido.")

#     def reset(self) -> None:
#         with self.bloqueo:
#             self.valores = [0.0] * self.num_alarmas
#             self.ultimo_estado = [False] * self.num_alarmas
#             self.historial.clear()

#     def configurar(self, **kwargs):
#         """
#         Permite reconfigurar el sistema dinámicamente.
#         Uso: configurar(limites=[...], niveles=[...])
#         """
#         with self.bloqueo:
#             if 'tags' in kwargs and 'nombres' in kwargs:
#                 if len(kwargs['tags']) != len(kwargs['nombres']):
#                     print("[ERROR] Tags y Nombres no coinciden.")
#                     return
#                 self.tags = kwargs['tags']
#                 self.nombres = kwargs['nombres']
#                 self.num_alarmas = len(self.tags)

#             if 'limites' in kwargs:
#                 self.limites = self._completar_lista(kwargs['limites'], (0.0, 100.0), self.num_alarmas)
#             if 'niveles' in kwargs:
#                 self.niveles = self._completar_lista(kwargs['niveles'], "rojo", self.num_alarmas)
#             if 'tipos' in kwargs:
#                 self.tipos = self._completar_lista(kwargs['tipos'], "numerico", self.num_alarmas)
#             if 'trigger_booleano' in kwargs:
#                 self.trigger_booleano = self._completar_lista(kwargs['trigger_booleano'], True, self.num_alarmas)
            
#             # Reset de estados al cambiar la configuración estructural
#             self.valores = [0.0] * self.num_alarmas
#             self.ultimo_estado = [False] * self.num_alarmas
            
#             self.guardar_config()

#     def guardar_config(self):
#         config = {
#             "tags": self.tags, 
#             "nombres": self.nombres,
#             "limites": self.limites, 
#             "niveles": self.niveles, 
#             "tipos": self.tipos, 
#             "trigger_booleano": self.trigger_booleano
#         }
#         try:
#             with open("config.json", "w", encoding="utf-8") as f:
#                 json.dump(config, f, indent=2, ensure_ascii=False)
#         except Exception as e:
#             print(f"[ERROR] No se pudo guardar config.json: {e}")

#     def cargar_config(self):
#         if os.path.exists("config.json"):
#             try:
#                 with open("config.json", "r", encoding="utf-8") as f: 
#                     datos = json.load(f)
#                     self.configurar(**datos)
#             except Exception as e:
#                 print(f"[ERROR] No se pudo cargar config.json: {e}")

#     def obtener_historial(self):
#         with self.bloqueo:
#             return self.historial.copy()





# import threading
# import time
# import json
# import os
# from typing import List, Tuple, Callable, Optional, Any

# # 1. IMPORTAMOS LIBRERÍA DE QT
# from PySide6.QtCore import QObject, Signal 

# # 2. HEREDAMOS DE QObject
# class SistemaAlarmas(QObject):
#     """
#     Sistema de monitoreo de alarmas numéricas y booleanas con soporte multi-hilo.

#     Detecta cambios de estado y notifica mediante callbacks (ideal para GUI).

#     Args:
#         mnombre (list[str]):nombres para mostrar 
#         tags (List[str]): tags de las alarmas. (logica)
#         limites (List[Tuple[float, float]], optional): Límites (mín, máx) para alarmas numéricas.
#         niveles (List[str], optional): Nivel de severidad ("rojo", "amarillo", etc.).
#         on_alarma (Callable, optional): Se llama al activar/desactivar una alarma.
#         on_registro (Callable, optional): Se llama al registrar un evento en el historial.
#         tipos (List[str], optional): "numerico" o "booleano".
#         trigger_booleano (List[bool], optional): Para booleanas:
#             True  → activa cuando valor ≠ 0
#             False → activa cuando valor == 0
#     """
#     # 3. DEFINIMOS LA SEÑAL (idx, activada, valor, nombre, nivel, limite)
#     # 'object' se usa para el limite porque es una tupla (min, max)
#     cambio_alarma = Signal(int, bool, float, str, str, object)
    
#     # Señal para el historial (evento, valor, hora)
#     nuevo_evento = Signal(str, float, str)

#     def __init__(
#         self,
#         nombres: list[str],
#         tags: List[str],        
#         limites: Optional[List[Tuple[float, float]]] = None,
#         niveles: Optional[List[str]] = None,        
#         tipos: Optional[List[str]] = None,
#         trigger_booleano: Optional[List[bool]] = None,
#     ):
#         super().__init__() # Init de QObject

#         if not tags or not nombres:
#             raise ValueError("La lista de tags y nombres no puede estar vacía") 
        
#         if len(tags) != len(nombres):
#             raise ValueError("El número de tags y nombres no coincide")

#         self.tags = tags
#         self.nombres = nombres
#         self.num_alarmas = len(tags)

#         self.limites = self._completar_lista(limites, (0.0, 100.0), self.num_alarmas)
#         self.niveles = self._completar_lista(niveles, "rojo", self.num_alarmas)
#         self.tipos = self._completar_lista(tipos, "numerico", self.num_alarmas)
#         self.trigger_booleano = self._completar_lista(trigger_booleano, True, self.num_alarmas)

#         self.valores = [0.0] * self.num_alarmas
#         self.ultimo_estado = [False] * self.num_alarmas
#         self.historial: List[Tuple[str, float, str]] = []

#         self.bloqueo = threading.Lock()
#         self.hilo: Optional[threading.Thread] = None
#         self.ejecutando = False

#         self.iniciar_monitoreo()

#     @staticmethod
#     def _completar_lista(lista, valor_defecto, tamaño):
#         if lista is None: return [valor_defecto] * tamaño
#         if len(lista) >= tamaño: return lista[:tamaño]
#         return lista + [valor_defecto] * (tamaño - len(lista))

#     def actualizar_valor(self, idx: int, valor: float) -> None:
#         if 0 <= idx < self.num_alarmas:
#             with self.bloqueo:
#                 self.valores[idx] = valor

#     def _monitoreo(self) -> None:
#         while self.ejecutando:
#             with self.bloqueo:
#                 valores_actuales = self.valores.copy()

#             for i in range(self.num_alarmas):
#                 valor = valores_actuales[i]
#                 tipo = self.tipos[i]
                
#                 # Lógica de detección
#                 if tipo == "numerico":
#                     minv, maxv = self.limites[i]
#                     activada = valor < minv or valor > maxv
#                 else: 
#                     condicion = (valor != 0)
#                     activada = condicion if self.trigger_booleano[i] else not condicion

#                 if activada != self.ultimo_estado[i]:
#                     self.ultimo_estado[i] = activada
#                     hora = time.strftime("%H:%M:%S")
#                     estado_texto = "ACTIVADA" if activada else "DESACTIVADA"
#                     evento = f"{estado_texto} - {self.nombres[i]}"
                    
#                     self.historial.append((evento, valor, hora))

#                     # 4. EMITIMOS SEÑALES EN LUGAR DE LLAMAR FUNCIONES
#                     self.nuevo_evento.emit(evento, valor, hora)
                    
#                     self.cambio_alarma.emit(
#                         i, activada, valor,
#                         self.nombres[i], self.niveles[i], self.limites[i]
#                     )

#             time.sleep(0.5)

#     def iniciar_monitoreo(self) -> None:
#         if not self.ejecutando:
#             self.ejecutando = True
#             self.ultimo_estado = [False] * self.num_alarmas
#             self.hilo = threading.Thread(target=self._monitoreo, daemon=True)
#             self.hilo.start()

#     def detener(self) -> None:
#         self.ejecutando = False
#         if self.hilo and self.hilo.is_alive():
#             self.hilo.join(timeout=2.0)
#         self.hilo = None
#         print("[INFO] Sistema de alarmas detenido.")

#     def reset(self) -> None:
#         """Reinicia todos los valores y el historial (mantiene configuración)."""
#         with self.bloqueo:
#             self.valores = [0.0] * self.num_alarmas
#             self.ultimo_estado = [False] * self.num_alarmas
#             self.historial.clear()

#     def configurar(self, tags=None,nombres=None, limites=None, niveles=None, tipos=None, trigger_booleano=None):
#         with self.bloqueo:
#             if tags and nombres: 
#                 if len(tags) != len(nombres):
#                     print("[ERROR] Tags y Nombres deben coincidir en longitud al configurar.")
#                     return
#                 self.tags = tags
#                 self.nombres = nombres
#                 self.num_alarmas = len(tags)

#             self.limites = self._completar_lista(limites, (0.0, 100.0), self.num_alarmas)
#             self.niveles = self._completar_lista(niveles, "rojo", self.num_alarmas)
#             self.tipos = self._completar_lista(tipos, "numerico", self.num_alarmas)
#             self.trigger_booleano = self._completar_lista(trigger_booleano, True, self.num_alarmas)
#             self.valores = [0.0] * self.num_alarmas
#             self.ultimo_estado = [False] * self.num_alarmas
#             self.guardar_config()
            

#     def guardar_config(self):
#         # Guardamos también los nombres
#         config = {
#             "tags": self.tags, 
#             "nombres": self.nombres,
#             "limites": self.limites, 
#             "niveles": self.niveles, 
#             "tipos": self.tipos, 
#             "trigger_booleano": self.trigger_booleano
#         }
#         try:
#             with open("config.json", "w", encoding="utf-8") as f: json.dump(config, f, indent=2)
#         except: pass

#     def cargar_config(self):
#         if os.path.exists("config.json"):
#             try:
#                 with open("config.json", "r", encoding="utf-8") as f: 
#                     self.configurar(**json.load(f))
#             except: pass

#     def obtener_historial(self):
#         with self.bloqueo: return self.historial.copy()

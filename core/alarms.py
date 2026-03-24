# core/alarms.py

import threading
import time
import json
import os
from typing import List, Tuple, Optional, Any

from PySide6.QtCore import QObject, Signal


class AlarmSystem(QObject):
    """
    Sistema de Monitorización y Gestión de Alarmas para Dispositivos Médicos.

    Este módulo define la clase `AlarmSystem`, un componente crítico diseñado
    para supervisar continuamente diversas variables (numéricas y booleanas)
    de un dispositivo médico, como una máquina de hemodiálisis. Opera en un
    hilo separado para garantizar un monitoreo ininterrumpido sin bloquear
    la interfaz de usuario y utiliza señales de Qt para una integración segura
    con la GUI.

    Cumple con los principios de seguridad y fiabilidad requeridos por normativas
    como IEC 60601-1-8 (sistemas de alarma en equipamiento médico), asegurando
    la detección de condiciones críticas y la notificación oportuna.

    Características principales:
    -------------------------
    - **Monitoreo en Hilo Separado**: Ejecuta un bucle de monitoreo en un hilo
      dedicado para verificar el estado de las alarmas periódicamente, sin
      interferir con el ciclo principal de la aplicación o la interfaz gráfica.
    - **Detección de Cambios de Estado**: Identifica cuándo una alarma pasa de
      inactiva a activa y viceversa, emitiendo señales solo cuando hay un cambio
      relevante.
    - **Gestión de Variables Diversas**: Soporta la monitorización de variables
      numéricas (con límites min/max) y booleanas (activadas por True/False).
    - **Niveles de Severidad Configurable**: Cada alarma puede tener un nivel de
      severidad asociado (ej. "rojo", "naranja", "cian") para priorizar y
      diferenciar la retroalimentación al usuario.
    - **Integración con `AlarmLimitsManager`**: Permite obtener los límites de
      alarma de una instancia de `AlarmLimitsManager`, facilitando la
      persistencia y la configuración dinámica de los umbrales.
    - **Registro de Eventos**: Mantiene un historial interno de todas las
      activaciones y normalizaciones de alarmas, y lo notifica a través de una señal.
    - **Comunicación Segura con GUI (Qt Signals)**: Emite señales de Qt
      (`alarm_changed`, `new_event`) para que la interfaz gráfica pueda
      actualizarse de forma segura desde el hilo principal, sin problemas de
      thread-safety.
    - **Actualización de Valores Thread-Safe**: Proporciona métodos protegidos
      por un `threading.Lock` para actualizar los valores de las variables
      monitoreadas desde otros hilos.

    Señales:
    --------
    alarm_changed (int, bool, float, str, str, object): Emitida cuando el estado
        de una alarma cambia (se activa o se normaliza).
        - `index` (int): Índice de la alarma en la lista de configuración.
        - `is_active` (bool): `True` si la alarma está ahora activa, `False` si se ha normalizado.
        - `value` (float): El valor actual de la variable que ha disparado/normalizado la alarma.
        - `name` (str): El nombre legible de la alarma.
        - `level` (str): El nivel de severidad de la alarma (ej. "rojo", "naranja", "cian").
        - `limits` (tuple): Una tupla `(min_val, max_val)` con los límites actuales de la alarma.

    new_event (str, float, str): Emitida para cualquier evento significativo
        del sistema de alarmas (ej. activación, normalización, reconocimiento).
        - `message` (str): Una descripción textual del evento.
        - `value` (float): Un valor numérico asociado al evento (si aplica, `None` si no).
        - `timestamp` (str): Una marca de tiempo del momento en que ocurrió el evento (formato HH:MM:SS).

    Args:
    -----
        display_names (List[str]): Lista de nombres legibles para cada alarma/variable.
                                   Debe coincidir en longitud con `tags`.
        tags (List[str]): Lista de identificadores únicos (tags) para cada alarma/variable,
                          usados para identificar los datos que vienen del controlador.
                          Debe coincidir en longitud con `display_names`.
        limits (Optional[List[Tuple[float, float]]], optional): Lista de tuplas `(min_val, max_val)`
                                                                 definiendo los límites para alarmas numéricas.
                                                                 Si `limits_manager` está presente, estos son ignorados.
                                                                 Por defecto: `(0.0, 100.0)` para todos.
        severity_levels (Optional[List[str]], optional): Lista de cadenas que indican el nivel de
                                                         severidad (ej. "rojo", "naranja", "amarillo", "cian").
                                                         Debe coincidir en longitud con `tags`. Por defecto: "red".
        types (Optional[List[str]], optional): Lista de cadenas indicando el tipo de alarma ("numeric" o "boolean").
                                               Debe coincidir en longitud con `tags`. Por defecto: "numeric".
        boolean_triggers (Optional[List[bool]], optional): Lista de booleanos para alarmas de tipo "boolean".
                                                            Si `True`, `value != 0.0` activa la alarma.
                                                            Si `False`, `value == 0.0` activa la alarma.
                                                            Debe coincidir en longitud con `tags`. Por defecto: `True`.
        limits_manager (Optional[Any], optional): Una instancia de `AlarmLimitsManager` (u objeto compatible)
                                                  que proporciona el método `get_limits(tag)`. Si se proporciona,
                                                  los límites se obtendrán dinámicamente de aquí. Por defecto: `None`.

    Atributos:
    ----------
        current_values (List[float]): Almacena el último valor conocido para cada variable monitoreada.
        previous_states (List[bool]): Almacena el estado de alarma previo (`True` si estaba activa, `False` si no).
        event_history (List[Tuple[str, float, str]]): Un registro de todos los eventos de alarma detectados.
        lock (threading.Lock): Un objeto de bloqueo utilizado para asegurar el acceso thread-safe a los datos internos.
        monitor_thread (Optional[threading.Thread]): Referencia al hilo de monitoreo en ejecución.
        running (bool): Bandera que indica si el hilo de monitoreo debe continuar ejecutándose.

    Uso:
    ----
    1.  **Inicialización**: Crear una instancia de `AlarmSystem` con la configuración
        de alarmas deseada. Es recomendable usar un `AlarmLimitsManager` para
        gestionar los límites persistentes.
    2.  **Iniciar Monitoreo**: Llamar a `start_monitoring()` para iniciar el hilo
        de monitoreo.
    3.  **Actualizar Valores**: Periodicamente, o cada vez que se reciba un nuevo dato,
        llamar a `update_value_by_tag(tag, value)` o `update_value_by_index(index, value)`
        para alimentar al sistema con los valores más recientes.
    4.  **Conectar Señales**: Conectar las señales `alarm_changed` y `new_event` a slots
        en la GUI para reaccionar a los eventos de alarma.
    5.  **Detener Monitoreo**: Al cerrar la aplicación, llamar a `stop()` para finalizar
        el hilo de monitoreo de forma segura.
    """

    alarm_changed = Signal(int, bool, float, str, str, object)

    new_event = Signal(str, float, str)

    def __init__(
        self,
        display_names: List[str],
        tags: List[str],
        limits: Optional[List[Tuple[float, float]]] = None,
        severity_levels: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        boolean_triggers: Optional[List[bool]] = None,
        limits_manager = None,
    ):
        super().__init__()

        if not tags or not display_names:
            raise ValueError("Tags and display_names lists cannot be empty")

        if len(tags) != len(display_names):
            raise ValueError("Number of tags and display_names must match")

        self.tags = tags
        self.display_names = display_names
        self.alarm_count = len(tags)
        self.limits_manager = limits_manager

        # Inicializar límites: priorizar manager si existe
        if limits_manager is None:
            self.limits = limits or [(0.0, 100.0)] * len(tags)
        else:
            self.limits = [limits_manager.get_limits(tag) for tag in tags]

        # Default values when parameters are missing or incomplete
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
                tag = self.tags[i]
                alarm_type = self.types[i]

                # Obtener límites actuales (prioridad: manager > estático)
                if self.limits_manager:
                    min_val, max_val = self.limits_manager.get_limits(tag)
                else:
                    min_val, max_val = self.limits[i]

                # Determine if alarm should be active
                if alarm_type == "numeric":
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
                        (min_val, max_val)  # Enviamos los límites actuales
                    )

            time.sleep(0.5)  # Check interval — can be made configurable

    def start_monitoring(self) -> None:
        """Start the alarm monitoring thread if not already running."""
        if not self.running:
            self.running = True
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


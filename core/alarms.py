# core/alarm_system.py

#==================================================================================================
#=================TRADUCCION DE CODIGO A INGLES, HACE LO MISMO SOLO ESTA CON NOMEMCLATURA EN INGLES
#===================================================================================================

# LA TRADUCCIÓN LA HIZO GEMINI, HAY QUE REVISAR Y COMPARAR CON LA VERSION EN ESPAÑOL 


import threading
import time
import json
import os
from typing import List, Tuple, Callable, Optional, Any

from PySide6.QtCore import QObject, Signal 

class DialysisAlarmSystem(QObject):
    """
    Patient Safety Alarm System (IEC 60601-1-8 compliant).
    Monitors physiological parameters and machine states for a hemodialysis device.
    Implements thread-safe Qt signals for Clinical GUI integration.
    """
    
    # Signal: (index, is_active, current_reading, parameter_name, priority, alarm_limits)
    # Changed from generic 'cambio_alarma' to specific 'alarm_condition_changed'
    alarm_condition_changed = Signal(int, bool, float, str, str, object)
    
    # Signal: (clinical_log_message, reading, timestamp)
    # Changed from 'nuevo_evento' to 'clinical_event_logged' (audit trail)
    clinical_event_logged = Signal(str, float, str)

    def __init__(
        self,
        parameter_names: List[str],      # e.g., "Venous Pressure", "Conductivity"
        sensor_tags: List[str],          # e.g., "VP_SENS", "COND_CELL"
        alarm_limits: Optional[List[Tuple[float, float]]] = None, # (Low Limit, High Limit)
        priorities: Optional[List[str]] = None,    # "High", "Medium", "Low"
        data_types: Optional[List[str]] = None,    # "numeric", "boolean"
        boolean_triggers: Optional[List[bool]] = None,
    ):
        super().__init__()

        if not sensor_tags or not parameter_names:
            raise ValueError("'sensor_tags' and 'parameter_names' cannot be empty") 
        
        if len(sensor_tags) != len(parameter_names):
            raise ValueError("The count of 'sensor_tags' and 'parameter_names' must match")

        self.sensor_tags = sensor_tags
        self.parameter_names = parameter_names
        self.alarm_count = len(sensor_tags)

        # Parameter Initialization (Padding with safe defaults)
        # We ensure lists are equal length to prevent runtime errors during treatment
        self.alarm_limits = self._ensure_list_size(alarm_limits, (0.0, 100.0), self.alarm_count)
        self.priorities = self._ensure_list_size(priorities, "High", self.alarm_count)
        self.data_types = self._ensure_list_size(data_types, "numeric", self.alarm_count)
        self.boolean_triggers = self._ensure_list_size(boolean_triggers, True, self.alarm_count)

        # Internal Patient/Machine State
        self.current_readings = [0.0] * self.alarm_count
        self.active_conditions = [False] * self.alarm_count
        self.audit_trail: List[Tuple[str, float, str]] = []
        
        # Concurrency control
        self._mutex = threading.Lock()
        self._surveillance_thread: Optional[threading.Thread] = None
        self._is_monitoring = False

        # self.start_surveillance()

    @staticmethod
    def _ensure_list_size(input_list, default_val, target_size):
        """Helper to ensure configuration lists match the sensor count."""
        if input_list is None: return [default_val] * target_size
        if len(input_list) >= target_size: return input_list[:target_size]
        return input_list + [default_val] * (target_size - len(input_list))

    def update_reading(self, idx: int, value: float) -> None:
        """Updates a sensor reading by its internal index."""
        if 0 <= idx < self.alarm_count:
            with self._mutex:
                self.current_readings[idx] = value

    def update_by_tag(self, tag: str, value: float) -> None: 
        """
        Locates the sensor tag and updates its clinical value. 
        Links hardware abstraction layer (HAL) to alarm logic.
        """
        try:
            idx = self.sensor_tags.index(tag)
            self.update_reading(idx, value)
        except ValueError:
            pass # Tag not monitored by this system (safe ignore)

    def _surveillance_loop(self) -> None:
        """
        Continuous background surveillance loop.
        Checks vital signs against safety limits.
        """
        while self._is_monitoring:
            with self._mutex:
                # Snapshot of current patient data to minimize lock duration
                snapshot_readings = list(self.current_readings)

            for i in range(self.alarm_count):
                reading = snapshot_readings[i]
                d_type = self.data_types[i]
                
                # --- Clinical Logic Evaluation ---
                if d_type == "numeric":
                    lower_limit, upper_limit = self.alarm_limits[i]
                    # Alarm condition exists if reading is outside the therapeutic/safety window
                    is_condition_present = reading < lower_limit or reading > upper_limit
                else: 
                    # Logic for binary sensors (e.g., Blood Leak Detector, Air Bubble)
                    state = (reading != 0)
                    is_condition_present = state if self.boolean_triggers[i] else not state

                # --- State Transition ---
                if is_condition_present != self.active_conditions[i]:
                    self.active_conditions[i] = is_condition_present
                    timestamp = time.strftime("%H:%M:%S")
                    
                    # Medical Terminology: "Onset" (Inicio de alarma) vs "Resolved" (Resuelta)
                    status_text = "ALARM ONSET" if is_condition_present else "RESOLVED"
                    log_entry = f"[{self.priorities[i]}] {status_text} - {self.parameter_names[i]}"
                    
                    with self._mutex:
                        self.audit_trail.append((log_entry, reading, timestamp))

                    # Thread-safe emission to Clinical GUI
                    self.clinical_event_logged.emit(log_entry, reading, timestamp)
                    self.alarm_condition_changed.emit(
                        i, is_condition_present, reading,
                        self.parameter_names[i], self.priorities[i], self.alarm_limits[i]
                    )

            time.sleep(0.5) # Safety poll interval (adjust per risk analysis)

    def start_surveillance(self) -> None:
        if not self._is_monitoring:
            self._is_monitoring = True
            # We don't reset active_conditions here to preserve state across temporary pauses
            self._surveillance_thread = threading.Thread(target=self._surveillance_loop, daemon=True)
            self._surveillance_thread.start()

    def stop_surveillance(self) -> None:
        self._is_monitoring = False
        if self._surveillance_thread and self._surveillance_thread.is_alive():
            self._surveillance_thread.join(timeout=2.0)
        self._surveillance_thread = None
        print("[INFO] Patient monitoring halted.")

    def reset_session(self) -> None:
        """Clears data for a new treatment session (between patients)."""
        with self._mutex:
            self.current_readings = [0.0] * self.alarm_count
            self.active_conditions = [False] * self.alarm_count
            self.audit_trail.clear()

    def reconfigure_treatment(self, **kwargs):
        """
        Dynamically adjusts treatment parameters (e.g., Nurse changing limits).
        Usage: reconfigure_treatment(alarm_limits=[...], priorities=[...])
        """
        with self._mutex:
            if 'sensor_tags' in kwargs and 'parameter_names' in kwargs:
                if len(kwargs['sensor_tags']) != len(kwargs['parameter_names']):
                    print("[ERROR] Tags and Parameter Names mismatch.")
                    return
                self.sensor_tags = kwargs['sensor_tags']
                self.parameter_names = kwargs['parameter_names']
                self.alarm_count = len(self.sensor_tags)

            if 'alarm_limits' in kwargs:
                self.alarm_limits = self._ensure_list_size(kwargs['alarm_limits'], (0.0, 100.0), self.alarm_count)
            if 'priorities' in kwargs:
                self.priorities = self._ensure_list_size(kwargs['priorities'], "High", self.alarm_count)
            if 'data_types' in kwargs:
                self.data_types = self._ensure_list_size(kwargs['data_types'], "numeric", self.alarm_count)
            if 'boolean_triggers' in kwargs:
                self.boolean_triggers = self._ensure_list_size(kwargs['boolean_triggers'], True, self.alarm_count)
            
            # Reset logic states when structural config changes to prevent false positives
            self.current_readings = [0.0] * self.alarm_count
            self.active_conditions = [False] * self.alarm_count
            
            self.save_treatment_preset()

    def save_treatment_preset(self):
        config = {
            "sensor_tags": self.sensor_tags, 
            "parameter_names": self.parameter_names,
            "alarm_limits": self.alarm_limits, 
            "priorities": self.priorities, 
            "data_types": self.data_types, 
            "boolean_triggers": self.boolean_triggers
        }
        try:
            with open("treatment_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Could not save treatment preset: {e}")

    def load_treatment_preset(self):
        if os.path.exists("treatment_config.json"):
            try:
                with open("treatment_config.json", "r", encoding="utf-8") as f: 
                    data = json.load(f)
                    self.reconfigure_treatment(**data)
            except Exception as e:
                print(f"[ERROR] Could not load treatment preset: {e}")

    def get_audit_trail(self):
        """Returns a copy of the event log for audit purposes."""
        with self._mutex:
            return self.audit_trail.copy()

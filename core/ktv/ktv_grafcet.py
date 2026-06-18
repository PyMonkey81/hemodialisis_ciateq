"""Modelo GRAFCET de la secuencia de medición de Kt/V."""

import logging
from enum import Enum, auto
from typing import Callable, Optional, Dict

from PySide6.QtCore import QObject, QTimer

logger = logging.getLogger(__name__)


class KtvStep(Enum):
    IDLE = auto()
    START_BIOIMPEDANCE = auto()
    WAIT_BIOIMPEDANCE = auto()
    START_UREA = auto()
    WAIT_UREA = auto()
    CAPTURE_T1 = auto()
    SET_STEP_CONDUCTIVITY = auto()
    WAIT_CONDUCTIVITY_STEP = auto()
    CAPTURE_T2 = auto()
    RESTORE_CONDUCTIVITY = auto()
    WAIT_RESTORE = auto()
    CALCULATE_RESULT = auto()
    FINISHED = auto()
    ERROR = auto()
    PAUSED_SEQUENCE = auto() # Nuevo estado para la pausa


class KtvGrafcet(QObject):
    """GRAFCET para la medición de Kt/V desde la pantalla de diálisis."""

    def __init__(self, callbacks: Dict[str, Callable], parent=None): # Usar Dict para los callbacks
        super().__init__(parent)
        self.step = KtvStep.IDLE
        self.callbacks = callbacks # Estos callbacks ahora serán métodos del KtvController
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timer_timeout)

        # Variables para la pausa/reanudación de la secuencia
        self._paused_step: Optional[KtvStep] = None
        self._remaining_wait_time_ms: int = 0
        self._next_step_after_wait: Optional[KtvStep] = None # Almacenar el siguiente paso después de un wait

        self.is_auto_trigger: bool = False # Para saber si la medición fue automática o manual
        logger.info("KtvGrafcet inicializado.")

    def start(self) -> None:
        """Arranca la secuencia de medición Kt/V."""
        if self.step not in (KtvStep.IDLE, KtvStep.FINISHED, KtvStep.ERROR):
            logger.warning(f"[Kt/V GRAFCET] Intento de iniciar secuencia desde estado {self.step.name}. Abortando.")
            self.abort("Inicio inválido") # Evitar iniciar si ya está en curso
            return
        
        logger.info("[Kt/V GRAFCET] Inicio de secuencia")
        self._clear_pause_state() # Asegurarse de que no haya estado de pausa previo
        self._transition_to(KtvStep.START_BIOIMPEDANCE)

    def abort(self, reason: str = "Abortado por usuario") -> None:
        """Aborta la secuencia de medición Kt/V."""
        logger.warning(f"[Kt/V GRAFCET] Abortando secuencia: {reason} desde {self.step.name}")
        self.timer.stop()
        self._clear_pause_state() # Limpiar cualquier estado de pausa
        # Si ya estábamos en ERROR, no transicionar de nuevo para evitar loops de log
        if self.step != KtvStep.ERROR:
            self._transition_to(KtvStep.ERROR) # Ir directamente al estado de error
        else:
            self._execute_current_step() # Ejecutar el handler de error si ya estábamos ahí

    def reset(self) -> None:
        """Restablece el GRAFCET a su estado inicial IDLE."""
        logger.info("[Kt/V GRAFCET] Reseteando secuencia a IDLE.")
        self.timer.stop()
        self._clear_pause_state()
        self.step = KtvStep.IDLE
        self.is_auto_trigger = False

    def is_running(self) -> bool:
        """Indica si la secuencia está activa (incluye estado pausado interno)."""
        return self.step not in (KtvStep.IDLE, KtvStep.FINISHED, KtvStep.ERROR)

    def pause_sequence(self) -> None:
        """Pausa la ejecución de la secuencia del GRAFCET."""
        if self.step in [KtvStep.IDLE, KtvStep.FINISHED, KtvStep.ERROR, KtvStep.PAUSED_SEQUENCE]:
            logger.debug(f"[Kt/V GRAFCET] No se puede pausar en el estado {self.step.name}.")
            return

        logger.info(f"[Kt/V GRAFCET] Pausando secuencia desde {self.step.name}.")
        self._paused_step = self.step # Guardar el paso actual
        
        if self.timer.isActive():
            self._remaining_wait_time_ms = self.timer.remainingTime()
            self.timer.stop()
            logger.debug(f"[Kt/V GRAFCET] Timer detenido. Tiempo restante: {self._remaining_wait_time_ms} ms.")

        self._transition_to(KtvStep.PAUSED_SEQUENCE)
        # El KtvController será el encargado de mostrar el mensaje al usuario
        # self._call_callback("show_info", "Medición Kt/V pausada.", 2000)

    def resume_sequence(self) -> None:
        """Reanuda la ejecución de la secuencia del GRAFCET."""
        if self.step != KtvStep.PAUSED_SEQUENCE:
            logger.warning(f"[Kt/V GRAFCET] Intento de reanudar secuencia desde un estado no pausado: {self.step.name}.")
            return

        logger.info(f"[Kt/V GRAFCET] Reanudando secuencia a {self._paused_step.name}.")
        restored_step = self._paused_step
        self._clear_pause_state() # Limpiar estado de pausa

        if self._remaining_wait_time_ms > 0:
            self.timer.start(self._remaining_wait_time_ms)
            logger.debug(f"[Kt/V GRAFCET] Timer reiniciado con {self._remaining_wait_time_ms} ms restantes.")
            # No ejecutar _execute_current_step aún, el timer lo hará al dispararse
            self.step = restored_step # Simplemente restauramos el paso para que el _on_timer_timeout sepa a dónde ir
        else:
            # Si el paso pausado no era un wait (ej. capturar valores, enviar comandos), ejecutarlo de nuevo
            self._transition_to(restored_step)
        
        # El KtvController será el encargado de mostrar el mensaje al usuario
        # self._call_callback("show_info", "Medición Kt/V reanudada.", 2000)

    def _clear_pause_state(self) -> None:
        """Limpia las variables de estado de pausa."""
        self._paused_step = None
        self._remaining_wait_time_ms = 0

    def _transition_to(self, next_step: KtvStep) -> None:
        """Cambia el estado actual del GRAFCET y ejecuta el paso."""
        if self.step == KtvStep.PAUSED_SEQUENCE and next_step != KtvStep.PAUSED_SEQUENCE:
            # Si estamos en PAUSED_SEQUENCE y se intenta transicionar a otro,
            # esto indica un error de lógica o un intento de reanudar sin usar resume_sequence.
            # Excepto si la transición es a ERROR, que siempre es posible.
            if next_step != KtvStep.ERROR:
                logger.error(f"[Kt/V GRAFCET] Transición inválida desde PAUSED_SEQUENCE a {next_step.name}.")
                self.abort("Transición inválida desde pausa.")
                return

        logger.info(f"[Kt/V GRAFCET] Transición: {self.step.name} → {next_step.name}")
        self.step = next_step
        if self.step != KtvStep.PAUSED_SEQUENCE: # No ejecutar si el nuevo estado es PAUSED_SEQUENCE
            self._execute_current_step()

    def _execute_current_step(self) -> None:
        """Ejecuta la acción asociada al estado actual del GRAFCET."""
        if self.step == KtvStep.IDLE:
            return # No hay acción en IDLE
        elif self.step == KtvStep.START_BIOIMPEDANCE:
            self._start_bioimpedance()
        elif self.step == KtvStep.WAIT_BIOIMPEDANCE:
            self._wait(5000, KtvStep.START_UREA)
        elif self.step == KtvStep.START_UREA:
            self._start_urea()
        elif self.step == KtvStep.WAIT_UREA:
            self._wait(2000, KtvStep.CAPTURE_T1)
        elif self.step == KtvStep.CAPTURE_T1:
            self._capture_t1()
        elif self.step == KtvStep.SET_STEP_CONDUCTIVITY:
            self._set_step_conductivity()
        elif self.step == KtvStep.WAIT_CONDUCTIVITY_STEP:
            self._wait(120000, KtvStep.CAPTURE_T2) # 2 minutos
        elif self.step == KtvStep.CAPTURE_T2:
            self._capture_t2()
        elif self.step == KtvStep.RESTORE_CONDUCTIVITY:
            self._restore_conductivity()
        elif self.step == KtvStep.WAIT_RESTORE:
            self._wait(120000, KtvStep.CALCULATE_RESULT) # 2 minutos
        elif self.step == KtvStep.CALCULATE_RESULT:
            self._calculate_result()
        elif self.step == KtvStep.FINISHED:
            self._finish()
        elif self.step == KtvStep.ERROR:
            self._handle_error()
        elif self.step == KtvStep.PAUSED_SEQUENCE:
            # En este estado, no hay ejecución, solo espera ser reanudado.
            pass


    def _start_bioimpedance(self) -> None:
        """Envía comando de Bioimpedancia y muestra mensaje."""
        self._call_callback("send_bioz_command", "SRTB")
        self._call_callback("show_info", "Iniciando medición de Bioimpedancia...", 2000)
        self._transition_to(KtvStep.WAIT_BIOIMPEDANCE)

    def _start_urea(self) -> None:
        """Envía comando de Urea."""
        self._call_callback("send_bioz_command", "SRTU")
        self._transition_to(KtvStep.WAIT_UREA)

    def _capture_t1(self) -> None:
        """Captura los valores iniciales de conductividad y guarda el setpoint original."""
        self._call_callback("capture_t1")
        self._transition_to(KtvStep.SET_STEP_CONDUCTIVITY)

    def _set_step_conductivity(self) -> None:
        """Cambia el setpoint de conductividad para el paso."""
        self._call_callback("set_step_conductivity")
        self._call_callback("show_info", "Ajustando conductividad. Espere...", 2000)
        self._transition_to(KtvStep.WAIT_CONDUCTIVITY_STEP)

    def _capture_t2(self) -> None:
        """Captura los valores de conductividad después del paso."""
        self._call_callback("capture_t2")
        self._transition_to(KtvStep.RESTORE_CONDUCTIVITY)

    def _restore_conductivity(self) -> None:
        """Restaura el setpoint de conductividad original."""
        self._call_callback("restore_conductivity")
        self._call_callback("show_info", "Restaurando conductividad original. Espere...", 2000)
        self._transition_to(KtvStep.WAIT_RESTORE)

    def _calculate_result(self) -> None:
        """Realiza el cálculo final de Kt/V."""
        self._call_callback("calculate_ktv")
        self._transition_to(KtvStep.FINISHED)

    def _finish(self) -> None:
        """Maneja la finalización exitosa de la secuencia."""
        self._call_callback("on_finish")
        logger.info("[Kt/V GRAFCET] Secuencia finalizada con éxito.")
        self.step = KtvStep.IDLE # Volver a IDLE al finalizar

    def _handle_error(self) -> None:
        """Maneja un error en la secuencia."""
        self._call_callback("on_error")
        logger.error("[Kt/V GRAFCET] Secuencia finalizada con error.")
        self.step = KtvStep.IDLE # Volver a IDLE después de un error

    def _wait(self, duration_ms: int, next_step: KtvStep) -> None:
        """Inicia un temporizador para esperar antes de pasar al siguiente paso."""
        self._next_step_after_wait = next_step
        self.timer.start(duration_ms)
        logger.debug(f"[Kt/V GRAFCET] Esperando {duration_ms} ms para {next_step.name}")

    def _on_timer_timeout(self) -> None:
        """Callback del temporizador: Transiciona al siguiente paso después de la espera."""
        if self.step == KtvStep.PAUSED_SEQUENCE:
            # Si el timer se dispara mientras está pausado, ignorarlo.
            # Esto puede ocurrir si se pausó justo después de iniciar el timer.
            logger.warning("[Kt/V GRAFCET] Timer timeout ignorado, secuencia en estado PAUSED_SEQUENCE.")
            return
        self._transition_to(self._next_step_after_wait)

    def _call_callback(self, name: str, *args) -> None:
        """Intenta llamar un callback definido, manejando errores."""
        callback = self.callbacks.get(name)
        if not callable(callback):
            logger.error(f"[Kt/V GRAFCET] Callback no definido o no invocable: '{name}'. Abortando secuencia.")
            self.abort(f"Callback '{name}' no disponible.")
            return
        try:
            callback(*args)
        except Exception as exc:
            logger.error(f"[Kt/V GRAFCET] Error en la ejecución del callback '{name}': {exc}", exc_info=True)
            self.abort(f"Error en callback '{name}': {exc}")

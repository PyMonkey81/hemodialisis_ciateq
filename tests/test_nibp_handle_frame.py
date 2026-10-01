"""Tests para la lógica de _handle_frame en NibpParCommunication."""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from connection.nibp_protocol import checksum_hex, parse_frame
from connection.nibp_par_communication import NibpParCommunication


@pytest.fixture
def nibp_comm():
    """Crea una instancia de NibpParCommunication con señales mockeadas."""
    # Mock QObject y Signal
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        # Mock las señales para capturar emisiones
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        comm.cuff_pressure = Mock()
        comm.raw_frame_received = Mock()
        comm.connected_changed = Mock()
        return comm


def build_status_frame(status_digit, error_code, sys, dia, map_val, hr, use_spo2_delim=False):
    """Construye una trama de status para pruebas."""
    if error_code:
        sys_str = "---------"
        hr_str = "---"
        message_code = str(error_code).zfill(2)  # Ensure 2-digit format
    else:
        sys_str = f"{sys:03d}{dia:03d}{map_val:03d}"
        hr_str = f"{hr:03d}"
        message_code = "00"
    
    body = f"S{status_digit};A0;C00;M{message_code};P{sys_str};R{hr_str};T    ;;".encode()
    content = body + checksum_hex(body).encode("ascii")
    
    if use_spo2_delim:
        frame = b"\xFD" + content + b"\xFE\x0D"
    else:
        frame = b"\x02" + content + b"\x03\x0D"
    return frame


def test_measurement_ready_emitted_on_valid_status_without_error():
    """Trama de status sin error_code y con valores válidos DEBE emitir measurement_ready."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame: sin error, valores válidos
        frame = build_status_frame(status_digit=1, error_code=None, sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # measurement_ready DEBE ser emitido
        comm.measurement_ready.emit.assert_called_once_with(120, 80, 90, 70)
        # error_message NO debe ser emitido
        comm.error_message.emit.assert_not_called()


def test_measurement_ready_not_emitted_on_status_with_error_code():
    """Trama de status con error_code M15 NO DEBE emitir measurement_ready."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Frame: con error M15 (sys/dia/map/hr son valores de toma anterior)
        frame = build_status_frame(status_digit=2, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # measurement_ready NO debe ser emitido
        comm.measurement_ready.emit.assert_not_called()
        # error_message SÍ debe ser emitido
        comm.error_message.emit.assert_called_once()
        call_args = comm.error_message.emit.call_args
        assert call_args[0][0] == "M15"
        assert "error de sistema" in call_args[0][1].lower()


def test_measurement_ready_not_emitted_on_status_with_missing_values():
    """Trama de status sin error_code pero con valores ausentes (-1) NO emite measurement_ready."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame: sin error_code pero con valores ausentes (guiones)
        body = b"S1;A0;C00;M00;P---------;R---;T    ;;"
        content = body + checksum_hex(body).encode("ascii")
        frame = b"\x02" + content + b"\x03\x0D"
        
        comm._handle_frame(frame)
        
        # measurement_ready NO debe ser emitido (valores inválidos)
        comm.measurement_ready.emit.assert_not_called()
        # error_message NO debe ser emitido (no hay error_code)
        comm.error_message.emit.assert_not_called()


def test_error_message_emitted_with_correct_error_code():
    """error_message debe emitir el código de error correcto."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Frame: error M07 (fuga de manguito)
        frame = build_status_frame(status_digit=1, error_code="07", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame)
        
        # error_message debe ser emitido con el código correcto
        comm.error_message.emit.assert_called_once()
        call_args = comm.error_message.emit.call_args
        assert call_args[0][0] == "M07"


def test_m15_counter_increments_on_repeated_error():
    """El contador de M15 debe incrementar en errores repetidos."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Primer error M15
        frame1 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame1)
        assert comm._m15_consecutive_count == 1
        
        # Segundo error M15
        frame2 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame2)
        assert comm._m15_consecutive_count == 2
        
        # Tercer error M15
        frame3 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame3)
        assert comm._m15_consecutive_count == 3


def test_m15_counter_resets_on_successful_measurement():
    """El contador de M15 debe resetearse en una medición exitosa."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Primero, simular 2 errores M15
        frame_error1 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_error1)
        frame_error2 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_error2)
        assert comm._m15_consecutive_count == 2
        
        # Luego, una medición exitosa
        frame_ok = build_status_frame(status_digit=1, error_code=None, sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_ok)
        
        # El contador debe resetearse a 0
        assert comm._m15_consecutive_count == 0
        comm.measurement_ready.emit.assert_called_once()


def test_spo2_delimiters_work_correctly():
    """Las tramas con delimitadores SpO2 (0xFD/0xFE) deben funcionar igual."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame con delimitadores SpO2
        frame = build_status_frame(
            status_digit=1, error_code=None, sys=101, dia=65, map_val=76, hr=60,
            use_spo2_delim=True
        )
        comm._handle_frame(frame)
        
        # measurement_ready debe ser emitido
        comm.measurement_ready.emit.assert_called_once_with(101, 65, 76, 60)


def test_error_code_02_and_03_no_recovery():
    """Error codes 02 y 03 no deben disparar recuperación (reset)."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm._enqueue_command = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Error M02 (comando inválido, reset automático)
        frame = build_status_frame(status_digit=1, error_code="02", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame)
        
        # _handle_measurement_error no debe encolar reset para M02/M03
        # (se verifica que no se encole comando)
        comm._enqueue_command.assert_not_called()


def test_status_error_m15_with_previous_measurements_no_measurement_ready():
    """Status con error M15 y P/R numéricos de toma previa → NO measurement_ready, SÍ error M15.
    
    Este es el bug específico: cuando hay error, los P/R pueden tener valores numéricos
    de la última toma buena, pero NO deben ser interpretados como una nueva medición.
    """
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Frame: error M15, pero con P/R numéricos de toma anterior
        # Esto es lo que el módulo manda: valores viejos en una trama de error
        frame = build_status_frame(status_digit=2, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # measurement_ready NO debe ser emitido (hay error_code)
        comm.measurement_ready.emit.assert_not_called()
        
        # error_message SÍ debe ser emitido con M15
        comm.error_message.emit.assert_called_once()
        call_args = comm.error_message.emit.call_args
        assert call_args[0][0] == "M15"
        assert "error de sistema" in call_args[0][1].lower() or "falla" in call_args[0][1].lower()


def test_status_without_error_valid_measurements_emits_measurement_ready():
    """Status sin error, checksum ok, P y R válidos → SÍ measurement_ready."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame: sin error, valores válidos
        frame = build_status_frame(status_digit=1, error_code=None, sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # measurement_ready SÍ debe ser emitido
        comm.measurement_ready.emit.assert_called_once_with(120, 80, 90, 70)
        # error_message NO debe ser emitido
        comm.error_message.emit.assert_not_called()


def test_status_without_error_but_sys_is_dashes_no_measurement_ready():
    """Status sin error con P = "---" (sys < 0) → NO measurement_ready."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame: sin error pero con sys = "---" (ausente)
        body = b"S1;A0;C00;M00;P---------;R070;T    ;;"
        content = body + checksum_hex(body).encode("ascii")
        frame = b"\x02" + content + b"\x03\x0D"
        
        comm._handle_frame(frame)
        
        # measurement_ready NO debe ser emitido (sys < 0)
        comm.measurement_ready.emit.assert_not_called()
        # error_message NO debe ser emitido (sin error_code)
        comm.error_message.emit.assert_not_called()


def test_error_15_counter_increments_and_blocks_at_three():
    """Contador M15 se incrementa, y al tercero emite error_message. NO encola reset automático."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm._enqueue_command = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Primer error M15: cuenta a 1, NO encola reset
        frame1 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame1)
        assert comm._m15_consecutive_count == 1
        comm._enqueue_command.assert_not_called()  # NO encola (reset solo del botón)
        
        # Segundo error M15: cuenta a 2, NO encola reset
        frame2 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame2)
        assert comm._m15_consecutive_count == 2
        comm._enqueue_command.assert_not_called()  # NO encola
        
        # Tercer error M15: cuenta a 3, emite error_message, NO encola reset
        frame3 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame3)
        assert comm._m15_consecutive_count == 3
        comm._enqueue_command.assert_not_called()  # NO encola
        # Debe emitir error_message con "fallo repetido"
        comm.error_message.emit.assert_called()
        call_args = comm.error_message.emit.call_args
        assert call_args[0][0] == "M15"
        assert "fallo repetido" in call_args[0][1]


def test_successful_measurement_resets_m15_counter():
    """Una trama sin error_code reseta el contador M15."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Simular 2 errores M15
        frame_error1 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_error1)
        frame_error2 = build_status_frame(status_digit=1, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_error2)
        assert comm._m15_consecutive_count == 2
        
        # Luego, una medición exitosa
        frame_ok = build_status_frame(status_digit=1, error_code=None, sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame_ok)
        
        # El contador debe resetearse a 0
        assert comm._m15_consecutive_count == 0
        comm.measurement_ready.emit.assert_called_once()


def test_error_10_does_not_enqueue_software_reset():
    """Error M10 no debe encolar CMD_SOFTWARE_RESET; módulo en standby."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm._enqueue_command = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame: error M10 (ej. presión no alcanzada)
        frame = build_status_frame(status_digit=1, error_code="10", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame)
        
        # _enqueue_command NO debe ser llamado (sin reset automático)
        comm._enqueue_command.assert_not_called()
        
        # Contador M15 debe resetearse a 0 (no es M15)
        assert comm._m15_consecutive_count == 0


def test_valid_status_emits_measurement_ready_and_error_cleared():
    """Trama status válida debe emitir measurement_ready y error_cleared."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_cleared = Mock()
        comm.status_changed = Mock()
        
        # Frame: status válido (checksum ok, sin error, valores >= 0)
        frame = build_status_frame(status_digit=1, error_code=None, sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # measurement_ready DEBE emitirse
        comm.measurement_ready.emit.assert_called_once_with(120, 80, 90, 70)
        
        # error_cleared DEBE emitirse (limpiar estado de error)
        comm.error_cleared.emit.assert_called_once()
        
        # Counters reseteados
        assert comm._m15_consecutive_count == 0
        assert comm._last_error_code is None


def test_error_10_does_not_emit_measurement_ready_or_error_cleared():
    """Trama status con error M10 NO emite measurement_ready ni error_cleared."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.measurement_ready = Mock()
        comm.error_cleared = Mock()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Frame: error M10 (presión no alcanzada)
        frame = build_status_frame(status_digit=1, error_code="10", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame)
        
        # measurement_ready NO debe emitirse
        comm.measurement_ready.emit.assert_not_called()
        
        # error_cleared NO debe emitirse (hay error, no limpiamos)
        comm.error_cleared.emit.assert_not_called()
        
        # error_message SÍ debe emitirse
        comm.error_message.emit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_residual_error_at_startup_not_emitted():
    """Error residual al startup (_measurement_active=False) NO emite error_message ni cuenta M15."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # _measurement_active = False (valor inicial)
        assert comm._measurement_active is False
        
        # Frame: error M15 en startup (residual)
        frame = build_status_frame(status_digit=2, error_code="15", sys=120, dia=80, map_val=90, hr=70)
        comm._handle_frame(frame)
        
        # error_message NO debe ser emitido (error residual, no activo)
        comm.error_message.emit.assert_not_called()
        
        # Contador NO debe incrementar (error residual)
        assert comm._m15_consecutive_count == 0


def test_multiple_residual_errors_then_active_error():
    """Varios errores residuales al startup, luego medición con error → solo emite cuando activo."""
    with patch('connection.nibp_par_communication.QObject'):
        comm = NibpParCommunication()
        comm.error_message = Mock()
        comm.status_changed = Mock()
        
        # Frame 1: error residual M10 (startup)
        frame1 = build_status_frame(status_digit=1, error_code="10", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame1)
        comm.error_message.emit.assert_not_called()  # Sin emitir
        assert comm._m15_consecutive_count == 0
        
        # Frame 2: error residual M15 (startup)
        frame2 = build_status_frame(status_digit=1, error_code="15", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame2)
        comm.error_message.emit.assert_not_called()  # Sin emitir
        assert comm._m15_consecutive_count == 0  # No incrementa
        
        # Simular medición activa
        comm._measurement_active = True
        
        # Frame 3: error M15 durante medición activa
        frame3 = build_status_frame(status_digit=1, error_code="15", sys=-1, dia=-1, map_val=-1, hr=-1)
        comm._handle_frame(frame3)
        comm.error_message.emit.assert_called_once()  # Ahora sí emite
        assert comm._m15_consecutive_count == 1  # Y cuenta

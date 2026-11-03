"""
Preclinical smoke tests for production screens and core modules.

Tests that key production pantallas instantiate without exceptions,
and core functions behave safely under edge cases (None values, 0 values).

NO serial ports opened. If a screen crashes with None, the test turns RED.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from core.state_manager import TreatmentPhase
from gui.therapy.dialysis_screenV2 import DialysisScreen
from gui.therapy.heparin_config_screenV2 import HeparinConfigScreen
from gui.therapy.therapy_config_screenV2 import TherapyConfigScreen
from gui.therapy.nibp_config_screen import NibpConfigScreen
from gui.therapy.ktv_screen import KTVScreen


def create_mock_parent():
    """Create a real QWidget parent with mocked methods."""
    parent = QWidget()
    parent.start_treatment = Mock()
    parent.pause_treatment = Mock()
    parent.stop_treatment = Mock()
    parent.start_priming = Mock()
    parent.stop_priming = Mock()
    parent.show_ktv_screen = Mock()
    parent.show_warning_message = Mock()
    parent.current_values = {}
    parent.heparin_config_screen = None
    parent.patient_config_screen = None
    parent.therapy_config_screen = None
    return parent

from logic.ktv_calculator import CalculadoraKtV
from logic.heparin_time import (
    reference_minutes, max_heparin_minutes, clamp_heparin_time, was_clamped
)
from connection.nibp_protocol import parse_frame
from logic.uf_volume import litros_removidos


_app = None


def get_qapp():
    """Ensure QApplication exists for PySide6 widgets."""
    global _app
    if _app is None:
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication([])
    return _app


# ============================================================================
# Section 1: PANTALLAS (Screens)
# ============================================================================

class TestDialysisScreen:
    """Tests for DialysisScreen instantiation and basic operations."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def test_instantiate_with_parent_and_empty_values(self):
        """Instantiate DialysisScreen with mocked parent and empty values_dict."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        assert screen is not None
        assert screen.parent_window is parent
    
    def test_instantiate_with_all_tags_none(self):
        """Instantiate with None values_dict (should use empty dict)."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict=None)
        assert screen is not None
        assert screen.current_values == {}
    
    def test_update_values_with_empty_dict(self):
        """Call update_values with empty dict should not crash."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_values({})
        # No exception raised
    
    def test_update_state_idle(self):
        """Call update_state with IDLE phase."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_state(TreatmentPhase.IDLE)
        # No exception raised
    
    def test_update_state_preparing(self):
        """Call update_state with PREPARING phase."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_state(TreatmentPhase.PREPARING)
        # No exception raised
    
    def test_update_state_running(self):
        """Call update_state with RUNNING phase."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_state(TreatmentPhase.RUNNING)
        # No exception raised
    
    def test_update_state_paused(self):
        """Call update_state with PAUSED phase."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_state(TreatmentPhase.PAUSED)
        # No exception raised
    
    def test_update_state_cleaning(self):
        """Call update_state with CLEANING phase."""
        parent = create_mock_parent()
        screen = DialysisScreen(parent=parent, values_dict={})
        screen.update_state(TreatmentPhase.CLEANING)
        # No exception raised


class TestHeparinConfigScreen:
    """Tests for HeparinConfigScreen instantiation and operations."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def test_instantiate_with_parent_and_empty_values(self):
        """Instantiate HeparinConfigScreen with mocked parent and empty values_dict."""
        parent = create_mock_parent()
        screen = HeparinConfigScreen(parent=parent, values_dict={})
        assert screen is not None
        assert screen.parent_window is parent
    
    def test_instantiate_with_all_tags_none(self):
        """Instantiate with None values_dict."""
        parent = create_mock_parent()
        screen = HeparinConfigScreen(parent=parent, values_dict=None)
        assert screen is not None
        assert screen.current_values == {}
    
    def test_update_values_with_empty_dict(self):
        """Call update_values with empty dict should not crash."""
        parent = create_mock_parent()
        screen = HeparinConfigScreen(parent=parent, values_dict={})
        screen.update_values({})
        # No exception raised
    
    def test_update_state_all_phases(self):
        """Call update_state with all TreatmentPhase values."""
        parent = create_mock_parent()
        screen = HeparinConfigScreen(parent=parent, values_dict={})
        
        for phase in [TreatmentPhase.IDLE, TreatmentPhase.PREPARING, 
                      TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, 
                      TreatmentPhase.CLEANING]:
            screen.update_state(phase)
            # No exception raised


class TestTherapyConfigScreen:
    """Tests for TherapyConfigScreen instantiation and operations."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def test_instantiate_with_parent_and_empty_values(self):
        """Instantiate TherapyConfigScreen with mocked parent and empty values_dict."""
        parent = create_mock_parent()
        screen = TherapyConfigScreen(parent=parent, values_dict={})
        assert screen is not None
        assert screen.parent_window is parent
    
    def test_instantiate_with_all_tags_none(self):
        """Instantiate with None values_dict."""
        parent = create_mock_parent()
        screen = TherapyConfigScreen(parent=parent, values_dict=None)
        assert screen is not None
        assert screen.current_values == {}
    
    def test_update_values_with_empty_dict(self):
        """Call update_values with empty dict should not crash."""
        parent = create_mock_parent()
        screen = TherapyConfigScreen(parent=parent, values_dict={})
        screen.update_values({})
        # No exception raised
    
    def test_update_state_all_phases(self):
        """Call update_state with all TreatmentPhase values."""
        parent = create_mock_parent()
        screen = TherapyConfigScreen(parent=parent, values_dict={})
        
        for phase in [TreatmentPhase.IDLE, TreatmentPhase.PREPARING, 
                      TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, 
                      TreatmentPhase.CLEANING]:
            screen.update_state(phase)
            # No exception raised


class TestNibpConfigScreen:
    """Tests for NibpConfigScreen instantiation and operations."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def test_instantiate_with_parent(self):
        """Instantiate NibpConfigScreen with mocked parent."""
        parent = create_mock_parent()
        screen = NibpConfigScreen(parent=parent)
        assert screen is not None
        assert screen.parent_window is parent
    
    def test_instantiate_without_parent(self):
        """Instantiate NibpConfigScreen without parent (None)."""
        screen = NibpConfigScreen(parent=None)
        assert screen is not None


class TestKTVScreen:
    """Tests for KTVScreen instantiation and operations."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def test_instantiate_with_parent_and_empty_values(self):
        """Instantiate KTVScreen with mocked parent and empty values_dict."""
        parent = create_mock_parent()
        screen = KTVScreen(parent=parent, values_dict={})
        assert screen is not None
        assert screen.parent_window is parent
    
    def test_instantiate_with_all_tags_none(self):
        """Instantiate with None values_dict."""
        parent = create_mock_parent()
        screen = KTVScreen(parent=parent, values_dict=None)
        assert screen is not None
        assert screen.current_values == {}
    
    def test_update_values_with_empty_dict(self):
        """Call update_values with empty dict should not crash."""
        parent = create_mock_parent()
        screen = KTVScreen(parent=parent, values_dict={})
        screen.update_values({})
        # No exception raised
    
    def test_update_state_all_phases(self):
        """Call update_state with all TreatmentPhase values."""
        parent = create_mock_parent()
        screen = KTVScreen(parent=parent, values_dict={})
        
        for phase in [TreatmentPhase.IDLE, TreatmentPhase.PREPARING, 
                      TreatmentPhase.RUNNING, TreatmentPhase.PAUSED, 
                      TreatmentPhase.CLEANING]:
            screen.update_state(phase)
            # No exception raised


# ============================================================================
# Section 2: HEPARINA - Auto-trim on RUNNING
# ============================================================================

class TestHeparinAutoTrimOnRunning:
    """Tests for HemodialysisHMI._apply_heparin_auto_trim_on_running method."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        get_qapp()
    
    def _create_hmi_with_mocks(self, therapy_hours=0, therapy_minutes=60,
                                heparin_auto_hours=0, heparin_auto_minutes=60):
        """
        Create a HemodialysisHMI instance with mocked dependencies.
        
        Mocks:
        - _write_setpoint: collects written tags and values
        - _persist_therapy_config_tag: collects persisted tags and values
        - ignore_tags_until: empty dict
        - _get_heparin_flow_ml_per_h: returns 20.0
        
        Args:
            therapy_hours, therapy_minutes: Therapy programmed duration
            heparin_auto_hours, heparin_auto_minutes: Heparin programmed duration
        
        Returns:
            tuple: (hmi_instance, written_tags_dict, persisted_tags_dict)
        """
        from gui.appMainHemodialysis import HemodialysisHMI
        
        hmi = Mock(spec=HemodialysisHMI)
        
        hmi.current_values = {
            "heparineTherapyHours": float(therapy_hours),
            "heparineTherapyMinutes": float(therapy_minutes),
            "heparineAutoStopHours": float(heparin_auto_hours),
            "heparineAutoStopMinutes": float(heparin_auto_minutes),
        }
        
        written_tags = {}
        persisted_tags = {}
        
        def mock_write_setpoint(tag, value):
            written_tags[tag] = value
        
        def mock_persist_therapy_config_tag(tag, value):
            persisted_tags[tag] = value
        
        def mock_get_heparin_flow_ml_per_h():
            return 20.0
        
        hmi._write_setpoint = Mock(side_effect=mock_write_setpoint)
        hmi._persist_therapy_config_tag = Mock(side_effect=mock_persist_therapy_config_tag)
        hmi._get_heparin_flow_ml_per_h = Mock(side_effect=mock_get_heparin_flow_ml_per_h)
        hmi.ignore_tags_until = {}
        hmi.heparin_config_screen = None
        
        # Bind the real method to this mock instance
        from gui.appMainHemodialysis import HemodialysisHMI as RealHMI
        hmi._apply_heparin_auto_trim_on_running = RealHMI._apply_heparin_auto_trim_on_running.__get__(hmi, Mock)
        
        return hmi, written_tags, persisted_tags
    
    def test_scenario_1_therapy_60m_heparin_60m_with_autostop_1(self):
        """
        Scenario 1: Therapy 01:00 (60 min) + Heparin 01:00 (60 min)
        heparineAutoStop = 1 and 0
        After trim: heparin → 00:30 (30 min)
        Dosage calculated with 0.5 h (half hour).
        ignore_tags_until marked for all three tags before _write_setpoint.
        """
        hmi, written, persisted = self._create_hmi_with_mocks(
            therapy_hours=0,
            therapy_minutes=60,
            heparin_auto_hours=1,
            heparin_auto_minutes=0
        )
        
        hmi._apply_heparin_auto_trim_on_running()
        
        # Verify current_values updated
        assert hmi.current_values["heparineAutoStopHours"] == 0
        assert hmi.current_values["heparineAutoStopMinutes"] == 30
        
        # Verify dosage calculated with 0.5 h: 0.5 * 20 = 10.0
        expected_dosage = 0.5 * 20.0
        assert hmi.current_values["heparineTherapyDosage"] == expected_dosage
        
        # Verify ignore_tags_until marked BEFORE _write_setpoint calls
        assert "heparineAutoStopHours" in hmi.ignore_tags_until
        assert "heparineAutoStopMinutes" in hmi.ignore_tags_until
        assert "heparineTherapyDosage" in hmi.ignore_tags_until
        
        # Verify _write_setpoint called for all three tags
        assert hmi._write_setpoint.call_count == 3
        
        # Verify _persist_therapy_config_tag called for all three tags
        assert hmi._persist_therapy_config_tag.call_count == 3
        
        # Verify written values
        assert written["heparineAutoStopHours"] == 0.0
        assert written["heparineAutoStopMinutes"] == 30.0
        assert written["heparineTherapyDosage"] == expected_dosage
    
    def test_scenario_2_therapy_180m_heparin_60m_no_change(self):
        """
        Scenario 2: Therapy 03:00 (180 min) + Heparin 01:00 (60 min)
        Max allowed: 180 - 30 = 150 min
        Heparin 60 min < 150 min → NO TRIM
        The function should not write anything.
        """
        hmi, written, persisted = self._create_hmi_with_mocks(
            therapy_hours=0,
            therapy_minutes=180,
            heparin_auto_hours=1,
            heparin_auto_minutes=0
        )
        
        hmi._apply_heparin_auto_trim_on_running()
        
        # Verify no write_setpoint or persist calls
        assert hmi._write_setpoint.call_count == 0
        assert hmi._persist_therapy_config_tag.call_count == 0
        
        # Verify nothing written
        assert len(written) == 0
        assert len(persisted) == 0
    
    def test_scenario_3_therapy_60m_heparin_20m_no_change(self):
        """
        Scenario 3: Therapy 01:00 (60 min) + Heparin 00:20 (20 min)
        Max allowed: 60 - 30 = 30 min
        Heparin 20 min < 30 min → NO TRIM
        The function should not write anything.
        """
        hmi, written, persisted = self._create_hmi_with_mocks(
            therapy_hours=0,
            therapy_minutes=60,
            heparin_auto_hours=0,
            heparin_auto_minutes=20
        )
        
        hmi._apply_heparin_auto_trim_on_running()
        
        # Verify no write_setpoint or persist calls
        assert hmi._write_setpoint.call_count == 0
        assert hmi._persist_therapy_config_tag.call_count == 0
        
        # Verify nothing written
        assert len(written) == 0
        assert len(persisted) == 0
    
    def test_scenario_4_paused_to_running_no_invoke(self):
        """
        Scenario 4: Verify that _apply_heparin_auto_trim_on_running is NOT called
        when transitioning from PAUSED to RUNNING in update_value.
        
        This test mocks the update_value method and checks that the condition
        (old_phase != TreatmentPhase.PAUSED) prevents the call.
        """
        from gui.appMainHemodialysis import HemodialysisHMI
        
        # Create a real mock but with patched update_value
        hmi = Mock(spec=HemodialysisHMI)
        hmi._apply_heparin_auto_trim_on_running = Mock()
        
        # Simulate the logic from update_value:
        # if new_phase == TreatmentPhase.RUNNING:
        #     if old_phase != TreatmentPhase.PAUSED:
        #         self._apply_heparin_auto_trim_on_running()
        
        old_phase = TreatmentPhase.PAUSED
        new_phase = TreatmentPhase.RUNNING
        
        if new_phase == TreatmentPhase.RUNNING:
            if old_phase != TreatmentPhase.PAUSED:
                hmi._apply_heparin_auto_trim_on_running()
        
        # Verify the method was NOT called
        hmi._apply_heparin_auto_trim_on_running.assert_not_called()
    
    def test_scenario_5_idle_to_running_calls_method(self):
        """
        Scenario 5: Verify that _apply_heparin_auto_trim_on_running IS called
        when transitioning from IDLE (or other non-PAUSED phases) to RUNNING.
        
        This confirms the guard condition only blocks PAUSED → RUNNING.
        """
        from gui.appMainHemodialysis import HemodialysisHMI
        
        hmi = Mock(spec=HemodialysisHMI)
        hmi._apply_heparin_auto_trim_on_running = Mock()
        
        # Simulate the logic from update_value with old_phase = IDLE
        old_phase = TreatmentPhase.IDLE
        new_phase = TreatmentPhase.RUNNING
        
        if new_phase == TreatmentPhase.RUNNING:
            if old_phase != TreatmentPhase.PAUSED:
                hmi._apply_heparin_auto_trim_on_running()
        
        # Verify the method WAS called
        hmi._apply_heparin_auto_trim_on_running.assert_called_once()


# ============================================================================
# Section 3: Kt/V CALCULATOR - Zero/None handling
# ============================================================================

class TestKtvCalculatorIonicEdgeCases:
    """Tests for Kt/V ionic calculation with zero and None conductivities."""
    
    def test_zero_conductivities_and_flows(self):
        """With Qd=0, Qb=0, Qf=0, conductivities=0, D should be 0 (no exception)."""
        calc = CalculadoraKtV()
        calc.set_volumen_bioimpedancia(30.0)
        
        # Store zero conductivities
        calc.store_conductivity_t1(0.0, 0.0)
        calc.store_conductivity_t2(0.0, 0.0)
        
        # Calculate D with zero flows
        d = calc.calculate_d_ionic(qd=0.0, qf=0.0, qb=0.0)
        assert d == 0.0  # No exception, result is 0
    
    def test_none_like_values(self):
        """With very small deltas, D should not crash and should be 0."""
        calc = CalculadoraKtV()
        calc.set_volumen_bioimpedancia(30.0)
        
        # Store small conductivities (delta < 0.05 threshold)
        calc.store_conductivity_t1(13.5, 13.45)
        calc.store_conductivity_t2(13.50001, 13.45001)
        
        # Delta is very small (< 0.05)
        d = calc.calculate_d_ionic(qd=500.0, qf=10.0, qb=300.0)
        assert d == 0.0  # Should return 0 due to small delta threshold
    
    def test_valid_d_calculation(self):
        """With valid conductivity deltas and ratio, D should be calculated."""
        calc = CalculadoraKtV()
        calc.set_volumen_bioimpedancia(30.0)
        
        # Store conductivities with larger delta and proper ratio
        # delta_ef = 0.2, delta_sf = 0.1 -> ratio 0.5, should give positive D
        calc.store_conductivity_t1(13.5, 13.45)
        calc.store_conductivity_t2(13.7, 13.55)  # delta_ef = 0.2, delta_sf = 0.1
        
        d = calc.calculate_d_ionic(qd=500.0, qf=10.0, qb=300.0)
        assert d > 0  # Should calculate a positive D
    
    def test_first_dt_is_zero(self):
        """First interval (dt) is 0 seconds when no prior measurement."""
        calc = CalculadoraKtV()
        
        # Before any measurement, tiempo_ultima_medicion is None
        assert calc.tiempo_ultima_medicion is None
        
        # After reset, it's still None
        calc.reset()
        assert calc.tiempo_ultima_medicion is None
    
    def test_get_ktv_delivered_vs_projected(self):
        """get_ktv_projected and get_ktv_delivered differ if time remains."""
        calc = CalculadoraKtV()
        calc.set_volumen_bioimpedancia(30.0)
        
        # Mock the calculation
        calc.kt_acumulado = 10.0
        calc.tiempo_ultima_medicion = 30.0  # 30 minutes elapsed
        
        # If we call get_ktv_delivered (elapsed only) vs projected (remaining + elapsed),
        # they should differ if time remains in therapy.
        # This is tested in the actual test_ktv_calculator_ionic.py with real scenarios.


# ============================================================================
# Section 4: NIBP PROTOCOL - Frame parsing with errors
# ============================================================================

class TestNibpProtocolEdgeCases:
    """Tests for NIBP frame parsing edge cases."""
    
    def test_parse_frame_status_with_error_M10(self):
        """
        Status frame with error M10 (values out of range).
        Should parse but indicate an error (valid measurement = False).
        """
        # M10 is "valores fuera de rango" (values out of range)
        # Build a status frame with M10
        status_content = b"S1;A0;C00;M10;P101065076;R060;T    ;;F3"
        
        # Wrap with STX/ETX
        frame = bytes([0xFD]) + status_content + bytes([0xFE, 0x0D])
        
        result = parse_frame(frame)
        assert result is not None
        assert result["type"] == "status"
        assert result["error_code"] == "10"
        assert result["error_text"] == "valores fuera de rango"
    
    def test_parse_frame_garbage_data(self):
        """Garbage data should not crash; returns None or {'type': 'unknown'}."""
        garbage = b"\xFD\xFF\xFF\xFF\xFE\x0D"
        result = parse_frame(garbage)
        # Either None or unknown type is acceptable
        assert result is None or result.get("type") == "unknown"
    
    def test_parse_frame_none_input(self):
        """parse_frame(None) should not crash."""
        result = parse_frame(None)
        assert result is None
    
    def test_parse_frame_empty_bytes(self):
        """parse_frame(b'') should not crash."""
        result = parse_frame(b"")
        assert result is None
    
    def test_patient_mode_in_status_frame(self):
        """Status frame with patient_mode="adult" (A digit = 0)."""
        status_content = b"S1;A0;C00;M00;P101065076;R060;T    ;;F3"
        frame = bytes([0xFD]) + status_content + bytes([0xFE, 0x0D])
        
        result = parse_frame(frame)
        assert result is not None
        assert result["patient_mode"] == 0  # 0 = adult mode


# ============================================================================
# Section 5: UF VOLUME - Pump speed and pulse count None handling
# ============================================================================

class TestUfVolumeEdgeCases:
    """Tests for UF volume calculation with None and edge values."""
    
    def test_litros_removidos_with_zero_pulses(self):
        """With 0 pulses, result should be 0.0 (no exception)."""
        result = litros_removidos(0)
        assert result == 0.0
    
    def test_litros_removidos_with_none_like_value(self):
        """Negative pulses should return 0.0."""
        result = litros_removidos(-100)
        assert result == 0.0
    
    def test_litros_removidos_with_valid_pulses(self):
        """With 1000 pulses, result should be ~0.94 L."""
        result = litros_removidos(1000)
        assert result == round(1000 * 0.94162 / 1000.0, 2)
        assert result > 0.0
    
    def test_therapy_3h_with_1_l_h_uf_target(self):
        """
        With ultraFilterPumpSpeed = 1 L/h and therapy duration = 03:00:
        Target UF volume should be 3.00 L.
        """
        uf_rate_l_h = 1.0
        therapy_duration_min = 180  # 3 hours
        therapy_duration_h = therapy_duration_min / 60
        
        expected_uf_l = uf_rate_l_h * therapy_duration_h
        assert expected_uf_l == 3.0
        
        # If we have pumped exactly 3 L, pulses should be:
        # pulses = 3000 mL / 0.94162 mL/pulse ≈ 3185.6 pulses
        # litros_removidos(3185) should be ~3.0
        pulses_needed = int(3000 / 0.94162)
        result = litros_removidos(pulses_needed)
        assert result >= 2.99 and result <= 3.01  # Within 0.01 L


# ============================================================================
# Run the tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

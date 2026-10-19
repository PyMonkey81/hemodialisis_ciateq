"""
Smoke tests for animal trial robustness.

Tests that incomplete or zero data does not cause exceptions.
No serial ports, no full GUI instantiation.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget


def get_qapp():
    """Get or create QApplication singleton."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestDialysisScreenUpdateValues:
    """Test DialysisScreen.update_values with incomplete data."""
    
    def _create_parent_widget(self):
        """Create a mock parent widget with all necessary methods."""
        parent = QWidget()
        # Inject all required methods as attributes
        parent.start_treatment = Mock()
        parent.pause_treatment = Mock()
        parent.stop_treatment = Mock()
        parent.start_priming = Mock()
        parent.stop_priming = Mock()
        parent.show_warning_message = Mock()
        parent.show_heparin_config_screen = Mock()
        parent.show_patient_config = Mock()
        parent.show_therapy_config = Mock()
        parent.show_ktv_screen = Mock()
        parent.get_remaining_therapy_minutes = Mock(return_value=180)
        parent.get_elapsed_seconds = Mock(return_value=0)
        
        return parent
    
    def test_update_values_empty_dict(self):
        """Empty dictionary should not crash."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        # This should not raise
        screen.update_values({})
        
        # Labels should have text (at least default values)
        assert screen.uf_rate_val.text() is not None
        assert screen.uf_goal_val.text() is not None
        assert screen.uf_rem_val.text() is not None
        assert screen.ktv_val.text() is not None
    
    def test_update_values_missing_uf_keys(self):
        """Missing UF keys (ultraFilterPumpSpeed, ufPumpPulseCount, uf_goal_liters)."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        data = {
            "bloodArteryPressureData": 120.0,
            "bloodVenousPressureData": 40.0,
            # No UF keys
        }
        
        # Should not raise
        screen.update_values(data)
        
        # Should have default text
        assert len(screen.uf_goal_val.text()) > 0
        assert len(screen.uf_rem_val.text()) > 0
    
    def test_update_values_uf_goal_exact_format(self):
        """UF goal must be exactly '3.00' when tasa=1 L/h and therapy=3:00."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        
        # 1 L/h × 3:00 therapy = exactly 3.00 L
        data = {
            "ultraFilterPumpSpeed": 1.0,
            "ufPumpPulseCount": 500,
            "heparineTherapyHours": 3,
            "heparineTherapyMinutes": 0,
        }
        screen.update_values(data)
        
        # Must be exactly "3.00", not just "3"
        assert "3.00" in screen.uf_goal_val.text(), \
            f"Expected '3.00' in goal, got '{screen.uf_goal_val.text()}'"
    
    def test_update_values_none_pressures_cond_temp(self):
        """Pressures, conductivity, and temperature as None."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        data = {
            "bloodArteryPressureData": None,
            "bloodVenousPressureData": None,
            "dialyCondVariableData": None,
            "dialyTempIFProcessData": None,
            "dialyPresIFProcessData": None,
            "dialyPresOFProcessData": None,
        }
        
        # Should not raise
        screen.update_values(data)
        
        # Labels should have text
        assert screen.art_p_value.text() is not None
        assert screen.ven_p_value.text() is not None
        assert screen.cond_val.text() is not None
        assert screen.temp_value.text() is not None
    
    def test_update_values_none_uf_and_therapy_fields(self):
        """UF speed, therapy hours/minutes, and pulse count as None should not crash."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        data = {
            "ultraFilterPumpSpeed": None,      # None instead of float
            "balanceChamberCycleCount": None,  # None instead of int
            "heparineTherapyHours": None,      # None instead of int
            "heparineTherapyMinutes": None,    # None instead of int
        }
        
        # Should not raise exception
        try:
            screen.update_values(data)
        except Exception as e:
            pytest.fail(f"update_values raised exception with None UF/therapy values: {e}")
        
        # UF labels should have text (not crash when displaying)
        assert screen.uf_rate_val.text() is not None, "UF rate label should have text"
        assert screen.uf_goal_val.text() is not None, "UF goal label should have text"
        assert screen.uf_rem_val.text() is not None, "UF removed label should have text"
    
    def test_heart_rate_display(self):
        """Heart rate should display correctly and handle negative values."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen
        
        get_qapp()
        
        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)
        
        # Test valid heart rate
        screen.update_nibp_measurement(sys_mmhg=120, dia_mmhg=80, map_mmhg=93, hr_bpm=72)
        assert screen.hr_value.text() == "72", f"Expected '72', got '{screen.hr_value.text()}'"
        
        # Test negative heart rate shows "--"
        screen.update_nibp_measurement(sys_mmhg=120, dia_mmhg=80, map_mmhg=93, hr_bpm=-1)
        assert screen.hr_value.text() == "--", f"Expected '--', got '{screen.hr_value.text()}'"
        
        # Test zero heart rate is valid
        screen.update_nibp_measurement(sys_mmhg=120, dia_mmhg=80, map_mmhg=93, hr_bpm=0)
        assert screen.hr_value.text() == "0", f"Expected '0', got '{screen.hr_value.text()}'"


class TestUfVolumeCalculation:
    """Test UF volume calculation with edge cases."""
    
    def test_uf_volume_zero_pulses(self):
        """0 pulses should give 0.00 L."""
        from logic.uf_volume import litros_removidos
        
        result = litros_removidos(0)
        assert result == 0.0
    
    def test_uf_volume_negative_pulses(self):
        """Negative pulses should clamp to 0."""
        from logic.uf_volume import litros_removidos
        
        result = litros_removidos(-100)
        assert result == 0.0
    
    def test_uf_volume_large_pulses(self):
        """Large pulse counts should calculate correctly."""
        from logic.uf_volume import litros_removidos
        
        # 1,000,000 pulses × 1.0 ml/pulse = 1000 liters
        result = litros_removidos(1_000_000)
        assert result == 1000.0
    
    def test_uf_volume_rounding(self):
        """Result should round to 2 decimals."""
        from logic.uf_volume import litros_removidos
        
        # 1234 pulses × 1.0 ml/pulse = 1.234 liters → 1.23 L
        result = litros_removidos(1234)
        assert result == 1.23
        
        # 1235 pulses × 1.0 ml/pulse = 1.235 liters → 1.24 L (round half up)
        result = litros_removidos(1235)
        assert result == 1.24


class TestKtVCalculation:
    """Test Kt/V calculation module can be imported and used."""
    
    def test_ktv_calculator_import(self):
        """Kt/V calculator module should be importable."""
        # Import Kt/V calculator class - let it fail red if module doesn't exist
        from logic.ktv_calculator import CalculadoraKtV
        
        calc = CalculadoraKtV()
        
        # Just verify it has key methods
        assert hasattr(calc, 'get_ktv_delivered')
        assert hasattr(calc, 'get_ktv_projected')
        assert hasattr(calc, 'calculate_ktv_ionic')
        assert hasattr(calc, 'reset')
        assert hasattr(calc, 'update_kt')
    
    def test_ktv_calculator_reset(self):
        """Kt/V calculator reset should not crash."""
        from logic.ktv_calculator import CalculadoraKtV
        
        calc = CalculadoraKtV()
        
        # Reset should not raise exception
        calc.reset()
        
        # After reset, state should be clean
        assert calc is not None


class TestPressureWaveformGraphRobustness:
    """Test PressureWaveformWidget can handle None values in history."""
    
    def test_pressure_plot_none_values_no_crash(self):
        """Pressure plot should handle None values in history without crashing."""
        from gui.therapy.dialysis_screenV2 import PressureWaveformWidget
        
        get_qapp()
        
        # Create a minimal parent widget for the graph
        parent = QWidget()
        graph = PressureWaveformWidget(parent)
        
        # Add some normal values
        graph.add_values(90.0, 50.0)
        graph.add_values(95.0, 52.0)
        
        # Add None values (simulating a communication error)
        graph.add_values(None, None)
        graph.add_values(100.0, None)
        graph.add_values(None, 55.0)
        
        # Repaint should not crash
        try:
            graph.paintEvent(None)
        except Exception as e:
            pytest.fail(f"paintEvent raised exception with None values in history: {e}")
        
        # Graph should still be valid
        assert graph is not None


class TestHeparinConfigScreenRunning:
    """Test HeparinConfigScreen with real widget in RUNNING phase."""
    
    def _create_parent_for_heparin(self, phase):
        """Create real QWidget parent with proper attributes."""
        from core.state_manager import TreatmentPhase
        
        parent = QWidget()
        parent.state = Mock()
        parent.state.current_phase = phase
        parent.current_values = {
            "heparineAutoStopHours": 2,
            "heparineAutoStopMinutes": 30,
        }
        parent.show_warning_message = Mock()
        parent.begin_operator_alert = Mock()
        parent.end_operator_alert = Mock()
        parent.set_heparin_infusion_enabled = Mock()
        parent.get_remaining_therapy_minutes = Mock(return_value=180)
        parent.get_elapsed_seconds = Mock(return_value=0)
        
        return parent
    
    def test_heparin_running_time_disabled_stays_020(self):
        """In RUNNING, time field disabled and stays 02:30 with infusion enabled."""
        from core.state_manager import TreatmentPhase
        from gui.therapy.heparin_config_screenV2 import HeparinConfigScreen
        
        get_qapp()
        
        parent = self._create_parent_for_heparin(TreatmentPhase.PREPARING)
        parent.current_values = {
            "heparineInfusionEnabled": 1.0,
            "heparineAutoStopHours": 2,
            "heparineAutoStopMinutes": 30,
        }
        
        screen = HeparinConfigScreen(parent)
        screen.current_values = parent.current_values
        screen.chk_heparin_enabled.setChecked(True)
        screen.input_heparin_auto_stop.setText("02:30")
        
        # Switch to RUNNING
        screen.update_state(TreatmentPhase.RUNNING)
        
        # Field must be disabled
        assert not screen.input_heparin_auto_stop.isEnabled(), \
            "Field should be disabled in RUNNING phase"
        
        # Text must stay "02:30"
        assert screen.input_heparin_auto_stop.text() == "02:30", \
            f"Expected '02:30' but got '{screen.input_heparin_auto_stop.text()}'"
    
    def test_heparin_running_uncheck_recheck_stays_020(self):
        """In RUNNING, uncheck and recheck infusion; text stays 02:30 and stays disabled."""
        from core.state_manager import TreatmentPhase
        from gui.therapy.heparin_config_screenV2 import HeparinConfigScreen
        
        get_qapp()
        
        parent = self._create_parent_for_heparin(TreatmentPhase.PREPARING)
        parent.current_values = {
            "heparineInfusionEnabled": 1.0,
            "heparineAutoStopHours": 2,
            "heparineAutoStopMinutes": 30,
        }
        
        screen = HeparinConfigScreen(parent)
        screen.current_values = parent.current_values
        screen.chk_heparin_enabled.setChecked(True)
        screen.input_heparin_auto_stop.setText("02:30")
        
        # Switch to RUNNING - update both screen and parent state
        parent.state.current_phase = TreatmentPhase.RUNNING
        screen.update_state(TreatmentPhase.RUNNING)
        
        # Uncheck
        screen.chk_heparin_enabled.setChecked(False)
        assert screen.input_heparin_auto_stop.text() == "02:30"
        assert not screen.input_heparin_auto_stop.isEnabled()
        
        # Recheck
        screen.chk_heparin_enabled.setChecked(True)
        assert screen.input_heparin_auto_stop.text() == "02:30", \
            "Text should not change when toggling infusion in RUNNING"
        assert not screen.input_heparin_auto_stop.isEnabled(), \
            "Field should stay disabled even after recheck in RUNNING"
    
    def test_heparin_missing_values_no_crash(self):
        """Missing heparin values (None, empty dict) should not crash."""
        from core.state_manager import TreatmentPhase
        from gui.therapy.heparin_config_screenV2 import HeparinConfigScreen
        
        get_qapp()
        
        parent = self._create_parent_for_heparin(TreatmentPhase.PREPARING)
        parent.current_values = {}  # Completely empty
        
        screen = HeparinConfigScreen(parent)
        screen.current_values = {}
        
        # Should not raise any exception
        screen.update_values({})
        screen.update_state(TreatmentPhase.RUNNING)
        
        # Screen should exist and not crash
        assert screen is not None
    
    def test_heparin_none_volume_values_no_crash(self):
        """Syringe volume, bolus, and syringe size as None should not crash."""
        from core.state_manager import TreatmentPhase
        from gui.therapy.heparin_config_screenV2 import HeparinConfigScreen
        
        get_qapp()
        
        parent = self._create_parent_for_heparin(TreatmentPhase.PREPARING)
        parent.current_values = {
            "heparineInfusionEnabled": 1.0,
            "heparineSyringeVolume": None,  # None instead of float
            "heparineBolusQuantity": None,  # None instead of float
            "heparineSyringeSize": None,    # None instead of float
        }
        
        screen = HeparinConfigScreen(parent)
        screen.current_values = parent.current_values
        
        # Should not raise any exception when updating with None values
        try:
            screen.update_values({
                "heparineSyringeVolume": None,
                "heparineBolusQuantity": None,
                "heparineSyringeSize": None,
            })
        except Exception as e:
            pytest.fail(f"update_values raised exception with None values: {e}")
        
        # Fields should display "0.0" (handled as default)
        assert screen.input_vol_hep.text() == "0.0", \
            "Syringe volume should display '0.0' when None"
        assert screen.input_bolus.text() == "0.0", \
            "Bolus quantity should display '0.0' when None"


class TestStartTreatmentLogic:
    """Test _can_start_treatment logic without running therapy."""
    
    def test_state_13_fresh_fill_cannot_start(self):
        """State 13, fill just started: cannot start and header NOT 'LISTO PARA INICIAR'."""
        from core.state_manager import TreatmentPhase
        from gui.appMainHemodialysis import HemodialysisHMI
        from PySide6.QtCore import QDateTime
        
        # Create minimal HMI instance for testing
        hmi = HemodialysisHMI.__new__(HemodialysisHMI)
        
        # Initialize minimum required attributes
        hmi.current_values = {
            "treatmentModeSelection": 0,
            "dialyTempIFProcessData": 37.0,
            "dialyCondVariableData": 14.0,
        }
        hmi.state = Mock()
        hmi.state.current_phase = TreatmentPhase.READY  # State 13 = READY
        hmi._last_priming_status = 13
        hmi.filter_fill_waiting = True  # <-- Critical: filter fill in progress
        hmi.filter_fill_start_time = QDateTime.currentDateTime()  # Just started
        hmi.MIN_FILTER_FILL_WAIT_SECONDS = 90
        hmi.alarm_system = None
        hmi.ignore_tags_until = {}
        hmi.current_process_status = Mock()
        hmi.current_process_status.setText = Mock()
        hmi.current_process_status.setStyleSheet = Mock()
        hmi.screen_state_manager = Mock()
        hmi.screen_state_manager.update_all_screens = Mock()
        hmi.hardware_mapper = Mock()
        hmi.hardware_mapper.get_display_text = Mock(return_value="LISTO PARA\nINICIAR")
        hmi.timer_manager = Mock()
        hmi.timer_manager.sync_with_hardware = Mock()
        hmi.treatment_controller = None
        hmi.show_info_message = Mock()
        
        # Test: _can_start_treatment should return False (elapsed < 90s)
        can_start = hmi._can_start_treatment()
        assert not can_start, "Should not be able to start with fresh fill (<90s)"
    
    def test_state_13_90s_elapsed_can_start(self):
        """State 13, 90s elapsed, temp/cond in range: can start."""
        from core.state_manager import TreatmentPhase
        from gui.appMainHemodialysis import HemodialysisHMI
        from PySide6.QtCore import QDateTime
        
        hmi = HemodialysisHMI.__new__(HemodialysisHMI)
        
        # Initialize attributes - include setpoints for validation logic
        hmi.current_values = {
            "treatmentModeSelection": 0,
            "dialyTempIFProcessData": 37.0,
            "dialyTempControlSetPoint": 37.0,  # Setpoint
            "dialyCondVariableData": 14.0,
            "dialyCondControlSetPoint": 14.0,  # Setpoint
        }
        hmi.state = Mock()
        hmi.state.current_phase = TreatmentPhase.READY  # State 13 = READY
        hmi._last_priming_status = 13
        hmi.filter_fill_waiting = True  # <-- Critical: filter fill in progress
        # Fill started 95 seconds ago
        hmi.filter_fill_start_time = QDateTime.currentDateTime().addSecs(-95)
        hmi.MIN_FILTER_FILL_WAIT_SECONDS = 90
        hmi.alarm_system = None
        hmi.ignore_tags_until = {}
        hmi.current_process_status = Mock()
        hmi.current_process_status.setText = Mock()
        hmi.current_process_status.setStyleSheet = Mock()
        hmi.screen_state_manager = Mock()
        hmi.screen_state_manager.update_all_screens = Mock()
        hmi.hardware_mapper = Mock()
        hmi.hardware_mapper.get_display_text = Mock(return_value="LISTO PARA\nINICIAR")
        hmi.timer_manager = Mock()
        hmi.timer_manager.sync_with_hardware = Mock()
        hmi.treatment_controller = None
        hmi.show_info_message = Mock()
        
        # Test: _can_start_treatment should return True (elapsed >= 90s AND temp/cond OK)
        can_start = hmi._can_start_treatment()
        assert can_start, "Should be able to start after 90s with valid temp/cond"
    
    def test_state_13_missing_temp_cond_no_crash(self):
        """State 13 with missing temp/cond: no exception, handles gracefully."""
        from core.state_manager import TreatmentPhase
        from gui.appMainHemodialysis import HemodialysisHMI
        from PySide6.QtCore import QDateTime
        
        hmi = HemodialysisHMI.__new__(HemodialysisHMI)
        
        # Initialize with missing temperature/conductivity
        hmi.current_values = {
            "treatmentModeSelection": 0,
            # Missing dialyTempIFProcessData and dialyCondVariableData
            # Will default to 0.0
        }
        hmi.state = Mock()
        hmi.state.current_phase = TreatmentPhase.READY
        hmi._last_priming_status = 13
        hmi.filter_fill_waiting = True  # <-- Critical: filter fill in progress
        hmi.filter_fill_start_time = QDateTime.currentDateTime().addSecs(-95)  # 95s elapsed
        hmi.MIN_FILTER_FILL_WAIT_SECONDS = 90
        hmi.alarm_system = None
        hmi.ignore_tags_until = {}
        hmi.current_process_status = Mock()
        hmi.current_process_status.setText = Mock()
        hmi.current_process_status.setStyleSheet = Mock()
        hmi.screen_state_manager = Mock()
        hmi.screen_state_manager.update_all_screens = Mock()
        hmi.hardware_mapper = Mock()
        hmi.hardware_mapper.get_display_text = Mock(return_value="LISTO PARA\nINICIAR")
        hmi.timer_manager = Mock()
        hmi.timer_manager.sync_with_hardware = Mock()
        hmi.treatment_controller = None
        hmi.show_info_message = Mock()
        
        # Should not raise exception - missing values should be handled gracefully
        try:
            can_start = hmi._can_start_treatment()
            # Result can be True or False depending on how defaults are compared
            assert isinstance(can_start, bool), "Should return a boolean"
        except Exception as e:
            pytest.fail(f"_can_start_treatment raised exception: {e}")



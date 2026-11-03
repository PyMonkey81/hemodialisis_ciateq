"""
Tests for HemodialysisHMI.start_treatment() integration with start_checklist.

Tests the complete flow with mocked dependencies:
- treatment_controller.start_treatment
- show_warning_message
- FloatingConfirmDialog.show_confirm
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from core.state_manager import TreatmentPhase


def create_qapp():
    """Ensure QApplication exists for PySide6 widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestStartTreatmentGate:
    """Tests for start_treatment() with start_checklist integration."""
    
    def setup_method(self):
        """Set up QApplication before each test."""
        create_qapp()
    
    def _create_hmi_with_mocks(self, phase=TreatmentPhase.READY, values_dict=None):
        """
        Create a HemodialysisHMI mock with the real start_treatment method bound.
        
        Mocks:
        - treatment_controller.start_treatment: tracked for calls
        - show_warning_message: tracks messages
        - FloatingConfirmDialog.show_confirm: controlled return value
        - ignore_tags_until: empty dict
        - state.current_phase: set to provided phase
        - screen_state_manager.update_all_screens: mocked
        
        Args:
            phase: TreatmentPhase for state.current_phase
            values_dict: current_values dict (empty if None)
        
        Returns:
            tuple: (hmi_mock, controller_mock, warning_messages, confirm_dialog)
        """
        from gui.appMainHemodialysis import HemodialysisHMI
        
        hmi = Mock(spec=HemodialysisHMI)
        
        # Set phase
        hmi.state = Mock()
        hmi.state.current_phase = phase
        
        # Set current_values
        hmi.current_values = values_dict or {}
        
        # Track warning messages
        warning_messages = []
        def mock_show_warning_message(text, timeout_ms=4500):
            warning_messages.append(text)
        
        hmi.show_warning_message = Mock(side_effect=mock_show_warning_message)
        
        # Mock treatment_controller
        controller_mock = Mock()
        controller_calls = []
        def track_start_treatment():
            controller_calls.append(True)
            return True
        
        controller_mock.start_treatment = Mock(side_effect=track_start_treatment)
        hmi.treatment_controller = controller_mock
        
        # Mock screen_state_manager
        hmi.screen_state_manager = Mock()
        hmi.screen_state_manager.update_all_screens = Mock()
        
        # Lock for start_treatment
        hmi._start_treatment_locked = False
        
        # Mock FloatingConfirmDialog
        dialog_result = None
        confirm_calls = []
        
        def mock_show_confirm(text, accept_text="Iniciar", cancel_text="Cancelar"):
            confirm_calls.append({
                "text": text,
                "accept_text": accept_text,
                "cancel_text": cancel_text,
            })
            return dialog_result
        
        confirm_dialog_mock = Mock()
        confirm_dialog_mock.show_confirm = Mock(side_effect=mock_show_confirm)
        
        # Bind real start_treatment method to this mock
        from gui.appMainHemodialysis import HemodialysisHMI as RealHMI
        hmi.start_treatment = RealHMI.start_treatment.__get__(hmi, Mock)
        hmi._show_start_confirmation_dialog = RealHMI._show_start_confirmation_dialog.__get__(hmi, Mock)
        
        # Patch FloatingConfirmDialog at the module level for the call
        # We'll return the confirm_dialog_mock when FloatingConfirmDialog is instantiated
        hmi._confirm_dialog_mock = confirm_dialog_mock
        hmi._dialog_result = lambda: dialog_result
        hmi._set_dialog_result = lambda val: setattr(hmi, '_dialog_result_value', val) or setattr(confirm_dialog_mock.show_confirm, '_dialog_result', val)
        
        return hmi, controller_mock, warning_messages, confirm_dialog_mock, confirm_calls
    
    def test_ready_empty_dict_shows_warning_no_start(self):
        """
        READY phase, empty dict: no start_treatment call, warning contains 'flujo de sangre'.
        """
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict={}
        )
        
        # Patch FloatingConfirmDialog to ensure it's not created
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            hmi.start_treatment()
        
        # Verify no start_treatment call
        assert controller.start_treatment.call_count == 0
        
        # Verify warning shown with "flujo de sangre"
        assert len(warnings) > 0
        combined_warning = "\n".join(warnings)
        assert "flujo de sangre" in combined_warning.lower()
        
        # Verify FloatingConfirmDialog NOT created
        mock_dialog_class.assert_not_called()
    
    def test_ready_complete_data_cancel_no_start(self):
        """
        READY phase, complete data, heparin disabled, Cancel button: no start.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        hmi, controller, warnings, confirm, confirm_calls = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog to return False (Cancel)
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = False  # Cancel
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Verify no warning shown (data is complete)
        assert len(warnings) == 0
        
        # Verify FloatingConfirmDialog was created
        mock_dialog_class.assert_called_once()
        
        # Verify show_confirm was called
        mock_instance.show_confirm.assert_called_once()
        
        # Verify no start_treatment call (Cancel)
        assert controller.start_treatment.call_count == 0
    
    def test_ready_complete_data_confirm_starts_once(self):
        """
        READY phase, complete data, Iniciar button: start_treatment called once.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        hmi, controller, warnings, confirm, confirm_calls = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog to return True (Iniciar)
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = True  # Iniciar
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Verify no warning shown (data is complete)
        assert len(warnings) == 0
        
        # Verify FloatingConfirmDialog was created
        mock_dialog_class.assert_called_once()
        
        # Verify show_confirm was called
        mock_instance.show_confirm.assert_called_once()
        
        # Verify start_treatment was called exactly once
        assert controller.start_treatment.call_count == 1
        
        # Verify screen updates were called
        assert hmi.screen_state_manager.update_all_screens.call_count > 0
    
    def test_paused_empty_dict_starts_no_dialog(self):
        """
        PAUSED phase, empty dict: starts without validation, no dialog opened.
        """
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.PAUSED,
            values_dict={}
        )
        
        # Patch FloatingConfirmDialog to ensure it's not created
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            hmi.start_treatment()
        
        # Verify start_treatment was called (resuming)
        assert controller.start_treatment.call_count == 1
        
        # Verify no warning shown
        assert len(warnings) == 0
        
        # Verify FloatingConfirmDialog NOT created (no dialog for PAUSED)
        mock_dialog_class.assert_not_called()
    
    def test_ready_heparin_enabled_shows_syringe_in_dialog(self):
        """
        READY phase with heparin enabled: dialog shows syringe volume.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 1,
            "heparineSyringeVolume": 10,
        }
        
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = True
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Get the text passed to show_confirm
        call_args = mock_instance.show_confirm.call_args
        dialog_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        
        # Verify syringe volume is in the dialog text
        assert "jeringa" in dialog_text.lower()
        assert "10" in dialog_text
    
    def test_ready_uf_flow_conversion_in_dialog(self):
        """
        READY phase with UF flow: dialog shows converted L/h (mL/min * 60 / 1000).
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
            "ultraFilterPumpSpeed": 1000,  # 1000 mL/min = 60 L/h
        }
        
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = True
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Get the text passed to show_confirm
        call_args = mock_instance.show_confirm.call_args
        dialog_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        
        # Verify UF conversion: 1000 * 60 / 1000 = 60.0 L/h
        assert "60.0" in dialog_text or "60" in dialog_text
        assert "L/h" in dialog_text or "l/h" in dialog_text.lower()
    
    def test_running_phase_no_start(self):
        """
        RUNNING phase: immediately returns without calling start_treatment.
        """
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.RUNNING,
            values_dict={}
        )
        
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            hmi.start_treatment()
        
        # Verify no start_treatment call
        assert controller.start_treatment.call_count == 0
        
        # Verify no warning or dialog
        assert len(warnings) == 0
        mock_dialog_class.assert_not_called()
    
    def test_ready_missing_multiple_items_shows_all_warnings(self):
        """
        READY phase with multiple items missing: warning shows all missing items.
        """
        values = {
            "patient_id": "12345",
            # patient_name missing
            # bloodFlowControlSetPoint missing
            # balanceChamberSetTiming missing
            "dialyTempControlSetPoint": 37,
            # dialyCondControlSetPoint missing
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            hmi.start_treatment()
        
        # Verify no start_treatment call
        assert controller.start_treatment.call_count == 0
        
        # Verify warning contains multiple items
        combined_warning = "\n".join(warnings)
        assert "nombre del paciente" in combined_warning
        assert "flujo de sangre" in combined_warning.lower()
        assert "flujo de dializante" in combined_warning.lower()
        assert "conductividad" in combined_warning.lower()
        assert "tiempo de terapia" in combined_warning
        
        # Verify no dialog opened
        mock_dialog_class.assert_not_called()
    
    def test_dialog_shows_qd_as_programado(self):
        """
        Dialog shows Qd as 'Programado' without unit conversion.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = True
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Get the text passed to show_confirm
        call_args = mock_instance.show_confirm.call_args
        dialog_text = call_args[1]['text'] if 'text' in call_args[1] else call_args[0][0]
        
        # Verify Qd shown as "Programado"
        assert "Programado" in dialog_text
    
    def test_dialog_buttons_iniciar_cancelar(self):
        """
        Dialog buttons are labeled 'Iniciar' and 'Cancelar'.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 4,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        hmi, controller, warnings, confirm, _ = self._create_hmi_with_mocks(
            phase=TreatmentPhase.READY,
            values_dict=values
        )
        
        # Mock FloatingConfirmDialog
        with patch('gui.appMainHemodialysis.FloatingConfirmDialog') as mock_dialog_class:
            mock_instance = Mock()
            mock_instance.show_confirm.return_value = True
            mock_dialog_class.return_value = mock_instance
            
            hmi.start_treatment()
        
        # Get the button texts
        call_args = mock_instance.show_confirm.call_args
        accept_text = call_args[1].get('accept_text', 'Iniciar')
        cancel_text = call_args[1].get('cancel_text', 'Cancelar')
        
        # Verify button labels
        assert accept_text == "Iniciar"
        assert cancel_text == "Cancelar"

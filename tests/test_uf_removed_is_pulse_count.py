"""
Tests for UF Removed calculation based on pulse count only.

UF Removed does NOT depend on time. It is simply:
litros_removidos(pulsos) = round(pulsos × 0.94162 / 1000, 2)

UF Goal depends on pump speed and therapy duration:
uf_goal = ultraFilterPumpSpeed × (heparineTherapyHours + heparineTherapyMinutes/60)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget


def get_qapp():
    """Get or create QApplication singleton."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestUFRemovedVsPulseCount:
    """Test that UF Removed calculation depends only on pulse count."""

    def test_uf_removed_zero_pulses(self):
        """0 pulses → 0.00 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(0)
        assert result == 0.00

    def test_uf_removed_241_pulses(self):
        """241 pulses → 0.23 L
        
        This is the volume expected if there is one pulse every 3.4 seconds
        during 13 minutes 40 seconds.
        """
        from logic.uf_volume import litros_removidos
        result = litros_removidos(241)
        assert result == 0.23

    def test_uf_removed_366_pulses(self):
        """366 pulses → 0.34 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(366)
        assert result == 0.34

    def test_uf_removed_367_pulses(self):
        """367 pulses → 0.35 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(367)
        assert result == 0.35

    def test_uf_removed_372_pulses(self):
        """372 pulses → 0.35 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(372)
        assert result == 0.35

    def test_uf_removed_377_pulses(self):
        """377 pulses → 0.35 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(377)
        assert result == 0.35

    def test_uf_removed_378_pulses(self):
        """378 pulses → 0.36 L"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(378)
        assert result == 0.36

    def test_uf_removed_negative_pulses(self):
        """Negative pulses return 0.00"""
        from logic.uf_volume import litros_removidos
        result = litros_removidos(-100)
        assert result == 0.00


class TestUFGoalVsTherapyDuration:
    """Test that UF Goal depends on pump speed and therapy duration."""

    def test_uf_goal_calculation_1lh_40min(self):
        """1.00 L/h × (0 + 40/60) = 0.67 L"""
        pump_speed = 1.00  # L/h
        therapy_hours = 0
        therapy_minutes = 40
        therapy_duration = therapy_hours + (therapy_minutes / 60.0)
        uf_goal = pump_speed * therapy_duration
        assert round(uf_goal, 2) == 0.67

    def test_uf_goal_calculation_1lh_3hours(self):
        """1.00 L/h × 3 = 3.00 L"""
        pump_speed = 1.00
        therapy_hours = 3
        therapy_minutes = 0
        therapy_duration = therapy_hours + (therapy_minutes / 60.0)
        uf_goal = pump_speed * therapy_duration
        assert uf_goal == 3.00


class TestDialysisScreenUFRemoved:
    """Test UF Removed display in dialysis screen."""

    def _create_parent_widget(self):
        """Create a mock parent widget."""
        parent = QWidget()
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

    def test_dialysis_screen_uf_removed_fixed_pulse_count(self):
        """With ultraFilterCycleCount fixed at 372, UF Removed stays at 0.35 L.
        
        ultraFilterCycleCount: 372 pulses
        ultraFilterPumpSpeed: 1.00 L/h
        heparineTherapyHours: 0
        heparineTherapyMinutes: 40
        
        Expected:
        - UF Removida: 0.35 L (from 372 pulses)
        - Objetivo Total: 0.67 L (1.00 × (0 + 40/60))
        """
        from gui.therapy.dialysis_screenV2 import DialysisScreen

        get_qapp()

        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)

        # First update
        data = {
            "ultraFilterCycleCount": 372,
            "ultraFilterPumpSpeed": 1.00,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 40,
        }
        screen.update_values(data)

        # Check values
        uf_removed_text = screen.uf_rem_val.text()
        uf_goal_text = screen.uf_goal_val.text()

        assert "0.35" in uf_removed_text, f"Expected '0.35' in UF Removed, got '{uf_removed_text}'"
        assert "0.67" in uf_goal_text, f"Expected '0.67' in UF Goal, got '{uf_goal_text}'"

    def test_dialysis_screen_uf_removed_does_not_increment_on_repeat_update(self):
        """Repeating update_values with same pulse count does NOT increment UF Removed.
        
        The screen reads ultraFilterCycleCount and calls litros_removidos(372).
        If we call update_values again with the same value, UF Removed should still be 0.35 L.
        The screen does NOT integrate L/h over time.
        """
        from gui.therapy.dialysis_screenV2 import DialysisScreen

        get_qapp()

        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)

        data = {
            "ultraFilterCycleCount": 372,
            "ultraFilterPumpSpeed": 1.00,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 40,
        }

        # First update
        screen.update_values(data)
        uf_removed_first = screen.uf_rem_val.text()

        # Second update with same data
        screen.update_values(data)
        uf_removed_second = screen.uf_rem_val.text()

        # Should be identical
        assert uf_removed_first == uf_removed_second, \
            f"UF Removed should not change: first='{uf_removed_first}', second='{uf_removed_second}'"

        # Should still be 0.35 L
        assert "0.35" in uf_removed_second

    def test_dialysis_screen_uf_removed_changes_only_with_pulse_count(self):
        """UF Removed changes only when ultraFilterCycleCount changes.
        
        First: 372 pulses → 0.35 L
        Second: 378 pulses → 0.36 L (pulse count increased)
        Third: 378 pulses again → 0.36 L (no change)
        """
        from gui.therapy.dialysis_screenV2 import DialysisScreen

        get_qapp()

        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)

        base_data = {
            "ultraFilterPumpSpeed": 1.00,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 40,
        }

        # Update with 372 pulses
        data1 = {**base_data, "ultraFilterCycleCount": 372}
        screen.update_values(data1)
        uf_removed_1 = screen.uf_rem_val.text()
        assert "0.35" in uf_removed_1

        # Update with 378 pulses
        data2 = {**base_data, "ultraFilterCycleCount": 378}
        screen.update_values(data2)
        uf_removed_2 = screen.uf_rem_val.text()
        assert "0.36" in uf_removed_2

        # Update with 378 pulses again (same as previous)
        screen.update_values(data2)
        uf_removed_3 = screen.uf_rem_val.text()
        assert uf_removed_3 == uf_removed_2, "Should not change when pulse count doesn't change"
        assert "0.36" in uf_removed_3


class TestUFRemovedNoneHandling:
    """Test that None ultraFilterCycleCount is handled gracefully."""

    def _create_parent_widget(self):
        """Create a mock parent widget."""
        parent = QWidget()
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

    def test_dialysis_screen_handles_none_pulse_count(self):
        """None ultraFilterCycleCount should not crash and should default to 0.00 L."""
        from gui.therapy.dialysis_screenV2 import DialysisScreen

        get_qapp()

        parent_widget = self._create_parent_widget()
        screen = DialysisScreen(parent_widget)

        data = {
            "ultraFilterCycleCount": None,
            "ultraFilterPumpSpeed": 1.00,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 40,
        }

        # Should not raise
        screen.update_values(data)

        # UF Removed should be 0.00 L (None treated as 0)
        uf_removed_text = screen.uf_rem_val.text()
        assert "0.00" in uf_removed_text, f"Expected '0.00' for None pulse count, got '{uf_removed_text}'"

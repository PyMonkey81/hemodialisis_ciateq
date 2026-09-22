"""
Test module for therapy time UI synchronization fix.

Tests that changing therapy time in therapy_config_screen correctly updates:
1. T. RESTANTE header display
2. T. Terapia card
3. Profile calculations use live therapy duration

Acceptance criteria:
- Program 00:10 → T. RESTANTE shows 00:10:00 in LISTO (ready state)
- Start → T. RESTANTE decreases, T. Terapia increases
- Linear UF profile 1.5→0.5 at t=5 min → ~1.0 L/h (≈16.7 ml/min)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from core.treatment_controller import TreatmentController
from core.state_manager import TreatmentPhase
from logic.uf_profile import UFProfile, ProfileType, calculate_target_uf


class TestTherapyTimeChanges:
    """Test suite for therapy time changes and their effects."""

    def setup_method(self):
        """Set up mock main window and treatment controller."""
        self.main = Mock()
        self.main.current_values = {
            "heparineTherapyHours": 0.0,
            "heparineTherapyMinutes": 10.0,
        }
        self.main.state = Mock()
        self.main.state.current_phase = TreatmentPhase.PREPARING
        self.main.timer_manager = Mock()
        self.main.dialysis_screen = Mock()
        self.main.update_remaining_time_header = Mock()
        
        self.controller = TreatmentController(self.main)

    def test_get_programmed_total_seconds(self):
        """Verify programmed total is read from current_values."""
        # Test 00:10
        self.main.current_values["heparineTherapyHours"] = 0.0
        self.main.current_values["heparineTherapyMinutes"] = 10.0
        
        total = self.controller._get_programmed_total_seconds()
        assert total == 600, f"Expected 600 seconds (10 min), got {total}"

    def test_get_programmed_total_seconds_various_durations(self):
        """Test various therapy durations."""
        test_cases = [
            (0, 10, 600),       # 10 min
            (1, 0, 3600),       # 1 hour
            (3, 0, 10800),      # 3 hours (default)
            (2, 30, 9000),      # 2:30
        ]
        
        for hours, minutes, expected_seconds in test_cases:
            self.main.current_values["heparineTherapyHours"] = float(hours)
            self.main.current_values["heparineTherapyMinutes"] = float(minutes)
            
            total = self.controller._get_programmed_total_seconds()
            assert total == expected_seconds, \
                f"Expected {expected_seconds}s for {hours:02d}:{minutes:02d}, got {total}"

    def test_update_therapy_times_in_ready_state(self):
        """Verify therapy times are correctly displayed in READY state."""
        self.main.state.current_phase = TreatmentPhase.PREPARING
        self.main.current_values["heparineTherapyHours"] = 0.0
        self.main.current_values["heparineTherapyMinutes"] = 10.0
        
        self.controller.update_therapy_times()
        
        # Verify update_remaining_time_header was called with 00:10:00
        self.main.update_remaining_time_header.assert_called()
        call_args = self.main.update_remaining_time_header.call_args[0]
        remaining_str = call_args[0]
        
        assert remaining_str == "00:10:00", \
            f"Expected remaining '00:10:00', got '{remaining_str}'"
        
        # Verify dialysis_screen was updated with elapsed 00:00:00
        self.main.dialysis_screen.update_therapy_times.assert_called()
        elapsed_str, remaining_str = self.main.dialysis_screen.update_therapy_times.call_args[0]
        assert elapsed_str == "00:00:00"
        assert remaining_str == "00:10:00"

    def test_therapy_time_change_updates_displays(self):
        """Verify that changing therapy time updates all displays."""
        # Start in READY state with 00:10
        self.main.state.current_phase = TreatmentPhase.PREPARING
        self.main.current_values["heparineTherapyHours"] = 0.0
        self.main.current_values["heparineTherapyMinutes"] = 10.0
        
        # Call update_therapy_times
        self.controller.update_therapy_times()
        
        # Verify T. RESTANTE shows 00:10:00
        call_args = self.main.update_remaining_time_header.call_args[0]
        assert call_args[0] == "00:10:00"
        
        # Verify dialysis_screen shows T. Terapia = 00:00:00, T. Restante = 00:10:00
        elapsed_str, remaining_str = self.main.dialysis_screen.update_therapy_times.call_args[0]
        assert elapsed_str == "00:00:00"
        assert remaining_str == "00:10:00"

    def test_prepare_new_treatment_session_sets_total_correctly(self):
        """Verify new session sets total_therapy_seconds from current_values."""
        self.main.current_values["heparineTherapyHours"] = 0.0
        self.main.current_values["heparineTherapyMinutes"] = 10.0
        
        self.controller.prepare_new_treatment_session()
        
        assert self.controller.total_therapy_seconds == 600, \
            f"Expected 600s, got {self.controller.total_therapy_seconds}"

    def test_total_therapy_not_changed_during_running(self):
        """Verify total_therapy_seconds is NOT updated while RUNNING."""
        # Set up initial state with 10 min
        self.main.current_values["heparineTherapyHours"] = 0.0
        self.main.current_values["heparineTherapyMinutes"] = 10.0
        self.controller.total_therapy_seconds = 600
        
        # Simulate therapy running
        self.main.state.current_phase = TreatmentPhase.RUNNING
        
        # Try to update therapy times (simulating a time change during running)
        self.main.current_values["heparineTherapyMinutes"] = 20.0
        
        self.controller.update_therapy_times()
        
        # total_therapy_seconds should still be the original 600s
        # (not changed to 1200s from new 20 min value)
        # This is because update_therapy_times only reads from current_values
        # when NOT RUNNING/PAUSED
        assert self.controller.total_therapy_seconds == 600, \
            f"During RUNNING, total should stay 600s, but got {self.controller.total_therapy_seconds}"


class TestTherapyDurationInProfiles:
    """Test that profile calculations use live therapy duration."""

    def test_uf_profile_uses_current_therapy_duration(self):
        """Verify UF profile interpolation uses current therapy duration."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,  # JSON snapshot says 180
        )
        
        # User programs 10 min therapy, but JSON still says 180
        # At t=5 min (50% of real 10 min), output should be ~1.0 (middle value)
        result = calculate_target_uf(profile, elapsed_min=5.0, therapy_duration_min=10)
        
        assert result is not None
        assert abs(result - 1.0) < 0.01, \
            f"At 50% of 10-min therapy, expected ~1.0 L/h, got {result}"

    def test_uf_profile_ml_per_min_conversion(self):
        """Verify 1.0 L/h ≈ 16.7 ml/min."""
        from logic.calculos import convertir_litros_h_a_ml_min
        
        ml_min = convertir_litros_h_a_ml_min(1.0)
        
        # 1.0 L/h = 1000 ml/60 min = 16.666... ml/min
        assert abs(ml_min - 16.666666) < 0.1, \
            f"Expected ~16.67 ml/min, got {ml_min}"

    def test_full_profile_calculation_chain_10min_therapy(self):
        """Full chain: 10min therapy, linear 1.5→0.5, at t=5min."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,  # JSON snapshot
        )
        
        # Real therapy is 10 min
        therapy_duration_min = 10.0
        elapsed_min = 5.0
        
        # Calculate target UF with real duration
        target_uf = calculate_target_uf(profile, elapsed_min, therapy_duration_min)
        
        # Convert to ml/min
        from logic.calculos import convertir_litros_h_a_ml_min
        target_ml_min = convertir_litros_h_a_ml_min(target_uf)
        
        # At 5 min (50% of 10 min), UF should be ~1.0 L/h ≈ 16.7 ml/min
        assert abs(target_uf - 1.0) < 0.01, \
            f"Expected target_uf ~1.0 L/h at 50%, got {target_uf}"
        assert abs(target_ml_min - 16.67) < 0.5, \
            f"Expected target_ml_min ~16.67 ml/min, got {target_ml_min}"

    def test_linear_profile_never_plateaus_with_real_duration(self):
        """Verify linear profile never plateaus when using real therapy duration."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,  # JSON says 180
        )
        
        # Real therapy is 10 min
        therapy_duration_min = 10.0
        
        # Check at several time points
        times = [0.0, 2.5, 5.0, 7.5, 10.0]
        results = []
        
        for t in times:
            val = calculate_target_uf(profile, elapsed_min=t, therapy_duration_min=therapy_duration_min)
            assert val is not None
            results.append(val)
        
        # Verify monotonic decrease
        for i in range(len(results) - 1):
            assert results[i] >= results[i + 1], \
                f"Values not decreasing: {results[i]} >= {results[i + 1]} at times {times[i]}, {times[i + 1]}"
        
        # Verify end value is 0.5, not hit earlier
        assert abs(results[-1] - 0.5) < 0.01, \
            f"At end (t=10), should be 0.5, got {results[-1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

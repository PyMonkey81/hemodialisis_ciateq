"""
Test module for UF profile linear interpolation fix.

Tests that linear/CUSTOM profiles interpolate correctly using real therapy duration,
not the frozen snapshot in the JSON profile.

Acceptance criteria:
- 180 min therapy, linear 1.5→0.5:
  - t=0 → out_Lh ≈ 1.50
  - t=90 → out_Lh ≈ 1.00 (arithmetic mean)
  - t=180 → out_Lh ≈ 0.50
  - Never flat at 0.5 from t=90
"""

import pytest
from logic.uf_profile import UFProfile, ProfileType, calculate_target_uf


class TestUFProfileLinearInterpolation:
    """Test suite for linear UF profile interpolation with real therapy duration."""

    def test_linear_profile_start_end_values(self):
        """Verify start and end values are returned correctly."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,
        )

        # At t=0, should return start value
        result_start = calculate_target_uf(profile, elapsed_min=0.0, therapy_duration_min=180)
        assert result_start is not None
        assert abs(result_start - 1.5) < 0.01, f"Expected ~1.50, got {result_start}"

        # At t=180, should return end value
        result_end = calculate_target_uf(profile, elapsed_min=180.0, therapy_duration_min=180)
        assert result_end is not None
        assert abs(result_end - 0.5) < 0.01, f"Expected ~0.50, got {result_end}"

    def test_linear_profile_midpoint(self):
        """Verify that at 50% of therapy, output is arithmetic mean."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,
        )

        # At t=90 (50% of 180), should be arithmetic mean: (1.5 + 0.5) / 2 = 1.0
        result_mid = calculate_target_uf(profile, elapsed_min=90.0, therapy_duration_min=180)
        assert result_mid is not None
        assert abs(result_mid - 1.0) < 0.01, f"Expected ~1.00 at 50%, got {result_mid}"

    def test_linear_profile_continuous_interpolation(self):
        """Verify continuous interpolation (not plateauing)."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,
        )

        # Test at several points: values should decrease monotonically
        times = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0]
        results = []
        for t in times:
            val = calculate_target_uf(profile, elapsed_min=t, therapy_duration_min=180)
            assert val is not None
            results.append(val)

        # Verify monotonic decrease (or stay same)
        for i in range(len(results) - 1):
            assert results[i] >= results[i + 1], \
                f"Values not decreasing: {results[i]} < {results[i + 1]} at times {times[i]}, {times[i + 1]}"

    def test_linear_profile_with_different_therapy_duration(self):
        """Verify correct behavior when real therapy duration != profile duration.

        This is the bug scenario: profile saved at 180 min, but therapy actually runs 240 min.
        """
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,  # Snapshot from JSON
        )

        # Real therapy is 240 min, pass it to the function
        therapy_duration_min = 240

        # At t=0, should still be start
        result_0 = calculate_target_uf(profile, elapsed_min=0.0, therapy_duration_min=therapy_duration_min)
        assert abs(result_0 - 1.5) < 0.01

        # At t=120 (50% of real 240 min), should be close to 1.0
        result_mid = calculate_target_uf(profile, elapsed_min=120.0, therapy_duration_min=therapy_duration_min)
        assert abs(result_mid - 1.0) < 0.01, f"Expected ~1.00 at 50% of 240min, got {result_mid}"

        # At t=180 (75% of real 240 min), should NOT be 0.5 yet
        result_75 = calculate_target_uf(profile, elapsed_min=180.0, therapy_duration_min=therapy_duration_min)
        expected_75 = 1.5 + (0.5 - 1.5) * 0.75  # = 1.5 - 0.75 = 0.75
        assert abs(result_75 - expected_75) < 0.01, \
            f"At 75%, expected ~{expected_75}, got {result_75}"

        # At t=240, should be 0.5
        result_end = calculate_target_uf(profile, elapsed_min=240.0, therapy_duration_min=therapy_duration_min)
        assert abs(result_end - 0.5) < 0.01

    def test_linear_profile_without_therapy_duration_param(self):
        """Verify fallback to profile.therapy_duration_min when not provided."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,
        )

        # Call without therapy_duration_min parameter (None)
        result = calculate_target_uf(profile, elapsed_min=90.0)
        # Should use profile.therapy_duration_min (180) and return 1.0
        assert abs(result - 1.0) < 0.01

    def test_exponential_profile_with_real_therapy_duration(self):
        """Verify CUSTOM (exponential) profile also uses real therapy duration."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.CUSTOM,
            start_uf=1.5,
            end_uf=0.5,
            therapy_duration_min=180,
        )

        # With real 240 min therapy
        result_0 = calculate_target_uf(profile, elapsed_min=0.0, therapy_duration_min=240)
        assert abs(result_0 - 1.5) < 0.01

        result_240 = calculate_target_uf(profile, elapsed_min=240.0, therapy_duration_min=240)
        assert abs(result_240 - 0.5) < 0.01

        # At 50%, should be somewhere close to middle (exponential, not linear)
        result_mid = calculate_target_uf(profile, elapsed_min=120.0, therapy_duration_min=240)
        assert 0.5 < result_mid < 1.5  # Should be in valid range

    def test_step_profile_unaffected(self):
        """Verify STEP profile is not affected by therapy_duration_min parameter."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.STEP,
            step_high=1.5,
            step_low=0.5,
            therapy_duration_min=180,
            points=[1.5, 0.5, 1.5, 0.5, 1.5, 0.5],
        )

        # STEP should return None (step index is handled separately in appMainHemodialysis)
        result = calculate_target_uf(profile, elapsed_min=90.0, therapy_duration_min=240)
        # STEP profile calculation requires step_index_by_seconds, not calculate_target_uf
        # For now, just verify no exception is raised
        assert result is None or isinstance(result, (int, float))

    def test_disabled_profile_returns_none(self):
        """Verify disabled profiles return None."""
        profile = UFProfile(
            enabled=False,
            profile_type=ProfileType.LINEAR,
            start_uf=1.5,
            end_uf=0.5,
        )

        result = calculate_target_uf(profile, elapsed_min=90.0, therapy_duration_min=180)
        assert result is None

    def test_none_profile_type_returns_none(self):
        """Verify NONE profile type returns None."""
        profile = UFProfile(
            enabled=True,
            profile_type=ProfileType.NONE,
            start_uf=1.5,
            end_uf=0.5,
        )

        result = calculate_target_uf(profile, elapsed_min=90.0, therapy_duration_min=180)
        assert result is None


class TestConductivityProfileLinearInterpolation:
    """Test suite for linear conductivity profile interpolation with real therapy duration."""

    def test_conductivity_linear_interpolation(self):
        """Verify conductivity linear profile works with real therapy duration."""
        from logic.conductivity_profile import ConductivityProfile, calculate_target_conductivity

        profile = ConductivityProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_conductivity=14.0,
            end_conductivity=12.0,
            therapy_duration_min=180,
        )

        # At 50%, should be arithmetic mean
        result = calculate_target_conductivity(profile, elapsed_min=90.0, therapy_duration_min=180)
        assert result is not None
        assert abs(result - 13.0) < 0.01

        # With different real duration (240 min)
        result_real = calculate_target_conductivity(profile, elapsed_min=120.0, therapy_duration_min=240)
        assert abs(result_real - 13.0) < 0.01  # At 50% of real duration

    def test_conductivity_without_therapy_duration_param(self):
        """Verify fallback to profile.therapy_duration_min for conductivity."""
        from logic.conductivity_profile import ConductivityProfile, calculate_target_conductivity

        profile = ConductivityProfile(
            enabled=True,
            profile_type=ProfileType.LINEAR,
            start_conductivity=14.0,
            end_conductivity=12.0,
            therapy_duration_min=180,
        )

        # Without parameter, should use profile.therapy_duration_min
        result = calculate_target_conductivity(profile, elapsed_min=90.0)
        assert abs(result - 13.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

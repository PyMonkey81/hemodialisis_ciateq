"""
Tests for start checklist validation logic.

Tests the pure function missing_start_items() with various scenarios.
"""

import pytest
from logic.start_checklist import missing_start_items


class TestStartChecklist:
    """Tests for missing_start_items validation function."""
    
    def test_empty_dict_returns_all_missing_items(self):
        """Empty dict should return all 8 missing items."""
        result = missing_start_items({})
        
        expected = [
            "Falta el paciente",
            "Falta el nombre del paciente",
            "Falta el flujo de sangre (Qb)",
            "Falta el flujo de dializante (Qd)",
            "Falta la temperatura",
            "Falta la conductividad",
            "Falta el tiempo de terapia",
            "Falta el volumen de heparina en la jeringa",
        ]
        
        assert result == expected
    
    def test_complete_valid_setup_with_heparin_disabled(self):
        """
        Complete setup with valid values and heparin disabled.
        Should return empty list (no missing items).
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert result == []
    
    def test_heparin_enabled_with_zero_syringe_volume(self):
        """
        Heparin enabled, syringe volume is 0.
        Should return ONLY the syringe volume missing item.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 1,
            "heparineSyringeVolume": 0,
        }
        
        result = missing_start_items(values)
        assert result == ["Falta el volumen de heparina en la jeringa"]
    
    def test_heparin_enabled_with_none_syringe_volume(self):
        """
        Heparin enabled (1), syringe volume is None.
        Should return ONLY the syringe volume missing item.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 1,
            "heparineSyringeVolume": None,
        }
        
        result = missing_start_items(values)
        assert result == ["Falta el volumen de heparina en la jeringa"]
    
    def test_heparin_enabled_default_with_zero_syringe_volume(self):
        """
        Heparin enabled (default/None counts as enabled), syringe volume is 0.
        Should return ONLY the syringe volume missing item.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            # heparineInfusionEnabled not provided (defaults to None, which means enabled)
            "heparineSyringeVolume": 0,
        }
        
        result = missing_start_items(values)
        assert result == ["Falta el volumen de heparina en la jeringa"]
    
    def test_heparin_disabled_ignores_syringe_volume(self):
        """
        Heparin disabled (0), syringe volume missing.
        Should NOT require syringe volume check.
        """
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
            # heparineSyringeVolume not provided
        }
        
        result = missing_start_items(values)
        assert result == []
    
    def test_missing_patient_id(self):
        """Patient ID is missing/empty."""
        values = {
            "patient_id": "",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el paciente" in result
    
    def test_missing_patient_name(self):
        """Patient name is missing/empty."""
        values = {
            "patient_id": "12345",
            "patient_name": None,
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el nombre del paciente" in result
    
    def test_zero_blood_flow(self):
        """Blood flow (Qb) is zero."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 0,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el flujo de sangre (Qb)" in result
    
    def test_negative_blood_flow(self):
        """Blood flow (Qb) is negative."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": -100,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el flujo de sangre (Qb)" in result
    
    def test_zero_dialysate_flow(self):
        """Dialysate flow (Qd) is zero."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 0,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el flujo de dializante (Qd)" in result
    
    def test_zero_temperature(self):
        """Temperature is zero."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 0,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta la temperatura" in result
    
    def test_zero_conductivity(self):
        """Conductivity is zero."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 0,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta la conductividad" in result
    
    def test_zero_therapy_time_hours_and_minutes(self):
        """Therapy time is 0:00 (zero hours and zero minutes)."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el tiempo de terapia" in result
    
    def test_valid_therapy_time_hours_only(self):
        """Therapy time has hours (minutes can be 0)."""
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
        
        result = missing_start_items(values)
        assert "Falta el tiempo de terapia" not in result
    
    def test_valid_therapy_time_minutes_only(self):
        """Therapy time has minutes (hours can be 0)."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 0,
            "heparineTherapyMinutes": 30,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el tiempo de terapia" not in result
    
    def test_missing_patient_id_not_in_dict(self):
        """patient_id key not in dict at all."""
        values = {
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el paciente" in result
    
    def test_validation_order(self):
        """Verify items are returned in the correct validation order."""
        values = {
            # patient_id missing
            # patient_name missing
            # bloodFlowControlSetPoint missing
            # balanceChamberSetTiming missing
            # dialyTempControlSetPoint missing
            # dialyCondControlSetPoint missing
            # heparineTherapyHours/Minutes = 0:00
            # heparineSyringeVolume missing (heparin enabled)
        }
        
        result = missing_start_items(values)
        
        expected_order = [
            "Falta el paciente",
            "Falta el nombre del paciente",
            "Falta el flujo de sangre (Qb)",
            "Falta el flujo de dializante (Qd)",
            "Falta la temperatura",
            "Falta la conductividad",
            "Falta el tiempo de terapia",
            "Falta el volumen de heparina en la jeringa",
        ]
        
        assert result == expected_order
    
    def test_multiple_missing_items(self):
        """Missing multiple items shows all in correct order."""
        values = {
            "patient_id": "12345",
            # patient_name missing
            "bloodFlowControlSetPoint": 250,
            # balanceChamberSetTiming missing
            "dialyTempControlSetPoint": 37,
            # dialyCondControlSetPoint missing
            # heparineTherapyHours/Minutes = 0:00
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        
        expected = [
            "Falta el nombre del paciente",
            "Falta el flujo de dializante (Qd)",
            "Falta la conductividad",
            "Falta el tiempo de terapia",
        ]
        
        assert result == expected
    
    def test_therapy_time_with_non_numeric_values(self):
        """Therapy time with non-numeric values should be treated as 0."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": "invalid",
            "heparineTherapyMinutes": "also_invalid",
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el tiempo de terapia" in result
    
    def test_blood_flow_missing_from_dict(self):
        """Blood flow key not in dict."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            # bloodFlowControlSetPoint missing
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
        }
        
        result = missing_start_items(values)
        assert "Falta el flujo de sangre (Qb)" in result
    
    def test_heparin_with_valid_syringe_volume(self):
        """Heparin enabled with valid syringe volume."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 1,
            "heparineSyringeVolume": 10,
        }
        
        result = missing_start_items(values)
        assert result == []
    
    def test_zero_uf_flow_is_valid(self):
        """UF flow of 0 L/h should be valid (no UF requirement)."""
        values = {
            "patient_id": "12345",
            "patient_name": "Juan Pérez",
            "bloodFlowControlSetPoint": 250,
            "balanceChamberSetTiming": 500,
            "dialyTempControlSetPoint": 37,
            "dialyCondControlSetPoint": 14,
            "heparineTherapyHours": 1,
            "heparineTherapyMinutes": 0,
            "heparineInfusionEnabled": 0,
            "ultraFilterPumpSpeed": 0,  # 0 L/h is valid
        }
        
        result = missing_start_items(values)
        assert result == []

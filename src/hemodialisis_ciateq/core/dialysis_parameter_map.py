# core/dialysis_parameter_map.py
from typing import Dict, List, Tuple, Any

# ==============================================================================
# COMPREHENSIVE DEVICE PARAMETER MAP - HEMODIALYSIS SYSTEM
#
# This map defines all configurable and measurable parameters within the
# hemodialysis machine's control system. It adheres to medical device software
# development best practices (e.g., IEC 62304) and alarm system standards
# (e.g., IEC 60601-1-8) by classifying parameters by data type, access mode,
# and alarm priority.
#
# Key definitions:
#   - 'parameter_name': User-friendly name for display in the Clinical GUI.
#   - 'data_type': Python type representation ("bool", "double").
#   - 'access_mode': 'True' for Read/Write (e.g., setpoints, control commands),
#                    'False' for Read-Only (e.g., sensor readings, status indicators).
#   - 'unit': Engineering unit (e.g., "mmHg", "ml/min", "°C").
#   - 'alarm_limits': Tuple (lower_limit, upper_limit) for numeric parameters,
#                     used for alarm condition evaluation.
#   - 'priority': Alarm priority level if the parameter triggers an alarm:
#                 "High" (Red - Immediate action required),
#                 "Medium" (Yellow - Prompt attention required),
#                 "Low" (Cyan - Operator awareness required).
#   - 'device_tag': Unique identifier for internal system referencing (e.g., Modbus tag).
#   - 'id': Internal numerical identifier within its address block.
# ==============================================================================

DIALYSIS_PARAMETERS: Dict[int, Dict[int, Dict[str, Any]]] = {

    # ==========================================================================
    # OPERATIONAL BOOLEANS (0x01) - 60 variables (0x00 to 0x3B)
    # ==========================================================================
    0x01: {
        **{i: {"parameter_name": name, "data_type": "bool", "access_mode": access_mode, "priority": priority, "device_tag": tag, "id": i}
            for i, (name, priority, tag, access_mode) in enumerate([
                # --- CONTROL COMMANDS (Read/Write) - ID 0 to 40 (access_mode=True) ---
                ("Blood Pump Start", "Low", "bloodPumpStartCommand", True),                   # 0
                ("Blood Pump Stop", "Low", "bloodPumpStopCommand", True),                     # 1
                ("Blood Pump Forward", "Low", "bloodPumpFwdCommand", True),                   # 2
                ("Blood Pump Reverse", "Low", "bloodPumpRevCommand", True),                   # 3
                ("Dialysate Purge Pump Start", "Low", "dialysatePurgePumpStartCommand", True),# 4
                ("Dialysate Purge Pump Stop", "Low", "dialysatePurgePumpStopCommand", True),  # 5
                ("Heparin Pump Start", "Low", "heparinPumpStartCommand", True),               # 6
                ("Heparin Pump Stop", "Low", "heparinPumpStopCommand", True),                 # 7
                ("Heparin Pump Forward", "Low", "heparinPumpFwdCommand", True),               # 8
                ("Heparin Pump Reverse", "Low", "heparinPumpRevCommand", True),               # 9
                ("Blood Flow Control Enable", "Low", "bloodFlowControlEnable", True),         # 10
                ("Blood Flow Control Mode (Auto/Manual)", "Low", "bloodFlowControlMode", True), # 11
                ("Dialysate Conductivity Control Enable", "Low", "dialysateCondControlEnable", True), # 12
                ("Dialysate Conductivity Control Mode (Auto/Manual)", "Low", "dialysateCondControlMode", True), # 13
                ("Dialysate Temperature Control Enable", "Low", "dialysateTempControlEnable", True), # 14
                ("Dialysate Temperature Control Mode (Auto/Manual)", "Low", "dialysateTempControlMode", True), # 15
                ("Heparin Pump Home Position", "Low", "heparinPumpHomeCommand", True),        # 16
                ("Balance Chamber Start Cycle", "Low", "balanceChamberStartCycle", True),     # 17
                ("Balance Chamber Stop Cycle", "Low", "balanceChamberStopCycle", True),       # 18
                ("Administer Heparin Bolus", "Low", "heparinApplyBolusCommand", True),        # 19
                ("Treatment Pause/Resume", "Low", "treatmentPauseResume", True),              # 20
                ("Dialysate Circuit Elements Operation Select", "Low", "dialysateCircuitOpSelect", True), # 21
                ("Dialysate Pump Start", "Low", "dialysatePumpStartCommand", True),           # 22 (Corrected from Purge to Dialysate Pump)
                ("Dialysate Pump Stop", "Low", "dialysatePumpStopCommand", True),             # 23 (Corrected from Purge to Dialysate Pump)
                ("Ultrafiltration Pump Start", "Low", "ultrafiltrationPumpStartCommand", True),# 24
                ("Ultrafiltration Pump Stop", "Low", "ultrafiltrationPumpStopCommand", True), # 25
                ("Bicarbonate Pump Start", "Low", "bicarbonatePumpStartCommand", True),       # 26
                ("Bicarbonate Pump Stop", "Low", "bicarbonatePumpStopCommand", True),         # 27
                ("Acid Pump Start", "Low", "acidPumpStartCommand", True),                     # 28
                ("Acid Pump Stop", "Low", "acidPumpStopCommand", True),                       # 29
                ("Water Inlet Valve Activate", "Low", "waterInletValveCommand", True),        # 30
                ("Recirculation Valve Activate", "Low", "recirculationValveCommand", True),   # 31
                ("Hot Chamber Valve Activate", "Low", "hotChamberValveCommand", True),        # 32
                ("Air Vent Valve Activate", "Low", "airVentValveCommand", True),              # 33
                ("Dialyzer Bypass Valve Activate", "Low", "dialyzerBypassValveCommand", True),# 34
                ("Dialyzer Inlet Isolation Valve Activate", "Low", "dialyzerInletValveCommand", True), # 35
                ("Dialyzer Outlet Isolation Valve Activate", "Low", "dialyzerOutletValveCommand", True), # 36
                ("Drain Valve Activate", "Low", "drainValveCommand", True),                   # 37
                ("Balance Chamber Cycle End Status", "Medium", "balanceChamberCycleEnd", True), # 38 (Status but might be resettable)
                ("Start Dialysis Treatment", "Low", "startDialysisCommand", True),            # 39
                ("Stop Dialysis Treatment", "Low", "stopDialysisCommand", True),              # 40

                # --- STATUS INDICATORS (Read-Only) - ID 41 to 59 (access_mode=False) ---
                ("Heater Element Overheat Protection Status", "High", "heaterOverheatProtectStatus", False),# 41
                ("Auxiliary Digital Input 3 Status", "Low", "auxDigitalInput1Status", False), # 42
                ("Auxiliary Digital Input 4 Status", "Low", "auxDigitalInput2Status", False), # 43
                ("Auxiliary Digital Input 5 Status", "Low", "auxDigitalInput3Status", False), # 44
                ("Auxiliary Digital Input 6 Status", "Low", "auxDigitalInput4Status", False), # 45
                ("Auxiliary Digital Input 7 Status", "Low", "auxDigitalInput5Status", False), # 46
                ("Auxiliary Digital Input 8 Status", "Low", "auxDigitalInput6Status", False), # 47
                ("Bloodline Air Bubble Detector Status", "High", "airBubbleDetectorStatus", False), # 48
                ("Blood Leak Detector Status", "High", "bloodLeakDetectorStatus", False),     # 49
                ("Water Tank High Level Switch Status", "Medium", "waterTankHiLevelStatus", False), # 50
                ("Deaeration Chamber Level Switch Status", "Medium", "deaerationChamberLevelStatus", False), # 51
                ("Auxiliary Digital Input 11 Status", "Low", "auxDigitalInput7Status", False), # 52
                ("Auxiliary Digital Input 12 Status", "Low", "auxDigitalInput8Status", False), # 53
                ("Auxiliary Digital Input 13 Status", "Low", "auxDigitalInput9Status", False), # 54
                ("Auxiliary Digital Input 14 Status", "Low", "auxDigitalInput10Status", False),# 55
                ("Auxiliary Digital Input 15 Status", "Low", "auxDigitalInput11Status", False),# 56
                ("Auxiliary Digital Input 16 Status", "Low", "auxDigitalInput12Status", False),# 57
                ("Auxiliary Digital Input 17 Status", "Low", "auxDigitalInput13Status", False),# 58
                ("Auxiliary Digital Input 18 Status", "Low", "auxDigitalInput14Status", False),# 59
            ], start=0)}
    },

    # ==========================================================================
    # CLINICAL PARAMETERS (0x02) - Patient-related and key system data
    # ==========================================================================
    0x02: {
        0x00: {"parameter_name": "Transmembrane Pressure (TMP)", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (1, 100), "device_tag": "transmembranePressure", "priority": "Low"},             # 0
        0x01: {"parameter_name": "Treatment Mode Selection", "data_type": "double", "access_mode": True, "unit": "N/A", "alarm_limits": (0, 100), "device_tag": "treatmentModeSelection", "priority": "Low"},   # 1
        0x02: {"parameter_name": "Priming Process Status", "data_type": "double", "access_mode": True, "unit": "N/A", "alarm_limits": (0, 100), "device_tag": "primingProcessStatus", "priority": "Low"},    # 2
        0x03: {"parameter_name": "Auxiliary Clinical Display 3", "data_type": "double", "access_mode": True, "unit": "N/A", "alarm_limits": (0, 100), "device_tag": "auxClinicalDisplay3", "priority": "Low"},    # 3
        0x04: {"parameter_name": "Balance Chamber Cycles Setpoint", "data_type": "double", "access_mode": True, "unit": "cycles", "alarm_limits": (1, 100), "device_tag": "balanceChamberCycleSetpoint", "priority": "Low"},   # 4
        0x05: {"parameter_name": "Current Heparin Delivered Volume", "data_type": "double", "access_mode": True, "unit": "mL", "alarm_limits": (0, 100), "device_tag": "heparinCurrentDeliveredVolume", "priority": "Low"},  # 5
        0x06: {"parameter_name": "Balance Chamber Cycle Count", "data_type": "double", "access_mode": True, "unit": "cycles", "alarm_limits": (0, 10000), "device_tag": "balanceChamberCycleCount", "priority": "Low"}, # 6
    },


    # ==========================================================================
    # SYSTEM SETPOINTS (0x03) - Configurable operational values
    # ==========================================================================
    0x03: {
        0x00: {"parameter_name": "Ultrafiltration Rate Setpoint", "data_type": "double", "access_mode": True, "unit": "mL/hr", "alarm_limits": (0, 5000), "device_tag": "ultrafiltrationRateSetpoint", "priority": "Low"},              # 7
        0x01: {"parameter_name": "Balance Chamber Cycle Time Setpoint", "data_type": "double", "access_mode": True, "unit": "s", "alarm_limits": (0, 100), "device_tag": "balanceChamberTimeSetpoint", "priority": "Low"}, # 8
        0x02: {"parameter_name": "Heparin Therapy Duration (Hours)", "data_type": "double", "access_mode": True, "unit": "h", "alarm_limits": (0, 10), "device_tag": "heparinTherapyHoursSetpoint", "priority": "Low"},                    # 9
        0x03: {"parameter_name": "Heparin Therapy Duration (Minutes)", "data_type": "double", "access_mode": True, "unit": "min", "alarm_limits": (0, 59), "device_tag": "heparinTherapyMinutesSetpoint", "priority": "Low"},               # 10
        0x04: {"parameter_name": "Heparin Syringe Scale Size (Calibration)", "data_type": "double", "access_mode": True, "unit": "mm/mL", "alarm_limits": (1, 10), "device_tag": "heparinSyringeScaleCal", "priority": "Low"},      # 11
        0x05: {"parameter_name": "Heparin Infusion Rate Setpoint", "data_type": "double", "access_mode": True, "unit": "mL/hr", "alarm_limits": (0, 50), "device_tag": "heparinInfusionRateSetpoint", "priority": "Low"},   # 12
        0x06: {"parameter_name": "Heparin Bolus Volume Setpoint", "data_type": "double", "access_mode": True, "unit": "mL", "alarm_limits": (0, 10), "device_tag": "heparinBolusVolumeSetpoint", "priority": "Low"},                       # 13
        0x07: {"parameter_name": "Bicarbonate Pump Flow Setpoint", "data_type": "double", "access_mode": True, "unit": "%", "alarm_limits": (0, 100), "device_tag": "bicarbonatePumpFlowSetpoint", "priority": "Low"},# 14
        0x08: {"parameter_name": "Acid Pump Flow Setpoint", "data_type": "double", "access_mode": True, "unit": "%", "alarm_limits": (0, 100), "device_tag": "acidPumpFlowSetpoint", "priority": "Low"},     # 15
    },

    # ==========================================================================
    # CONTROL LOOP PARAMETERS (0x04) - PID and feedforward tuning parameters
    # ==========================================================================
    0x04: {
        0x00: {"parameter_name": "Blood Flow PID Setpoint", "data_type": "double", "access_mode": True, "unit": "mL/min", "alarm_limits": (0, 600), "device_tag": "bloodFlowPidSetpoint", "priority": "Low"},        # 16   0
        0x01: {"parameter_name": "Blood Flow Process Variable", "data_type": "double", "access_mode": True, "unit": "mL/min", "alarm_limits": (0, 600), "device_tag": "bloodFlowProcessVariable", "priority": "Low"},   # 17   1 
        0x02: {"parameter_name": "Blood Flow Control Output", "data_type": "double", "access_mode": True, "unit": "%", "alarm_limits": (0, 100), "device_tag": "bloodFlowControlOutput", "priority": "Low"},         # 18   2
        0x03: {"parameter_name": "Blood Flow PID Proportional Gain (Kp)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "bloodFlowPidKp", "priority": "Low"},          # 19   3 
        0x04: {"parameter_name": "Blood Flow PID Integral Gain (Ki)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "bloodFlowPidKi", "priority": "Low"},          # 20   4
        0x05: {"parameter_name": "Blood Flow PID Derivative Gain (Kd)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "bloodFlowPidKd", "priority": "Low"},          # 21   5
        0x06: {"parameter_name": "Dialysate Conductivity PID Setpoint", "data_type": "double", "access_mode": True, "unit": "mS/cm", "alarm_limits": (13.0, 15.0), "device_tag": "dialysateCondPidSetpoint", "priority": "Low"},       # 22   6
        0x07: {"parameter_name": "Dialysate Conductivity Process Variable", "data_type": "double", "access_mode": False, "unit": "mS/cm", "alarm_limits": (12.5, 15.5), "device_tag": "dialysateCondProcessVariable", "priority": "Medium"},       # 23   7
        0x08: {"parameter_name": "Dialysate Conductivity Control Output", "data_type": "double", "access_mode": False, "unit": "%", "alarm_limits": (0, 100), "device_tag": "dialysateCondControlOutput", "priority": "Low"},       # 24   8
        0x09: {"parameter_name": "Dialysate Conductivity PID Proportional Gain (Kp)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateCondPidKp", "priority": "Low"},            # 25   9
        0x0A: {"parameter_name": "Dialysate Conductivity PID Integral Gain (Ki)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateCondPidKi", "priority": "Low"},            # 26   10
        0x0B: {"parameter_name": "Dialysate Conductivity PID Derivative Gain (Kd)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateCondPidKd", "priority": "Low"},            # 27   11  
        0x0C: {"parameter_name": "Dialysate Temperature PID Setpoint", "data_type": "double", "access_mode": True, "unit": "°C", "alarm_limits": (35.0, 39.0), "device_tag": "dialysateTempPidSetpoint", "priority": "Low"},            # 28   12 
        0x0D: {"parameter_name": "Dialysate Temperature Process Variable", "data_type": "double", "access_mode": False, "unit": "°C", "alarm_limits": (34.5, 39.5), "device_tag": "dialysateTempProcessVariable", "priority": "Medium"},            # 29   13
        0x0E: {"parameter_name": "Dialysate Temperature Control Output", "data_type": "double", "access_mode": False, "unit": "%", "alarm_limits": (0, 100), "device_tag": "dialysateTempControlOutput", "priority": "Low"},            # 30   14 
        0x0F: {"parameter_name": "Dialysate Temperature PID Proportional Gain (Kp)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateTempPidKp", "priority": "Low"},                 # 31   15
        0x10: {"parameter_name": "Dialysate Temperature PID Integral Gain (Ki)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateTempPidKi", "priority": "Low"},                 # 32   16
        0x11: {"parameter_name": "Dialysate Temperature PID Derivative Gain (Kd)", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 10), "device_tag": "dialysateTempPidKd", "priority": "Low"},                 # 33   17
        0x12: {"parameter_name": "Blood Flow Feedforward Gain", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 5), "device_tag": "bloodFlowFeedforwardGain", "priority": "Low"},              # 34   18
        0x13: {"parameter_name": "Blood Flow Feedforward Lead Time", "data_type": "double", "access_mode": True, "unit": "s", "alarm_limits": (0, 10), "device_tag": "bloodFlowFeedforwardLeadTime", "priority": "Low"},     # 35   19
        0x14: {"parameter_name": "Dialysate Flow Rate Setpoint", "data_type": "double", "access_mode": True, "unit": "mL/min", "alarm_limits": (300, 800), "device_tag": "dialysateFlowSetpoint", "priority": "Low"},       # 36   20
        0x15: {"parameter_name": "Deaeration Pump Control Output", "data_type": "double", "access_mode": False, "unit": "%", "alarm_limits": (0, 100), "device_tag": "deaerationPumpControlOutput", "priority": "Low"},                # 37   21  
        0x16: {"parameter_name": "Auxiliary Control Parameter 1", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParam1", "priority": "Low"},           # 38   22
        0x17: {"parameter_name": "Auxiliary Control Parameter 2", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParam2", "priority": "Low"},           # 39   23
        0x18: {"parameter_name": "Auxiliary Control Parameter 3", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParam3", "priority": "Low"},           # 40   24
        0x19: {"parameter_name": "Auxiliary Control Parameter 4", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParam4", "priority": "Low"},           # 41   25
        0x1A: {"parameter_name": "Auxiliary Control Parameter 5", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParam5", "priority": "Low"},           # 42   26 
    },

    # ==========================================================================
    # ANALOG PROCESS VARIABLES (0x05) - Measured values from sensors
    # ==========================================================================
    0x05: {
        0x00: {"parameter_name": "Blood Pump Speed", "data_type": "double", "access_mode": True, "unit": "RPM", "alarm_limits": (0, 600), "device_tag": "bloodPumpSpeed", "priority": "Low"}, # 43
        0x01: {"parameter_name": "Heparin Infusion Flow Rate", "data_type": "double", "access_mode": True, "unit": "mL/hr", "alarm_limits": (0, 50), "device_tag": "heparinInfusionFlow", "priority": "Low"},        # 44
        0x02: {"parameter_name": "Arterial Line Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-100, 400), "device_tag": "arterialLinePressure", "priority": "High"},  # 45
        0x03: {"parameter_name": "Venous Line Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-50, 300), "device_tag": "venousLinePressure", "priority": "High"},     # 46
        0x04: {"parameter_name": "Dialysate Inlet Pressure (Pre-Dialyzer)", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-200, 600), "device_tag": "dialysateInletPressure", "priority": "Medium"}, # 47
        0x05: {"parameter_name": "Dialysate Outlet Pressure (Post-Dialyzer)", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-200, 600), "device_tag": "dialysateOutletPressure", "priority": "Medium"},  # 48
        0x06: {"parameter_name": "Water Supply Inlet Pressure", "data_type": "double", "access_mode": True, "unit": "bar", "alarm_limits": (0, 5), "device_tag": "waterSupplyInletPressure", "priority": "Low"},        # 49
        0x07: {"parameter_name": "Dialysate Inlet Temperature", "data_type": "double", "access_mode": True, "unit": "°C", "alarm_limits": (35.0, 39.0), "device_tag": "dialysateInletTemperature", "priority": "Medium"},   # 50
        0x08: {"parameter_name": "Dialysate Outlet Temperature", "data_type": "double", "access_mode": True, "unit": "°C", "alarm_limits": (35.0, 39.0), "device_tag": "dialysateOutletTemperature", "priority": "Medium"},   # 51 
        0x09: {"parameter_name": "Replacement Fluid Flow Rate", "data_type": "double", "access_mode": True, "unit": "mL/hr", "alarm_limits": (0, 5000), "device_tag": "replacementFluidFlowRate", "priority": "Low"},      # 52
        0x0A: {"parameter_name": "Dialysate Conductivity (Pre-Dialyzer)", "data_type": "double", "access_mode": True, "unit": "mS/cm", "alarm_limits": (13.0, 15.0), "device_tag": "dialysateConductivityPre", "priority": "Medium"}, # 53
        0x0B: {"parameter_name": "Dialysate Conductivity (Post-Dialyzer)", "data_type": "double", "access_mode": True, "unit": "mS/cm", "alarm_limits": (13.0, 15.0), "device_tag": "dialysateConductivityPost", "priority": "Medium"}, # 54
        0x0C: {"parameter_name": "Patient Heart Rate", "data_type": "double", "access_mode": True, "unit": "bpm", "alarm_limits": (30, 180), "device_tag": "patientHeartRate", "priority": "High"},     # 55
        0x0D: {"parameter_name": "Dialysate Heater Tank Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-100, 100), "device_tag": "dialysateHeaterTankPressure", "priority": "Low"}, # 56
        0x0E: {"parameter_name": "Dialysate Circuit Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-200, 600), "device_tag": "dialysateCircuitPressure", "priority": "Medium"}, # 57
        0x0F: {"parameter_name": "Pre-Filter Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (0, 500), "device_tag": "preFilterPressure", "priority": "Low"},              #58  
    },
    # ==========================================================================
    # ANALOG CALIBRATION PARAMETERS (0x06) - For device calibration adjustments
    # ==========================================================================
    0x06: {
        0x00: {"parameter_name": "Heparin Pump Calibration Factor", "data_type": "double", "access_mode": True, "unit": "mL/rev", "alarm_limits": (0.01, 10.0), "device_tag": "heparinPumpCalibrationFactor", "priority": "Low"},          # 59
        0x01: {"parameter_name": "Ultrafiltration Pressure", "data_type": "double", "access_mode": True, "unit": "mmHg", "alarm_limits": (-50, 500), "device_tag": "ultrafiltrationPressure", "priority": "Medium"},               # 60 
        0x02: {"parameter_name": "Balance Chamber Pressure", "data_type": "double", "access_mode": False, "unit": "mmHg", "alarm_limits": (-100, 600), "device_tag": "balanceChamberPressure", "priority": "Medium"},        # 61
        0x03: {"parameter_name": "Arterial Circuit Pressure", "data_type": "double", "access_mode": False, "unit": "mmHg", "alarm_limits": (-300, 600), "device_tag": "arterialCircuitPressure", "priority": "High"},   # 62 
        0x04: {"parameter_name": "Venous Circuit Pressure", "data_type": "double", "access_mode": False, "unit": "mmHg", "alarm_limits": (-100, 500), "device_tag": "venousCircuitPressure", "priority": "High"},     # 63
        0x05: {"parameter_name": "Dialysis Operation Cycle Count", "data_type": "double", "access_mode": False, "unit": "cycles", "alarm_limits": (0, 100000), "device_tag": "dialysisOperationCycleCount", "priority": "Low"},      # 64
        0x06: {"parameter_name": "Auxiliary Calibration Factor 7", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0.01, 100.0), "device_tag": "auxCalibrationFactor7", "priority": "Low"},                 # 65
        0x07: {"parameter_name": "Auxiliary Control Parameter 8", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParameter8", "priority": "Low"},                                # 66
        0x08: {"parameter_name": "Auxiliary Control Parameter 9", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParameter9", "priority": "Low"},                                # 67
        0x09: {"parameter_name": "Auxiliary Control Parameter 10", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParameter10", "priority": "Low"},                              # 68
        0x0A: {"parameter_name": "Auxiliary Control Parameter 11", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParameter11", "priority": "Low"},                              # 69
        0x0B: {"parameter_name": "Auxiliary Control Parameter 12", "data_type": "double", "access_mode": True, "unit": "", "alarm_limits": (0, 1000), "device_tag": "auxControlParameter12", "priority": "Low"},                              # 70
    },
}

# ==============================================================================
# MASS ANALOG DATA ACQUISITION MAP
# This map defines the order and addresses for efficient bulk reading of analog
# parameters, typically for high-frequency data logging or display updates.
# ==============================================================================
ANALOG_READ_MAP: List[Tuple[int, int]] = [
    # 0x02 -> 7 variables (Clinical Parameters)
    *( (0x02, i) for i in range(7) ),
    # 0x03 -> 9 variables (System Setpoints)
    *( (0x03, i) for i in range(9) ),
    # 0x04 -> 27 variables (PID Control Parameters)
    *( (0x04, i) for i in range(0x1B) ),
    # 0x05 -> 16 specific variables (Analog Process Variables)
    *( (0x05, i) for i in range(0x10) ),
    # 0x06 -> 12 Calibration Variables (Analog Calibration Parameters)
    *( (0x06, i) for i in range(0x0C) )
]

# ==============================================================================
# PARAMETER GROUPING FOR USER INTERFACES
# Maps address blocks to logical groups for display, configuration, or logging.
# ==============================================================================
PARAMETER_GROUPS = {
    0x01: "Operational Controls",
    0x02: "Clinical Data",
    0x03: "System Setpoints",
    0x04: "PID Control Parameters",
    0x05: "Process Variables",
    0x06: "Calibration Parameters"
}

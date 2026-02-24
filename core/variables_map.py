#core/variables_map.py
from typing import Dict, List, Tuple, Any

# ================================================================
# MAPEO COMPLETO DE VARIABLES - HEMODIÁLISIS
# ================================================================

VARIABLES: Dict[int, Dict[int, Dict[str, Any]]] = {

    # ================================================================
    # BOOLEANOS OPERACIÓN (0x01) - 60 variables (0x00 a 0x3B)
    # ================================================================
    0x01: {
        **{i: {"name": name, "type": "bool", "rw": True, "nivel": nivel, "tag": tag, "id": i}
            for i, (name, nivel, tag) in enumerate([
                # --- VARIABLES DE CONTROL (ESCRITURA/LECTURA) - ID 0 a 40 (RW=True) ---
                ("Bomba peristáltica - Arranque", "cian", "bloodPumpStartButton"),       # 0
                ("Bomba peristáltica - Paro", "cian", "bloodPumpStopButton"),            # 1
                ("Bomba peristáltica - Avance", "cian", "bloodPumpFWDButton"),           # 2
                ("Bomba peristáltica - Reversa", "cian", "bloodPumpREVButton"),          # 3
                ("Bomba de purga - Arranque", "cian", "dialyserPumpStartButton"), # 4
                ("Bomba de purga - Paro", "cian", "dialyserPumpStopButton"),       # 5
                ("Bomba Heparina - Arranque", "cian", "heparinePumpsStartButton"),       # 6
                ("Bomba Heparina - Paro", "cian", "heparinePumpsStopButton"),            # 7
                ("Bomba Heparina - Avance", "cian", "heparinePumpFWDButton"),            # 8
                ("Bomba Heparina - Reversa", "cian", "heparinePumpREVButton"),           # 9
                ("Control Flujo Sangre - Habilitar", "cian", "bloodControlLoopEnable"),  # 10
                ("Control Flujo Sangre - Auto/Manual", "cian", "bloodControlLoopMode"),  # 11
                ("Control Conductividad - Habilitar", "cian", "dialyCondCtrlLoopEnable"),# 12
                ("Control Conductividad - Auto/Manual", "cian", "dialyCondCtrlLoopMode"),# 13
                ("Control Temp Dializante - Habilitar", "cian", "dialyTempCtrlLoopEnable"),# 14
                ("Control Temp Dializante - Auto/Manual", "cian", "dialyTempCtrlLoopMode"),# 15
                ("Bomba Heparina - Home", "cian", "heparinePumpHomePosition"),           # 16
                ("Cámara Balance - Start", "cian", "dialiserBalChambStrButt"),           # 17
                ("Cámara Balance - Stop", "cian", "dialiserBalChambStpButt"),            # 18
                ("Bolo Heparina", "cian", "heparinApplyBolusDose"),                      # 19
                ("Pausar/Continuar", "cian", "heparineOperPauseResume"),                 # 20
                ("Operar Elementos Dializante", "cian", "dialyCircuitElementsOpSel"),    # 21
                ("Bomba Purga Dializante - Start", "cian", "dialyPurgePumpStartButt"),   # 22 (Corregido: era 'Bomba Deaereación')
                ("Bomba Purga Dializante - Stop", "cian", "dialyPurgePumpStopButt"),     # 23 (Corregido: era 'Bomba Deaereación')
                ("Bomba UF - Start", "cian", "dialyUltraFPumpStartButt"),                # 24
                ("Bomba UF - Stop", "cian", "dialyUltraFPumpStoptButt"),                 # 25
                ("Bomba Bicarbonato - Start", "cian", "dialyBicarbonPumpStartButt"),     # 26
                ("Bomba Bicarbonato - Stop", "cian", "dialyBicarbonPumpStopButt"),       # 27
                ("Bomba Ácido Cítrico - Start", "cian", "dialyCitricAcPumpStartButt"),   # 28
                ("Bomba Ácido Cítrico - Stop", "cian", "dialyCitricAcPumpStopButt"),     # 29
                ("Válvula Agua Entrada", "cian", "dialyWaterInletValveButt"),            # 30
                ("Válvula Recirculación", "cian", "dialyRecirculatValveButt"),           # 31
                ("Válvula Cámara Caliente", "cian", "dialyHotChambValveButt"),           # 32
                ("Válvula Venteo Aire", "cian", "dialyAirVentSepChambButt"),             # 33
                ("Válvula Bypass Filtro", "cian", "dialyBypassFilterButt"),              # 34
                ("Válvula Corte Entrada Filtro", "cian", "dialyInputFilterCutButt"),     # 35
                ("Válvula Corte Salida Filtro", "cian", "dialyOutputFilterCutButt"),     # 36
                ("Válvula de Drenaje", "cian", "dialyWaterDrainValveButt"),              # 37
                ("Fin de Ciclo Cámara Balance", "amarillo", "dialyBalanceChambCycleEnd"),# 38 (Usualmente es solo lectura, pero por ser un indicador que puede ser reseteado o consultado se deja RW=True)
                ("Iniciar Diálisis", "cian", "dialyStartDialysisButt"),                  # 39
                ("Parar Diálisis", "cian", "dialyStopDialysisButt"),                     # 40

                # --- VARIABLES DE LECTURA/INDICADORES (RW=False) - ID 41 a 59 ---
                ("Protección Resistores Calefactor", "rojo", "watterTankHeaterProtect"),  # 41
                ("Disponible para Función Digital 3", "cian", "availableBoolVariable1"),  # 42
                ("Disponible para Función Digital 4", "cian", "availableBoolVariable2"),  # 43
                ("Disponible para Función Digital 5", "cian", "availableBoolVariable3"),  # 44
                ("Disponible para Función Digital 6", "cian", "availableBoolVariable4"),  # 45
                ("Disponible para Función Digital 7", "cian", "availableBoolVariable5"),  # 46
                ("Disponible para Función Digital 8", "cian", "availableBoolVariable6"),  # 47
                ("Detector Burbuja Aire en Sangre", "rojo", "airBubbleInBloodDetected"),  # 48
                ("Detector Sangre en Dializante", "rojo", "bloodInDialyCircDetected"),    # 49
                ("Nivel Alto Tanque Agua", "amarillo", "dialyTankHiLevelSwitch"),         # 50
                ("Nivel Cámara Deaereación", "amarillo", "dialyDeaerChamLevSwitch"),      # 51
                ("Disponible para Función Digital 11", "cian", "availableBoolVariable7"), # 52
                ("Disponible para Función Digital 12", "cian", "availableBoolVariable8"), # 53
                ("Disponible para Función Digital 13", "cian", "availableBoolVariable9"), # 54
                ("Disponible para Función Digital 14", "cian", "availableBoolVariable10"),# 55
                ("Disponible para Función Digital 15", "cian", "availableBoolVariable11"),# 56
                ("Disponible para Función Digital 16", "cian", "availableBoolVariable12"),# 57
                ("Disponible para Función Digital 17", "cian", "availableBoolVariable13"),# 58
                ("Disponible para Función Digital 18", "cian", "availableBoolVariable14"),# 59
            ], start=0)}
    },


    # ================================================================
    # PARÁMETROS CLÍNICOS (0x02)
    # ================================================================
    0x02: {
        0x00: {"name": "Presión intermembrana","type": "double","rw": True,"unit": "mmHg","limites": (1, 100),"tag": "interMembPresClinicData", "nivel": "cian"},             # 0
        0x01: {"name": "Selección de modo de tratamiento","type": "double","rw": True, "unit": "NA","limites": (0, 100),"tag": "treatmentModeSelection","nivel": "cian"},   # 1
        0x02: {"name": "Estado actual de proceso de cebado","type": "double","rw": True,"unit": "NA","limites": (0, 100),"tag": "primingProcessStatus","nivel": "cian"},    # 2
        0x03: {"name": "Variable clínica visualización 3","type": "double","rw": True,"unit": "NA","limites": (0, 100),"tag": "availableClinicVariable4","nivel": "cian"},    # 3
        0x04: {"name": "Selector de ciclos cámara de balance","type": "double","rw": True,"unit": "n","limites": (1, 100),"tag": "balanceChamberCycleSet","nivel": "cian"},   # 4
        0x05: {"name": "Volumen de heparina dosificado actual","type": "double","rw": True,"unit": "ml","limites": (0, 100),"tag": "heparineCurrentDosage","nivel": "cian"},  # 5
        0x06: {"name": "Número de ciclos cámara de balance","type": "double","rw": True,"unit": "c","limites": (0, 10000),"tag": "balanceChamberCycleCount","nivel": "cian"}, # 6
    },

    # ================================================================
    # SETPOINTS (0x03)
    # ================================================================
    0x03: {
        0x00: {"name": "Velocidad de UltraFiltrado","type": "double","rw": True,"unit": "L/h","limites": (0, 2),"tag": "ultraFilterPumpSpeed","nivel": "cian"},              # 7
        0x01: {"name": "Ajuste de tiempo de ciclo de cámara de balance","type": "double","rw": True,"unit": "s","limites": (0, 100),"tag": "balanceChamberSetTiming","nivel": "cian"}, # 8
        0x02: {"name": "Tiempo terapia: horas","type": "double","rw": True,"unit": "h","limites": (0, 10),"tag": "heparineTherapyHours","nivel": "cian"},                    # 9
        0x03: {"name": "Tiempo terapia: minutos","type": "double","rw": True, "unit": "m","limites": (0, 59),"tag": "heparineTherapyMinutes","nivel": "cian"},               # 10
        0x04: {"name": "Tamaño de escala de jeringa","type": "double","rw": True,"unit": "mm/ml","limites": (1, 10),"tag": "heparineSyrinjeScaleSize","nivel": "cian"},      # 11
        0x05: {"name": "Dosis de heparina por terapia ml/h","type": "double","rw": True,"unit": "ml/h","limites": (0, 50),"tag": "heparineTherapyDosage","nivel": "cian"},   # 12
        0x06: {"name": "Cantidad de bolo","type": "double","rw": True,"unit": "ml","limites": (0, 10),"tag": "heparineBolusQuantity","nivel": "cian"},                       # 13
        0x07: {"name": "Ajuste de velocidad de bomba bicarbonato","type": "double","rw": True,"unit": "%","limites": (0, 100),"tag": "bicarbonatePumpSpeed","nivel": "cian"},# 14
        0x08: {"name": "Ajuste de velocidad de ácido cítrico","type": "double","rw": True,"unit": "%","limites": (0, 100),"tag": "citricAcidPumpSpeed","nivel": "cian"},     # 15
    },

    # ================================================================
    # CONTROL PID (0x04)
    # ================================================================
    0x04: {
        0x00: {"name": "Setpoint flujo sanguíneo", "type": "double", "rw": True, "unit": "ml/min", "limites": (0, 600), "tag": "bloodFlowControlSetPoint", "nivel": "cian"},        # 16   0
        0x01: {"name": "Cálculo flujo circuito sanguíneo", "type": "double", "rw": True, "unit": "ml/min", "limites": (0, 600), "tag": "bloodFlowVariableData", "nivel": "cian"},   # 17   1 
        0x02: {"name": "Salida control flujo sanguíneo", "type": "double", "rw": True, "unit": "%", "limites": (0, 100), "tag": "bloodFlowControlOutput", "nivel": "cian"},         # 18   2
        0x03: {"name": "Kp control de flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "bloodFlowControlPropGain", "nivel": "cian"},          # 19   3 
        0x04: {"name": "Ki control de flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "bloodFlowControlInteGain", "nivel": "cian"},          # 20   4
        0x05: {"name": "Kd control de flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "bloodFlowControlDeriGain", "nivel": "cian"},          # 21   5
        0x06: {"name": "Setpoint conductividad", "type": "double", "rw": True, "unit": "mS/cm", "limites": (13.0, 15.0), "tag": "dialyCondControlSetPoint", "nivel": "cian"},       # 22   6
        0x07: {"name": "Conductividad medida", "type": "double", "rw": False, "unit": "mS/cm", "limites": (12.5, 15.5), "tag": "dialyCondVariableData", "nivel": "amarillo"},       # 23   7
        0x08: {"name": "Salida control de conductividad", "type": "double", "rw": False, "unit": "%", "limites": (0, 100), "tag": "dialyCondControlOutput", "nivel": "cian"},       # 24   8
        0x09: {"name": "Kp control de conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyCondControlPropGain", "nivel": "cian"},            # 25   9
        0x0A: {"name": "Ki control de conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyCondControlInteGain", "nivel": "cian"},            # 26   10
        0x0B: {"name": "Kd control de conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyCondControlDeriGain", "nivel": "cian"},            # 27   11  
        0x0C: {"name": "Setpoint temperatura", "type": "double", "rw": True, "unit": "°C", "limites": (35.0, 39.0), "tag": "dialyTempControlSetPoint", "nivel": "cian"},            # 28   12 
        0x0D: {"name": "Temperatura medida", "type": "double", "rw": False, "unit": "°C", "limites": (34.5, 39.5), "tag": "dialyTempVariableData", "nivel": "amarillo"},            # 29   13
        0x0E: {"name": "Salida control temperatura", "type": "double", "rw": False, "unit": "%", "limites": (0, 100), "tag": "dialyTempControlOutput", "nivel": "cian"},            # 30   14 
        0x0F: {"name": "Kp control temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyTempControlPropGain", "nivel": "cian"},                 # 31   15
        0x10: {"name": "Ki control temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyTempControlInteGain", "nivel": "cian"},                 # 32   16
        0x11: {"name": "Kd control temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10), "tag": "dialyTempControlDeriGain", "nivel": "cian"},                 # 33   17
        0x12: {"name": "Ganancia Feedforward flujo", "type": "double", "rw": True, "unit": "", "limites": (0, 5), "tag": "bloodFlowFeedForwardGain", "nivel": "cian"},              # 34   18
        0x13: {"name": "Tiempo adelanto Feedforward flujo", "type": "double", "rw": True, "unit": "s", "limites": (0, 10), "tag": "bloodFlowFeedForwardLead", "nivel": "cian"},     # 35   19
        0x14: {"name": "Setpoint flujo dializante", "type": "double", "rw": True, "unit": "ml/min", "limites": (300, 800), "tag": "dialyFlowControlOutput", "nivel": "cian"},       # 36   20
        0x15: {"name": "Salida bomba de purga", "type": "double", "rw": True, "unit": "%", "limites": (0, 100), "tag": "dialyDeaerControlOutput", "nivel": "cian"},                # 37   21  
        0x16: {"name": "Parámetro control variable 1", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "variableCtrlParamData1", "nivel": "cian"},           # 38   22
        0x17: {"name": "Parámetro control variable 2", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "variableCtrlParamData2", "nivel": "cian"},           # 39   23
        0x18: {"name": "Parámetro control variable 3", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "variableCtrlParamData3", "nivel": "cian"},           # 40   24
        0x19: {"name": "Parámetro control variable 4", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "variableCtrlParamData4", "nivel": "cian"},           # 41   25
        0x1A: {"name": "Parámetro control variable 5", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "variableCtrlParamData5", "nivel": "cian"},           # 42   26 
    },

    # ================================================================
    # PROCESO - ANALÓGICAS (0x05)
    # ================================================================
    0x05: {
        0x00: {"name": "Velocidad bomba peristáltica de sangre", "type": "double", "rw": True, "unit": "RPM", "limites": (0, 600), "tag": "bloodSpeedVariableData", "nivel": "cian"}, # 43
        0x01: {"name": "Flujo de heparina", "type": "double", "rw": True, "unit": "ml/h", "limites": (0, 50), "tag": "heparFlowProcessData", "nivel": "cian"},                        # 44
        0x02: {"name": "Presión arterial en línea sanguínea", "type": "double", "rw": True, "unit": "mmHg", "limites": (-100, 400), "tag": "arterPresProcessData", "nivel": "rojo"},  # 45
        0x03: {"name": "Presión venosa en línea sanguínea", "type": "double", "rw": True, "unit": "mmHg", "limites": (-50, 300), "tag": "venouPresProcessData", "nivel": "rojo"},     # 46
        0x04: {"name": "Presión del dializante Entrada del filtro (EF)", "type": "double", "rw": True, "unit": "mmHg", "limites": (-200, 600), "tag": "dialyPresIFProcessData", "nivel": "amarillo"}, # 47
        0x05: {"name": "Presión del dializante Salida del filtro (SF)", "type": "double", "rw": True, "unit": "mmHg", "limites": (-200, 600), "tag": "dialyPresOFProcessData", "nivel": "amarillo"},  # 48
        0x06: {"name": "Presión entrada agua alimentación", "type": "double", "rw": True, "unit": "bar", "limites": (0, 5), "tag": "dialyLineWaterPresData", "nivel": "cian"},        # 49
        0x07: {"name": "Temperatura del dializante EF", "type": "double", "rw": True, "unit": "°C", "limites": (35.0, 39.0), "tag": "dialyTempIFProcessData", "nivel": "amarillo"},   # 50
        0x08: {"name": "Temperatura del dializante SF", "type": "double", "rw": True, "unit": "°C", "limites": (35.0, 39.0), "tag": "dialyTempOFProcessData", "nivel": "amarillo"},   # 51 
        0x09: {"name": "Flujo de líquido de sustitución", "type": "double", "rw": True, "unit": "ml/h", "limites": (0, 5000), "tag": "subsLiqFlowProcessData", "nivel": "cian"},      # 52
        0x0A: {"name": "Conductividad dializante antes del filtro", "type": "double", "rw": True, "unit": "mS/cm", "limites": (13.0, 15.0), "tag": "dialyConductIFProcessData", "nivel": "amarillo"}, # 53
        0x0B: {"name": "Conductividad dializante después del filtro", "type": "double", "rw": True, "unit": "mS/cm", "limites": (13.0, 15.0), "tag": "dialyConductOFProcessData", "nivel": "amarillo"}, # 54
        0x0C: {"name": "Parametro de control ", "type": "double", "rw": True, "unit": "lpm", "limites": (0,1000), "tag": "patHeartFreqProcessData", "nivel": "rojo"},     # 55
        0x0D: {"name": "Presión en el tanque de calentamiento", "type": "double", "rw": True, "unit": "mmHg", "limites": (-100, 100), "tag": "dialyTankPresProcessData", "nivel": "cian"}, # 56
        0x0E: {"name": "Presión en la línea del dializante", "type": "double", "rw": True, "unit": "mmHg", "limites": (-200, 600), "tag": "dialyLinePresProcessData", "nivel": "amarillo"}, # 57
        0x0F: {"name": "Presión Prefiltrado", "type": "double", "rw": True, "unit": "mmHg", "limites": (0, 500), "tag": "dialyPFilPmpPresProcessData", "nivel": "cian"},              #58  
    },
    # ================================================================
    # CALIBRACIÓN - ANALÓGICAS (0x06) 
    # ================================================================
    0x06: {
        0x00: {"name": "Factor calibración bomba heparina", "type": "double", "rw": True, "unit": "ml/rev", "limites": (0.01, 10.0), "tag": "heparCalibFactorData", "nivel": "cian"},          # 59
        0x01: {"name": "Presión de ultrafiltrado", "type": "double", "rw": True, "unit": "mmHg", "limites": (-50, 500), "tag": "dialyUFilPresProcessData", "nivel": "amarillo"},               # 60 
        0x02: {"name": "Presión en cámara de balance", "type": "double", "rw": False, "unit": "mmHg", "limites": (-100, 600), "tag": "dialyBChamPresProcessData", "nivel": "amarillo"},        # 61
        0x03: {"name": "Presión arterial del circuito de sangre", "type": "double", "rw": False, "unit": "mmHg", "limites": (-300, 600), "tag": "bloodArteryPressureData", "nivel": "rojo"},   # 62 
        0x04: {"name": "Presión venosa del circuito de sangre", "type": "double", "rw": False, "unit": "mmHg", "limites": (-100, 500), "tag": "bloodVenousPressureData", "nivel": "rojo"},     # 63
        0x05: {"name": "Contador de ciclos de dialización", "type": "double", "rw": False, "unit": "ciclos", "limites": (0, 100000), "tag": "dialyCycleOperationCount", "nivel": "cian"},      # 64
        0x06: {"name": "Factor calibración parámetro 7", "type": "double", "rw": True, "unit": "", "limites": (0.01, 100.0), "tag": "parameterCalFactData7", "nivel": "cian"},                 # 65
        0x07: {"name": "Parámetro control 8", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "parameterControlData8", "nivel": "cian"},                                # 66
        0x08: {"name": "Parámetro control 9", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "parameterControlData9", "nivel": "cian"},                                # 67
        0x09: {"name": "Parámetro control 10", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "parameterControlData10", "nivel": "cian"},                              # 68
        0x0A: {"name": "Parámetro control 11", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "parameterControlData11", "nivel": "cian"},                              # 69
        0x0B: {"name": "Parámetro control 12", "type": "double", "rw": True, "unit": "", "limites": (0, 1000), "tag": "parameterControlData12", "nivel": "cian"},                              # 70
    },
    # ================================================================
    # BIOIMPEDANCIA Y UREA (0x07) - NUEVO GRUPO
    # ================================================================
    0x07: {
        0x00: {"name": "BioZ Resistencia", "type": "double", "rw": False, "unit": "Ohm", "limites": (0, 1000), "tag": "bioz_resistance", "nivel": "cian"}, # ID para Modbus si lo hubiera
        0x01: {"name": "BioZ Fase", "type": "double", "rw": False, "unit": "Deg", "limites": (-180, 180), "tag": "bioz_phase", "nivel": "cian"},           # Estos tags son usados en la señal data_received
        0x02: {"name": "Urea Sensor ADC1", "type": "double", "rw": False, "unit": "ADC", "limites": (0, 4095), "tag": "urea_adc1", "nivel": "cian"},       
        0x03: {"name": "Urea Sensor ADC2", "type": "double", "rw": False, "unit": "ADC", "limites": (0, 4095), "tag": "urea_adc2", "nivel": "cian"},       
    },
}

# ================================================================
# MAPEO DE LECTURA MASIVA ANALÓGICA (71 doubles)
# ================================================================
ANALOG_MAP: List[Tuple[int, int]] = [
    # 0x02 → 7 variables
    *( (0x02, i) for i in range(7) ),
    # 0x03 → 9 variables
    *( (0x03, i) for i in range(9) ),
    # 0x04 → 27 variables (0x00 a 0x1A)
    *( (0x04, i) for i in range(0x1B) ),
    # 0x05 → 16 variables específicas
    *( (0x05, i) for i in range(0x10) ),
    # 0x06 12 Variables de calibración)
    *( (0x06, i) for i in range(0x0C) )
]

# ================================================================
# GRUPOS PARA TABLAS
# ================================================================
TVAR_TO_GROUP = {
    0x01: "Operación",
    0x02: "Clínicos",
    0x03: "Setpoints",
    0x04: "Control PID",
    0x05: "Proceso",
    0x06: "Calibración",
    0x07: "Bioimpedancia y Urea" 
}
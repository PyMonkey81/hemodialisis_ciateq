# variables_map.py
VARIABLES = {
    # ================================================================
    # === OPERACIÓN (0x01) - BOOLEANOS R/W ===
    # ================================================================
    0x01: {
        0x00: {"name": "Bomba Sangre - Arranque", "type": "bool", "rw": True, "nivel": "cian"},
        0x01: {"name": "Bomba Sangre - Paro", "type": "bool", "rw": True, "nivel": "cian"},
        0x02: {"name": "Bomba Sangre - Avance", "type": "bool", "rw": True, "nivel": "cian"},
        0x03: {"name": "Bomba Sangre - Reversa", "type": "bool", "rw": True, "nivel": "cian"},
        0x04: {"name": "Bomba Dializante - Arranque", "type": "bool", "rw": True, "nivel": "cian"},
        0x05: {"name": "Bomba Dializante - Paro", "type": "bool", "rw": True, "nivel": "cian"},
        0x06: {"name": "Bomba Heparina - Arranque", "type": "bool", "rw": True, "nivel": "cian"},
        0x07: {"name": "Bomba Heparina - Paro", "type": "bool", "rw": True, "nivel": "cian"},
        0x08: {"name": "Bomba Heparina - Avance", "type": "bool", "rw": True, "nivel": "cian"},
        0x09: {"name": "Bomba Heparina - Reversa", "type": "bool", "rw": True, "nivel": "cian"},
        0x0A: {"name": "Control Flujo Sangre - Habilitar", "type": "bool", "rw": True, "nivel": "cian"},
        0x0B: {"name": "Control Flujo Sangre - Auto/Manual", "type": "bool", "rw": True, "nivel": "cian"},
        0x0C: {"name": "Control Conductividad - Habilitar", "type": "bool", "rw": True, "nivel": "cian"},
        0x0D: {"name": "Control Conductividad - Auto/Manual", "type": "bool", "rw": True, "nivel": "cian"},
        0x0E: {"name": "Control Temp Dializante - Habilitar", "type": "bool", "rw": True, "nivel": "cian"},
        0x0F: {"name": "Control Temp Dializante - Auto/Manual", "type": "bool", "rw": True, "nivel": "cian"},
        0x10: {"name": "Bomba Heparina - Home", "type": "bool", "rw": True, "nivel": "cian"},
        0x11: {"name": "Cámara Balance - Start", "type": "bool", "rw": True, "nivel": "cian"},
        0x12: {"name": "Cámara Balance - Stop", "type": "bool", "rw": True, "nivel": "cian"},
        0x13: {"name": "Bolo Heparina", "type": "bool", "rw": True, "nivel": "cian"},
        0x14: {"name": "Pausar/Continuar", "type": "bool", "rw": True, "nivel": "cian"},
        0x15: {"name": "Operar Elementos Dializante", "type": "bool", "rw": True, "nivel": "cian"},
        0x16: {"name": "Bomba Deaereación - Start", "type": "bool", "rw": True, "nivel": "cian"},
        0x17: {"name": "Bomba Deaereación - Stop", "type": "bool", "rw": True, "nivel": "cian"},
        0x18: {"name": "Bomba UF - Start", "type": "bool", "rw": True, "nivel": "cian"},
        0x19: {"name": "Bomba UF - Stop", "type": "bool", "rw": True, "nivel": "cian"},
        0x1A: {"name": "Bomba Bicarbonato - Start", "type": "bool", "rw": True, "nivel": "cian"},
        0x1B: {"name": "Bomba Bicarbonato - Stop", "type": "bool", "rw": True, "nivel": "cian"},
        0x1C: {"name": "Bomba Ácido Cítrico - Start", "type": "bool", "rw": True, "nivel": "cian"},
        0x1D: {"name": "Bomba Ácido Cítrico - Stop", "type": "bool", "rw": True, "nivel": "cian"},
        0x1E: {"name": "Válvula Agua Entrada", "type": "bool", "rw": True, "nivel": "cian"},
        0x1F: {"name": "Válvula Recirculación", "type": "bool", "rw": True, "nivel": "cian"},
        0x20: {"name": "Válvula Cámara Caliente", "type": "bool", "rw": True, "nivel": "cian"},
        0x21: {"name": "Válvula Venteo Aire", "type": "bool", "rw": True, "nivel": "cian"},
        0x22: {"name": "Válvula Bypass UF", "type": "bool", "rw": True, "nivel": "cian"},
        0x23: {"name": "Válvula Entrada Filtro", "type": "bool", "rw": True, "nivel": "cian"},
        0x24: {"name": "Válvula Salida Filtro", "type": "bool", "rw": True, "nivel": "cian"},
        0x25: {"name": "Válvula Drenaje", "type": "bool", "rw": True, "nivel": "cian"},
        0x26: {"name": "Ciclo Cámara Balance Terminado", "type": "bool", "rw": True, "nivel": "amarillo"},
        0x27: {"name": "Iniciar Diálisis", "type": "bool", "rw": True, "nivel": "cian"},
        0x28: {"name": "Parar Diálisis", "type": "bool", "rw": True, "nivel": "cian"},
        0x29: {"name": "Protección Resistores Calefactor", "type": "bool", "rw": True, "nivel": "rojo"},
        0x2A: {"name": "Disponible 1", "type": "bool", "rw": True, "nivel": "cian"},
        0x2B: {"name": "Disponible 2", "type": "bool", "rw": True, "nivel": "cian"},
        0x2C: {"name": "Disponible 3", "type": "bool", "rw": True, "nivel": "cian"},
        0x2D: {"name": "Disponible 4", "type": "bool", "rw": True, "nivel": "cian"},
        0x2E: {"name": "Disponible 5", "type": "bool", "rw": True, "nivel": "cian"},
        0x2F: {"name": "Disponible 6", "type": "bool", "rw": True, "nivel": "cian"},
        0x30: {"name": "Detector Aire en Sangre", "type": "bool", "rw": True, "nivel": "rojo"},
        0x31: {"name": "Detector Sangre en Dializante", "type": "bool", "rw": True, "nivel": "rojo"},
        0x32: {"name": "Nivel Alto Tanque Agua", "type": "bool", "rw": True, "nivel": "amarillo"},
        0x33: {"name": "Nivel Cámara Deaereación", "type": "bool", "rw": True, "nivel": "amarillo"},
        0x34: {"name": "Disponible 7", "type": "bool", "rw": True, "nivel": "cian"},
        0x35: {"name": "Disponible 8", "type": "bool", "rw": True, "nivel": "cian"},
        0x36: {"name": "Disponible 9", "type": "bool", "rw": True, "nivel": "cian"},
        0x37: {"name": "Disponible 10", "type": "bool", "rw": True, "nivel": "cian"},
        0x38: {"name": "Disponible 11", "type": "bool", "rw": True, "nivel": "cian"},
        0x39: {"name": "Disponible 12", "type": "bool", "rw": True, "nivel": "cian"},
        0x3A: {"name": "Disponible 13", "type": "bool", "rw": True, "nivel": "cian"},
        0x3B: {"name": "Disponible 14", "type": "bool", "rw": True, "nivel": "cian"},
    },

    # ================================================================
    # === PARÁMETROS CLÍNICOS (0x02) - R/W ===
    # ================================================================
    0x02: {
        0x00: {"name": "Presión intermembrana", "type": "double", "rw": True, "unit": "mmHg", "limites": (1, 100)},
        0x01: {"name": "Variable clínica visualización 1", "type": "double", "rw": True, "unit": "NA", "limites": (0, 100)},
        0x02: {"name": "Variable clínica visualización 2", "type": "double", "rw": True, "unit": "NA", "limites": (0, 100)},
        0x03: {"name": "Variable clínica visualización 3", "type": "double", "rw": True, "unit": "NA", "limites": (0, 100)},
        0x04: {"name": "Selector de ciclos cámara de balance", "type": "double", "rw": True, "unit": "n", "limites": (1, 100)},
        0x05: {"name": "Volumen de heparina dosificado actual", "type": "double", "rw": True, "unit": "ml", "limites": (1, 100)},
        0x06: {"name": "Número de ciclos cámara de balance", "type": "double", "rw": True, "unit": "c", "limites": (1, 100)},
    },

    # ================================================================
    # === SETPOINTS DE CONFIGURACIÓN (0x03) - W (solo escritura) ===
    # ================================================================
    0x03: {
        0x00: {"name": "Ajuste de strokes de bomba de ultra filtrado", "type": "double", "rw": False, "unit": "n", "limites": (0, 100)},
        0x01: {"name": "Ajuste de tiempo de ciclo de cámara de balance", "type": "double", "rw": False, "unit": "n", "limites": (0, 100)},
        0x02: {"name": "Ajuste de horas de terapia", "type": "double", "rw": False, "unit": "h", "limites": (0, 10)},
        0x03: {"name": "Ajuste de minutos de terapia", "type": "double", "rw": False, "unit": "m", "limites": (0, 59)},
        0x04: {"name": "Tamaño de escala de jeringa", "type": "double", "rw": False, "unit": "mm/ml", "limites": (1, 10)},
        0x05: {"name": "Dosis de heparina por terapia ml/h", "type": "double", "rw": False, "unit": "ml/h", "limites": (1, 10)},
        0x06: {"name": "Cantidad de bolo", "type": "double", "rw": False, "unit": "ml", "limites": (0, 10)},
        0x07: {"name": "Ajuste de velocidad de bomba bicarbonato", "type": "double", "rw": False, "unit": "%", "limites": (0, 100)},
        0x08: {"name": "Ajuste de velocidad de ácido cítrico", "type": "double", "rw": False, "unit": "%", "limites": (0, 100)},
    },

    # ================================================================
    # === CONTROL PID (0x04) - R/W ===
    # ================================================================
    0x04: {
        0x00: {"name": "Setpoint flujo sanguíneo", "type": "double", "rw": True, "unit": "ml/min", "limites": (0, 600)},
        0x01: {"name": "Cálculo flujo circuito sanguíneo", "type": "double", "rw": True, "unit": "ml/min"},
        0x02: {"name": "Salida control flujo sanguíneo", "type": "double", "rw": True, "unit": "%", "limites": (0, 100)},
        0x03: {"name": "Kp flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x04: {"name": "Ki flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x05: {"name": "Kd flujo sanguíneo", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x06: {"name": "Setpoint conductividad", "type": "double", "rw": True, "unit": "mS/cm", "limites": (13, 15)},
        0x07: {"name": "Conductividad medida", "type": "double", "rw": True, "unit": "mS/cm", "limites": (13, 15)},
        0x08: {"name": "Salida control conductividad", "type": "double", "rw": True, "unit": "%", "limites": (0, 100)},
        0x09: {"name": "Kp conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x0A: {"name": "Ki conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x0B: {"name": "Kd conductividad", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x0C: {"name": "Setpoint temperatura", "type": "double", "rw": True, "unit": "°C", "limites": (36, 38)},
        0x0D: {"name": "Temperatura medida", "type": "double", "rw": True, "unit": "°C", "limites": (35, 39)},
        0x0E: {"name": "Salida control temperatura", "type": "double", "rw": True, "unit": "%", "limites": (0, 100)},
        0x0F: {"name": "Kp temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x10: {"name": "Ki temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x11: {"name": "Kd temperatura", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x12: {"name": "Ganancia feedforward bomba", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x13: {"name": "Lead time feedforward", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x14: {"name": "Salida bomba dializante", "type": "double", "rw": True, "unit": "", "limites": (0, 100)},
        0x15: {"name": "Salida bomba purga", "type": "double", "rw": True, "unit": "", "limites": (0, 100)},
        0x16: {"name": "Variable disponible 1", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x17: {"name": "Variable disponible 2", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x18: {"name": "Variable disponible 3", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x19: {"name": "Variable disponible 4", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
        0x1A: {"name": "Variable disponible 5", "type": "double", "rw": True, "unit": "", "limites": (0, 10)},
    },

    # ================================================================
    # === PROCESO (0x05) - ANALÓGICAS R (solo lectura) ===
    # ================================================================
    0x05: {
        0x00: {"name": "Velocidad Bomba Sangre", "type": "double", "rw": False, "unit": "RPM", "limites": (0, 600)},
        0x01: {"name": "Flujo Heparina", "type": "double", "rw": False, "unit": "ml/h", "limites": (0, 50)},
        0x02: {"name": "Presión Arterial", "type": "double", "rw": False, "unit": "mmHg", "limites": (50, 200), "nivel": "rojo"},
        0x03: {"name": "Presión Venosa", "type": "double", "rw": False, "unit": "mmHg", "limites": (20, 150), "nivel": "rojo"},
        0x04: {"name": "Presión Dializante Entrada", "type": "double", "rw": False, "unit": "mmHg", "limites": (-100, 500)},
        0x05: {"name": "Presión Dializante Salida", "type": "double", "rw": False, "unit": "mmHg", "limites": (-100, 500)},
        0x06: {"name": "Presión Línea Agua", "type": "double", "rw": False, "unit": "bar"},
        0x07: {"name": "Temperatura Dializante IF", "type": "double", "rw": False, "unit": "°C", "limites": (35, 39), "nivel": "amarillo"},
        0x08: {"name": "Temperatura Dializante OF", "type": "double", "rw": False, "unit": "°C", "limites": (35, 39)},
        0x09: {"name": "Flujo Líquido Sustitución", "type": "double", "rw": False, "unit": "ml/min"},
        0x0A: {"name": "Conductividad IF", "type": "double", "rw": False, "unit": "mS/cm", "limites": (13.5, 14.5), "nivel": "amarillo"},
        0x0B: {"name": "Conductividad OF", "type": "double", "rw": False, "unit": "mS/cm", "limites": (13.5, 14.5)},
        0x0C: {"name": "Frecuencia Cardíaca", "type": "double", "rw": False, "unit": "bpm", "limites": (50, 120)},
        0x0D: {"name": "Presión Tanque Calentamiento", "type": "double", "rw": False, "unit": "bar"},
        0x0E: {"name": "Presión Línea Dializante", "type": "double", "rw": False, "unit": "bar"},
        0x0F: {"name": "Presión Bomba Prefiltrado", "type": "double", "rw": False, "unit": "bar"},
        0x3B: {"name": "Relación velocidad/volumen heparina", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x3C: {"name": "Presión de ultrafiltrado", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x3D: {"name": "Presión cámara de balance", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x3E: {"name": "Presión arterial guardada", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x3F: {"name": "Presión venosa guardada", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x40: {"name": "Contador de ciclos", "type": "double", "rw": False, "unit": "c", "limites": (0, 10000)},
        0x41: {"name": "Calibración 8", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x42: {"name": "Calibración 9", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x43: {"name": "Calibración 10", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x44: {"name": "Calibración 11", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x45: {"name": "Calibración 12", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
        0x46: {"name": "Calibración 13", "type": "double", "rw": False, "unit": "", "limites": (0, 100)},
    },
}

TVAR_TO_GROUP = {
    0x01: "O", 0x02: "C1", 0x03: "C2", 0x04: "CV", 0x05: "PV"
}

ANALOG_MAP = [
    # C1 (0x02): 7 variables → índices 0 a 6
    (0x02, 0x00), (0x02, 0x01), (0x02, 0x02), (0x02, 0x03),
    (0x02, 0x04), (0x02, 0x05), (0x02, 0x06),
    
    # C2 (0x03): 9 variables → índices 7 a 15
    (0x03, 0x00), (0x03, 0x01), (0x03, 0x02), (0x03, 0x03),
    (0x03, 0x04), (0x03, 0x05), (0x03, 0x06), (0x03, 0x07), (0x03, 0x08),
    
    # CV (0x04): 27 variables → índices 16 a 42
    *( (0x04, i) for i in range(0x1B) ),
    
    # PV (0x05): 28 variables → índices 43 a 70
    (0x05, 0x00), (0x05, 0x01), (0x05, 0x02), (0x05, 0x03),
    (0x05, 0x04), (0x05, 0x05), (0x05, 0x06), (0x05, 0x07),
    (0x05, 0x08), (0x05, 0x09), (0x05, 0x0A), (0x05, 0x0B),
    (0x05, 0x0C), (0x05, 0x0D), (0x05, 0x0E), (0x05, 0x0F),
    (0x05, 0x3B), (0x05, 0x3C), (0x05, 0x3D), (0x05, 0x3E),
    (0x05, 0x3F), (0x05, 0x40), (0x05, 0x41), (0x05, 0x42),
    (0x05, 0x43), (0x05, 0x44), (0x05, 0x45), (0x05, 0x46),
]
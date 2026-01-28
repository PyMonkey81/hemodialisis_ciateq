# logic/calculos.py
from typing import Optional
import logging

# Al inicio del archivo (para que sea más bonito)
__version__ = "1.0.0"
__author__ = "Miguel Espinoza - CIATEQ A.C."
__doc__ = "Módulo de cálculos clínicos para máquina de hemodiálisis Yeztli"

# ========================================
# CONFIGURACIÓN DE LOG (para auditoría médica)
# ========================================
logger = logging.getLogger(__name__)

# ========================================
# CONSTANTES FÍSICAS Y CLÍNICAS
# ========================================
FACTOR_CONVERSION_PTM = 51.71499   # mmHg/kPa (estándar clínico histórico)
FACTOR_CONVERSION_CICLOS = 1800.0  # ciclos → mL/min
OFFSET_CALIBRACION = 0.05          # compensación mecánica

# Límites clínicos reales (según Fresenius 5008, Baxter, etc.)
PTM_LIMITE = (-100, 600)           # mmHg
FLUJO_SANGRE_LIMITE = (0, 600)     # mL/min
CICLOS_LIMITE = (0, 1000)          # ciclos típicos

def calculo_ptm(
    pd_ef: Optional[float],
    pd_sf: Optional[float],
    pa: Optional[float],
    pv: Optional[float]
) -> float:
    """
    Cálculo de Presión Transmembrana (PTM) - Fórmula clínica estándar.
    
    PTM = (PA + PV)/2 - 51.71499 × (PD_EF + PD_SF)/2
    
   """
    if None in (pd_ef, pd_sf, pa, pv):
        logger.warning("PTM: Valor nulo recibido → devolviendo 0.0")
        return 0.0

    try:
        presion_sanguinea = (pa + pv) / 2
        presion_dializante_kpa = (pd_ef + pd_sf) / 2
        presion_dializante_mmhg = presion_dializante_kpa * FACTOR_CONVERSION_PTM
        
        ptm = presion_sanguinea - presion_dializante_mmhg
        
        # Clamping de seguridad
        ptm = max(PTM_LIMITE[0], min(PTM_LIMITE[1], ptm))
        
        return round(ptm, 1)
        
    except Exception as e:
        logger.error(f"Error crítico en cálculo PTM: {e}")
        return 0.0


def convertir_ciclos_a_flujo(n_ciclos: float) -> float:
    """
    Convierte ciclos de máquina → flujo sanguíneo real (mL/min)
    Fórmula clínica: 1800 / (ciclos + 0.05)
    """
    if not isinstance(n_ciclos, (int, float)) or n_ciclos <= 0:
        return 0.0

    try:
        flujo = FACTOR_CONVERSION_CICLOS / (n_ciclos + OFFSET_CALIBRACION)
        flujo = max(FLUJO_SANGRE_LIMITE[0], min(FLUJO_SANGRE_LIMITE[1], flujo))
        return round(flujo, 1)  # ← 1 decimal como en equipos reales
    except Exception:
        return 0.0


def convertir_flujo_a_ciclos(flujo_objetivo: float) -> float:
    """
    Calcula ciclos necesarios para alcanzar un flujo objetivo.
    Fórmula inversa: (1800 / flujo) - 0.05
    """
    if not isinstance(flujo_objetivo, (int, float)) or flujo_objetivo <= 0:
        return 0.0

    try:
        ciclos = (FACTOR_CONVERSION_CICLOS / flujo_objetivo) - OFFSET_CALIBRACION
        return max(0.0, round(ciclos, 3))  # 3 decimales para precisión de control
    except Exception:
        return 0.0
    
# ========================================
# CONSTANTES DE CONVERSIÓN (UF)
# ========================================
ML_POR_LITRO = 1000.0
SEGUNDOS_POR_MINUTO = 60.0

# Límites clínicos reales de UF
UF_MAX_LITROS_POR_HORA = 4.0    # 4000 mL/h → máximo típico
UF_MAX_ML_POR_MINUTO = UF_MAX_LITROS_POR_HORA * 1000 / 60  # ≈ 66.67 mL/min


def convertir_litros_h_a_ml_min(litros_por_hora: Optional[float]) -> float:
    """
    Convierte tasa de ultrafiltración de L/h → mL/min
    
    Uso típico:
        - Setpoint UF del médico: 2.0 L/h
        - Bomba UF trabaja en mL/min
    
    Fórmula: (litros/h × 1000) / 60
    
    :param litros_por_hora: Tasa en litros por hora (ej: 2.0)
    :return: Tasa en mL/min (ej: 33.3), redondeada a 1 decimal
    """
    if litros_por_hora is None or litros_por_hora < 0:
        logger.warning(f"UF inválida (L/h): {litros_por_hora} → devolviendo 0.0")
        return 0.0

    try:
        ml_min = (litros_por_hora * ML_POR_LITRO) / SEGUNDOS_POR_MINUTO
        
        # Clamping de seguridad
        if ml_min > UF_MAX_ML_POR_MINUTO:
            logger.warning(f"UF muy alta: {ml_min:.1f} mL/min → limitando a {UF_MAX_ML_POR_MINUTO:.1f}")
            ml_min = UF_MAX_ML_POR_MINUTO
            
        return round(ml_min, 1)
        
    except Exception as e:
        logger.error(f"Error en conversión L/h → mL/min: {e}")
        return 0.0


def convertir_ml_min_a_litros_h(ml_por_minuto: Optional[float]) -> float:
    """
    Convierte tasa de ultrafiltración de mL/min → L/h
    
    Uso típico:
        - Bomba UF reporta 33.3 mL/min
        - Pantalla muestra 2.0 L/h
    
    Fórmula: (mL/min × 60) / 1000
    """
    if ml_por_minuto is None or ml_por_minuto < 0:
        logger.warning(f"UF inválida (mL/min): {ml_por_minuto} → devolviendo 0.0")
        return 0.0

    try:
        litros_h = (ml_por_minuto * SEGUNDOS_POR_MINUTO) / ML_POR_LITRO
        
        if litros_h > UF_MAX_LITROS_POR_HORA:
            logger.warning(f"UF muy alta: {litros_h:.2f} L/h → limitando")
            litros_h = UF_MAX_LITROS_POR_HORA
            
        return round(litros_h, 2)  # 2 decimales como en equipos reales
        
    except Exception as e:
        logger.error(f"Error en conversión mL/min → L/h: {e}")
        return 0.0
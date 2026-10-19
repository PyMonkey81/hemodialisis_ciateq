"""
Módulo de cálculo de volumen ultrafiltrado.

Define la constante de desplazamiento de la bomba UF y proporciona
funciones para calcular el volumen removido en litros a partir del
acumulado de pulsos de la bomba.
"""

# Desplazamiento de la bomba UF
# TODO: Reemplazar por el valor real del desplazamiento en ml por pulso
# de la hoja de datos del fabricante de la bomba UF
UF_PUMP_ML_PER_PULSE = 1.0  # ml por pulso


def litros_removidos(pulsos: int) -> float:
    """
    Calcula el volumen ultrafiltrado en litros a partir del número de pulsos.
    
    Args:
        pulsos: Número acumulado de pulsos de la bomba UF (debe ser ≥ 0)
    
    Returns:
        Volumen removido en litros, con precisión de 2 decimales.
        Si pulsos < 0, retorna 0.0.
    
    Fórmula:
        litros = pulsos × UF_PUMP_ML_PER_PULSE / 1000
    
    Ejemplos:
        litros_removidos(1000) → 1.00 L (con 1.0 ml/pulso)
        litros_removidos(-100) → 0.00 L (pulsos negativos devuelven 0)
    """
    if pulsos < 0:
        return 0.0
    
    litros = (pulsos * UF_PUMP_ML_PER_PULSE) / 1000.0
    return round(litros, 2)

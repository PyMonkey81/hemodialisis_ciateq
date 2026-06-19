#logic/heitmann.py

import logging

logger = logging.getLogger(__name__)

def heitmann(Z: float, H: float, W: float, G: int, E: int) -> float:
    """
    Calcula el Agua Corporal Total (TBW) usando fórmula de Heitmann.
    Retorna solo el volumen en LITROS (o None si Z es inválido).
    Parámetros:
        Z (float): Impedancia o resistencia en Ohmios.
        H (float): Altura del paciente en cm.
        W (float): Peso del paciente en kg.
        G (int): Género del paciente (1 = hombre, 0 = mujer).
        E (int): Edad del paciente en años.
        """
    a = 0.266
    b = 0.186
    c = 4.702
    d = 0.081
    k = 12.44

    if Z <= 0 or W <= 0 or H <= 0:
        logger.warning(f"[Heitmann] Datos inválidos para cálculo: Z={Z}")
        return None

    try:
        TBW = (a * (H ** 2) / Z) + b * W + c * G - d * E - k
        return round(TBW, 2)
    except Exception as e:
        logger.error(f"[Heitmann] Error en cálculo: {e}")
        return None
#logic/heitmann.py


def heitmann(Z, H, W, G, E):
    """
    Calcula el Agua Corporal Total (TBW) y su porcentaje usando la fórmula de Heitmann et al.

    Parámetros:
    Z (float): Impedancia o resistencia en Ohmios.
    H (float): Altura del paciente en cm.
    W (float): Peso del paciente en kg.
    G (int): Género del paciente (1 = hombre, 0 = mujer).
    E (int): Edad del paciente en años.

    Retorna:
    tuple[float, float] | tuple[None, None]: TBW en Litros y %TBW del peso, o (None, None) si Z es inválido.
    """
    a = 0.266
    b = 0.186
    c = 4.702
    d = 0.081
    k = 12.44

    if Z <= 0:
        return None, None

    # Fórmula de Heitmann
    TBW = (a * (H ** 2) / Z) + b * W + c * G - d * E - k
    pct = (TBW / W * 100) if W > 0 else None

    return round(TBW, 2), round(pct, 2) if pct is not None else None
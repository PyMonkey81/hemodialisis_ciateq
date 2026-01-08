from typing import Dict, Tuple

# Supongamos que esta es tu estructura de diccionario (VARIABLES)
VARIABLES: Dict[int, Dict[int, Dict]] = {
    0x02: {
        0x00: {"name": "Presión intermembrana", "type": "double", "rw": True, "unit": "mmHg", "limites": (1, 100)},
        0x01: {"name": "Variable clínica visualización 1", "type": "double", "rw": True, "unit": "NA", "limites": (0, 100)},
        # ... otras variables ...
    },
    # ... otros grupos de variables (0x01, etc.)
}

def actualizar_limites_variables(grupo: int, direccion: int, nuevo_minimo: float, nuevo_maximo: float) -> bool:
    """
    Actualiza los límites (min y max) de una variable específica en el mapa VARIABLES.

    Args:
        grupo: El grupo de la variable (ej: 0x02 para analógicas).
        direccion: La dirección o índice de la variable dentro del grupo (ej: 0x00).
        nuevo_minimo: El nuevo valor mínimo para el límite.
        nuevo_maximo: El nuevo valor máximo para el límite.

    Returns:
        True si los límites se actualizaron con éxito, False en caso contrario.
    """
    if grupo in VARIABLES:
        if direccion in VARIABLES[grupo]:
            # Validación simple para asegurar que el mínimo no sea mayor que el máximo
            if nuevo_minimo < nuevo_maximo:
                # Accede al diccionario de la variable y actualiza la clave 'limites'
                VARIABLES[grupo][direccion]["limites"] = (nuevo_minimo, nuevo_maximo)
                print(f"[OK] Límites de '{VARIABLES[grupo][direccion]['name']}' actualizados a ({nuevo_minimo}, {nuevo_maximo})")
                return True
            else:
                print(f"[ERROR] El mínimo ({nuevo_minimo}) debe ser menor que el máximo ({nuevo_maximo}).")
                return False
        else:
            print(f"[ERROR] Dirección 0x{direccion:02X} no encontrada en el grupo 0x{grupo:02X}.")
            return False
    else:
        print(f"[ERROR] Grupo 0x{grupo:02X} no encontrado en VARIABLES.")
        return False

# --- Ejemplo de Uso ---
# 1. Variables antes del cambio
presion_actual = VARIABLES[0x02][0x00]["limites"]
print(f"Límites originales de Presión intermembrana: {presion_actual}")

# 2. Llamada para actualizar los límites
actualizar_limites_variables(grupo=0x02, direccion=0x00, nuevo_minimo=5.0, nuevo_maximo=150.0)

# 3. Variables después del cambio
presion_nueva = VARIABLES[0x02][0x00]["limites"]
print(f"Límites nuevos de Presión intermembrana: {presion_nueva}")
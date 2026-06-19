#logic/ktv_calculator.py
        
import math
import logging 
logger = logging.getLogger(__name__) # Inicializa el logger para esta clase

class CalculadoraKtV:
    def __init__(self, parent=None, values_dict=None):
        
        self.parent_windows = parent # Si necesitas referencia a la ventana principal
        self.current_values = values_dict if values_dict is not None else {} # Para valores iniciales si los hay
        self.reset()

    def reset(self):
        """Reinicia todos los valores acumulados para un nuevo ciclo de cálculo de Kt/V."""
        self.dilisancias_acumuladas = [] 
        self.tiempo_inicio = None 
        self.volumen_distribucion_v = 0.0 
        self.parametros_antropometricos = {} 

        # --- Variables CRÍTICAS para almacenar las conductividades de los dos puntos ---
        self._cd_in_t1: float = 0.0
        self._cd_out_t1: float = 0.0
        self._temp_t1: float = 0.0 # Temperatura del dializado en el punto T1

        self._cd_in_t2: float = 0.0
        self._cd_out_t2: float = 0.0
        self._temp_t2: float = 0.0 # Temperatura del dializado en el punto T2
        
        logger.debug("[KTV_CALC] CalculadoraKtV reiniciada.")

    def config_paciente(self, peso: float, altura: float, edad: int, genero: int):
        """
        Configura los parámetros antropométricos del paciente y calcula el Volumen (V)
        usando la fórmula de Watson si no hay datos de bioimpedancia.
        V se guarda en mL.
        """
        self.parametros_antropometricos = {
            "peso": peso, "altura": altura, "edad": edad, "genero": genero
        }

        # Ecuaciones de Watson (V en litros)
        v_litros = 0.0
        if genero == 1: # Hombre
            v_litros = 2.447 - (0.09156 * edad) + (0.1074 * altura) + (0.3362 * peso)
        elif genero == 2: # Mujer
            v_litros = -2.097 + (0.1069 * altura) + (0.2466 * peso)
        else:
            logger.warning(f"[KTV_CALC] Género '{genero}' no reconocido. No se puede usar Watson.")
            
        self.volumen_distribucion_v = v_litros * 1000 # Convertir a mL y almacenar
        logger.debug(f"[KTV_CALC] Volumen de Watson calculado: {self.volumen_distribucion_v:.2f} mL")


    def set_volumen_bioimpedancia(self, v_bis_litros: float):
        """
        Establece el Volumen (V) directamente desde una lectura de Bioimpedancia.
        V se guarda en mL.
        """
        if v_bis_litros > 0:
            self.volumen_distribucion_v = v_bis_litros * 1000 # Convertir a mL
            logger.debug(f"[KTV_CALC] Volumen de Bioimpedancia establecido: {self.volumen_distribucion_v:.2f} mL")
        else:
            logger.warning(f"[KTV_CALC] Volumen de Bioimpedancia no válido: {v_bis_litros} L. No se actualizará V.")


    def store_conductivity_t1(self, cd_in: float, cd_out: float, temp: float):
        """
        Almacena las lecturas de conductividad (entrada, salida) y temperatura
        en el tiempo 1 (conductividad inicial del dializado).
        """
        self._cd_in_t1 = cd_in
        self._cd_out_t1 = cd_out
        self._temp_t1 = temp
        logger.debug(f"[KTV_CALC] T1 almacenado: CdIn={cd_in:.2f}, CdOut={cd_out:.2f}, Temp={temp:.2f}")

    def store_conductivity_t2(self, cd_in: float, cd_out: float, temp: float):
        """
        Almacena las lecturas de conductividad (entrada, salida) y temperatura
        en el tiempo 2 (conductividad del dializado después del 'paso' de cambio).
        """
        self._cd_in_t2 = cd_in
        self._cd_out_t2 = cd_out
        self._temp_t2 = temp
        logger.debug(f"[KTV_CALC] T2 almacenado: CdIn={cd_in:.2f}, CdOut={cd_out:.2f}, Temp={temp:.2f}")

    def calculate_ktv_ionic(
        self, 
        qd: float, 
        qf: float, 
        qb: float, 
        t_min: float, 
        r: float = 0.0
    ) -> float:
        """
        Calcula el Kt/V iónico utilizando el método de dos puntos de conductividad.
        Versión mejorada con límites realistas y mayor robustez.
        """
        if self.volumen_distribucion_v <= 0:
            logger.error("[KTV_CALC] Error: Volumen de distribución (V) no válido. Kt/V = 0.0")
            return 0.0

        # Usar valores almacenados
        cd_in_1 = self._cd_in_t1
        cd_in_2 = self._cd_in_t2
        cd_out_1 = self._cd_out_t1
        cd_out_2 = self._cd_out_t2

        # Validación importante: ¿Tenemos los dos puntos?
        if abs(cd_in_2 - cd_in_1) < 0.1:
            logger.warning("[KTV_CALC] Delta de conductividad de entrada demasiado pequeño. "
                          f"Delta Cd_in = {cd_in_2 - cd_in_1:.3f}")
            return 0.0

        # Temperatura: usamos promedio si ambos puntos tienen temperatura
        if self._temp_t1 > 0 and self._temp_t2 > 0:
            temp = (self._temp_t1 + self._temp_t2) / 2
        else:
            temp = self._temp_t2 if self._temp_t2 > 0 else 37.0

        # Delta de conductividad
        delta_cd_in = cd_in_2 - cd_in_1
        delta_cd_out = cd_out_2 - cd_out_1

        # Corrección por temperatura (alpha ≈ 2.1% por °C)
        alpha = 0.021
        delta_cd_in_cor = delta_cd_in * (1 + alpha * (temp - 25))
        delta_cd_out_cor = delta_cd_out * (1 + alpha * (temp - 25))

        # Cálculo de la dialisancia iónica básica
        if abs(delta_cd_in_cor) < 0.05:   # Protección extra contra división por cero o ruido
            logger.warning("[KTV_CALC] Delta Cd_in corregido muy pequeño. No se puede calcular D.")
            return 0.0
        
        qf = (qf * 1000) / 60
        d = (qd + qf) * (1 - (delta_cd_out_cor / delta_cd_in_cor))

        # ==================== LÍMITE SUPERIOR REALISTA ====================
        d_max = qd + qf + 40.0          # Margen físico razonable (difusión + convección)
    
        # Limitamos la dialisancia
        d = max(0.0, min(d, d_max))

        # ==================== CORRECCIÓN POR RECIRCULACIÓN ====================
        d_efectiva = d
        
        if qb > 50 and d > 0 and r > 0.0:        # Solo aplicar si hay recirculación significativa
            denom = 1 - r * (1 - d / qb)
            if abs(denom) > 0.001:               # Evitar división por cero
                d_efectiva = d * ((1 - r) / denom)
            else:
                logger.warning("[KTV_CALC] Denominador de recirculación cercano a cero.")

        # Evitamos que la recirculación haga que D_efectiva sea mayor que D
        d_efectiva = min(d_efectiva, d)

        # ==================== CÁLCULO FINAL Kt/V ====================
        ktv = (d_efectiva * t_min) / self.volumen_distribucion_v

        # Logging útil para debugging
        logger.info(f"[KTV_CALC] D={d:.1f} mL/min | D_efectiva={d_efectiva:.1f} mL/min | "
                    f"QF={qf:.1f} | Temp={temp:.1f}°C | Kt/V={ktv:.3f}")
        
        print(f"[KTV_CALC] D={d:.1f} mL/min | D_efectiva={d_efectiva:.1f} mL/min | "
              f"QF={qf:.1f} | Temp={temp:.1f}°C | Kt/V={ktv:.3f}")

        return max(0.0, round(ktv, 2))

#logic/ktv_calculator.py

import math
import logging
logger = logging.getLogger(__name__) # Inicializar el logger
from logic import ktv

class CalculadoraKtV:
    def __init__(self, parent=None, values_dict=None):
        super().__init__(parent)
        self.parent_windows = parent
        self.current_values = values_dict if values_dict is not None else {}
        self.reset()

    def reset(self):
        self.dilisancias_acumuladas = []
        self.tiempo_inicio = None
        self.volumen_distribucion_v = 0.0
        self.parametros_antropometricos = {}
        
        # Nuevas variables para el método de dos puntos
        self.cd_in_1 = None
        self.cd_out_1 = None
        self.cd_in_2 = None
        self.cd_out_2 = None
        self.tiempo_medicion_1 = None
        self.tiempo_medicion_2 = None
    
    def config_paciente(self, peso, altura, edad, genero):
        """Clcula V usando Watson si no hay bioimpedancia disponible"""
        self.parametros_antropometricos = {
            "peso": peso, "altura": altura, "edad": edad, "genero":genero
        }

        # Ecuaciones de Watson (V en litros)
        if genero == "M": # Hombre
            v = 2.447 - (0.09156 * edad) + (0.1074 * altura) + (0.3362 * peso)
        else: # Mujer
            v = -2.097 + (0.1069 * altura) + (0.2466 * peso)

        self.volumen_distribucion_v = v * 1000 #convertir a ml

    def set_volumen_bioimpedancia(self, v_bis_litros):
        """Si se tiene dato directo de sensores BIS"""
        self.volumen_distribucion_v =  v_bis_litros * 1000 # convertir a ml

    def calc_dialisancia_inst(self, qd, qf, cd_in_1, cd_in_2, cd_out_1, cd_out_2, Temp):
        """ Calcula D (dialisancia Iónica) usando el método de dos puntos. Requiere
        que la máquina cambie la conductividad en entrada intencionamente (paso de conductividad)
        para obtener los estados 1 y 2"""
        alpha = 0.0021 # Coeficiente de temperatura para conductividad  (°C)
        try: 
            delta_cd_in = cd_in_2 - cd_in_1
            delta_cd_out = cd_out_2- cd_out_1

            d_cd_in_cor = delta_cd_in * (1 + alpha * (Temp - 25))
            d_cd_out_cor = delta_cd_out * ( 1 + alpha * (Temp - 25))

            if abs(d_cd_in_cor) < 0.1: # evita división por cero o ruido de sensores
                return 0.0
            
            d = (qd + qf) * (1 - (d_cd_out_cor / d_cd_in_cor))

            d = max(0, min(d, qd + qf))

            return d
        except ZeroDivisionError:
            return 0.0
        
    def calculo_ktv_acumulado(self, d_actual, tiempo_transcurrido_min):
        """ Calcula kt/V en tiempo real.
        kt/V = (K * t) / V"""

        if self.volumen_distribucion_v <= 0:
            return 0.0
        
        kt = d_actual * tiempo_transcurrido_min
        kt_v = kt / self.volumen_distribucion_v

        return kt_v
    
    def logic_ktv(
        cd_in_1: float, cd_in_2: float,
        cd_out_1: float, cd_out_2: float,
        qd: float, qf: float, qb: float,
        t_min: float, v_bis: float,
        temp: float = 25.0, r: float = 0.0
    ) -> float:
        # ΔCd - Diferencia de conductividad
        delta_cd_in = cd_in_2 - cd_in_1
        delta_cd_out = cd_out_2 - cd_out_1

        if delta_cd_in == 0:
            return 0.0

        # Corrección temperatura
        alpha = 0.021
        delta_cd_in_cor = delta_cd_in * (1 + alpha * (temp - 25))
        delta_cd_out_cor = delta_cd_out * (1 + alpha * (temp - 25))

        # D básica - determinación de la Dialisancia iónica
        d = (qd + qf) * (1 - (delta_cd_out_cor / delta_cd_in_cor))

        # Corrección recirculación
        if qb > 0:
            d_efectiva = d * ((1 - r) / (1 - r * (1 - d / qb)))
        else:
            d_efectiva = d

        # Kt/V
        ktv = (d_efectiva * t_min) / v_bis
        return max(0.0, round(ktv, 2))
    
    def measure_conductivity(self, cd_in: float, cd_out: float, tiempo_min: float):
        """Captura las conductividades en dos momentos diferentes"""
        if self.cd_in_1 is None:
            # Primera medición
            self.cd_in_1 = cd_in
            self.cd_out_1 = cd_out
            self.tiempo_medicion_1 = tiempo_min
            logger.info(f"[Kt/V] Capturada medición 1: Cd_in={cd_in:.2f}, Cd_out={cd_out:.2f}")
        else:
            # Segunda medición
            self.cd_in_2 = cd_in
            self.cd_out_2 = cd_out
            self.tiempo_medicion_2 = tiempo_min
            logger.info(f"[Kt/V] Capturada medición 2: Cd_in={cd_in:.2f}, Cd_out={cd_out:.2f}")
    
    def update_values(self, new_values: dict):
        """Actualiza los valores necesarios para el cálculo de Kt/V en tiempo real"""
            # Aquí se podrían actualizar parámetros como qd, qf, cd_in, cd_out, etc.
        self.current_values = new_values

        cd_in_1 = self.current_values.get("dialyConductIFProcessData", 13.0)
        cd_in_2 = self.current_values.get("dialyConductIFProcessData", 14.0)  # segunda medición
        cd_out_1 = self.current_values.get("dialyConductOFProcessData", 13.0)
        cd_out_2 = self.current_values.get("dialyConductOFProcessData", 14.0)
        qd = self.current_values.get("dialyFlowControlOutput", 500)
        qf = self.current_values.get("ultraFilterPumpSpeed", 10)
        qb = self.current_values.get("bloodFlowVariableData", 300)
        t_min = self.current_values.get("heparineTherapyHours", 4) * 60  # convertir horas a min
        min_ = self.current_values.get("heparineTherapyMinutes",59)
        total_min = t_min + min_
        v_bis = self.current_values.get("V_BIS", 40.0)  

  
        
import math
import logging # Asegúrate de que el logger esté configurado en tu app principal

logger = logging.getLogger(__name__) # Inicializa el logger para esta clase

class CalculadoraKtV:
    def __init__(self, parent=None, values_dict=None):
        # El 'parent' no se usa en este contexto de lógica pura, pero lo mantenemos si lo necesitas para Qt
        # super().__init__(parent) # Solo si CalculadoraKtV hereda de QObject, sino eliminar
        self.parent_windows = parent # Si necesitas referencia a la ventana principal
        self.current_values = values_dict if values_dict is not None else {} # Para valores iniciales si los hay
        self.reset()

    def reset(self):
        """Reinicia todos los valores acumulados para un nuevo ciclo de cálculo de Kt/V."""
        self.dilisancias_acumuladas = [] # No usado en el cálculo iónico de dos puntos, pero lo mantengo si es para otros usos.
        self.tiempo_inicio = None # No usado en este contexto específico.
        self.volumen_distribucion_v = 0.0 # Volumen de distribución de urea en mL
        self.parametros_antropometricos = {} # Para almacenar datos del paciente si se usa Watson

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


    # def calculate_ktv_ionic(
    #     self, qd: float, qf: float, qb: float, t_min: float, r: float = 0.0
    # ) -> float:
    #     """
    #     Calcula el Kt/V iónico utilizando el método de dos puntos de conductividad
    #     y los valores de T1 y T2 previamente almacenados.
        
    #     Args:
    #         qd (float): Flujo de dializado (mL/min).
    #         qf (float): Tasa de ultrafiltración (mL/min).
    #         qb (float): Flujo sanguíneo (mL/min).
    #         t_min (float): Tiempo de diálisis transcurrido en minutos.
    #         r (float): Coeficiente de recirculación (0.0 a 1.0), por defecto 0.
            
    #     Returns:
    #         float: El valor calculado de Kt/V, redondeado a 2 decimales.
    #     """
    #     if self.volumen_distribucion_v <= 0:
    #         logger.error("[KTV_CALC] Error: Volumen de distribución (V) no válido. Kt/V no calculable.")
    #         return 0.0
    #     print(f"[KTV_CALC] Iniciando cálculo de Kt/V con V={self.volumen_distribucion_v:.2f} mL")
    #     # Usamos los valores almacenados para el cálculo
    #     cd_in_1 = self._cd_in_t1
    #     cd_in_2 = self._cd_in_t2
    #     cd_out_1 = self._cd_out_t1
    #     cd_out_2 = self._cd_out_t2
    
    #     # Por simplicidad, usaremos la temperatura del punto T2
    #     # para la corrección en el momento del cambio.
    #     temp = self._temp_t2 

    #     # ΔCd - Diferencia de conductividad
    #     delta_cd_in = cd_in_2 - cd_in_1
    #     delta_cd_out = cd_out_2 - cd_out_1
    #     print(f"[KTV_CALC] ΔCd_in={delta_cd_in:.2f}, ΔCd_out={delta_cd_out:.2f}")

    #     if abs(delta_cd_in) < 0.1: # Evita división por cero o un cambio insignificante
    #         logger.warning("[KTV_CALC] Delta Cd_in es insignificante o cero. No se puede calcular dialisancia.")
    #         return 0.0

    #     # Corrección temperatura (a 25°C)
    #     alpha = 0.021 # Coeficiente de temperatura para conductividad del dializado (aprox.)
    #     delta_cd_in_cor = delta_cd_in * (1 + alpha * (temp - 25))
    #     delta_cd_out_cor = delta_cd_out * (1 + alpha * (temp - 25))

    #     # D básica - determinación de la Dialisancia iónica
    #     # La fórmula es D = Qd + Qf * (1 - (ΔCd_out_cor / ΔCd_in_cor))
    #     # O la forma simplificada si Qf es pequeño
    #     # Aquí usando la versión más común que incluye Qf
    #     d = (qd + qf) * (1 - (delta_cd_out_cor / delta_cd_in_cor))
        
    #     d = max(0.0, min(d, qd + qf + 40))
    #     # if qf > 0:
    #     #     d = max(0.0, min(d, qd + qf + qb * 2)) 
    #     # else:      
    #     #     d = max(0.0, min(d, qd * 1.2))

    #     # Corrección recirculación (si aplica)
    #     d_efectiva = d
    #     if qb > 0 and d > 0: # Aplicar corrección solo si hay flujo sanguíneo y dialisancia
    #         # Fórmula para corregir por recirculación, ajustada para que no haya división por cero
    #         denom = (1 - r * (1 - d / qb))
    #         if denom != 0:
    #             d_efectiva = d * ((1 - r) / denom)
    #         else:
    #             logger.warning("[KTV_CALC] Denominador de corrección por recirculación es cero. No se aplica.")

    #     # Kt/V = (K * t) / V
    #     # K (aclaramiento) es la dialisancia efectiva (D_efectiva) en mL/min
    #     # t (tiempo) en minutos
    #     # V (volumen) en mL
    #     ktv = (d_efectiva * t_min) / self.volumen_distribucion_v
        
    #     logger.info(f"[KTV_CALC] Cálculos intermedios: D={d:.2f}, Deff={d_efectiva:.2f}, V={self.volumen_distribucion_v:.2f} mL")
    #     return max(0.0, round(ktv, 2))
    

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

        # Diferencias de conductividad
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

        d = (qd + qf) * (1 - (delta_cd_out_cor / delta_cd_in_cor))

        # ==================== LÍMITE SUPERIOR REALISTA ====================
        # Este es el cambio más importante que te recomendaba
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

        return max(0.0, round(ktv, 2))

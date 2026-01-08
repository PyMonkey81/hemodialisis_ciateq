#logic/ktv_calculator.py

import math

class CalculadoraKtV:
    def __init__(self):
        self.reset()

    def reset(self):
        self.dilisancias_acumuladas = []
        self.tiempo_inicio = None
        self.volumen_distribucion_v = 0.0
        self.parametros_antropometricos = {}
    
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
    
        

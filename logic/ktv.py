# logic/ktv.py
def calcular_ktv(
    cd_in1: float, cd_in2: float,
    cd_out1: float, cd_out2: float,
    qd: float, qf: float, qb: float,
    t_min: float, v_bis: float,
    temp: float = 25.0, r: float = 0.0
) -> float:
    # ΔCd - Diferencia de conductividad
    delta_cd_in = cd_in2 - cd_in1
    delta_cd_out = cd_out2 - cd_out1

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

# En dialysisScreen.py
def actualizar_valores(self, valores_dict):
    self.valores = valores_dict

    # Ejemplo de parámetros
    cd_in1 = self.valores.get("dialyConductIFProcessData", 13.0)
    cd_in2 = self.valores.get("dialyConductIFProcessData", 14.0)  # segunda medición
    cd_out1 = self.valores.get("dialyConductOFProcessData", 13.0)
    cd_out2 = self.valores.get("dialyConductOFProcessData", 14.0)
    qd = self.valores.get("dialyFlowControlOutput", 500)
    qf = self.valores.get("ultraFilterPumpSpeed", 10)
    qb = self.valores.get("bloodFlowVariableData", 300)
    t_min = self.valores.get("heparineTherapyHours", 4) * 60  # convertir horas a min
    v_bis = self.valores.get("V_BIS", 40.0)  # de bioimpedancia

    ktv = calcular_ktv(cd_in1, cd_in2, cd_out1, cd_out2, qd, qf, qb, t_min, v_bis, temp=37.0, r=0.05)
    self.ktv.setValor(ktv)
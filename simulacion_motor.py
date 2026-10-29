"""Calcula costos y ahorro operativo acumulados durante tres años."""
import pandas as pd

CATEGORIAS = ["CapEx (Única Vez)", "OpEx Fijo", "OpEx Variable", "Mantenimiento"]


def proyectar(costos, usuarios, crecimiento, ingreso_anual, eficiencia):
    costos = costos.copy()
    for columna in ["Costo Base Anual (COP)", "Costo Variable por Usuario (COP)"]:
        costos[columna] = pd.to_numeric(costos[columna], errors="coerce").fillna(0).clip(lower=0)
    capex = costos.loc[costos["Categoría"].eq(CATEGORIAS[0]), "Costo Base Anual (COP)"].sum()
    recurrentes = costos.loc[~costos["Categoría"].eq(CATEGORIAS[0])]
    activos, acumulado, beneficios = int(usuarios), float(capex), 0.0
    filas = []
    for i in range(3):
        if i:
            activos = int(activos * (1 + crecimiento / 100))
        operacion = float(recurrentes["Costo Base Anual (COP)"].sum() +
                          (recurrentes["Costo Variable por Usuario (COP)"] * activos).sum())
        acumulado += operacion
        beneficios += activos * ingreso_anual * eficiencia / 100
        filas.append({"Periodo Fiscal": f"Año {i + 1}", "Usuarios Activos": activos,
                      "Costo Anual Total (COP)": round(operacion + (capex if i == 0 else 0), 2),
                      "TCO Acumulado (COP)": round(acumulado, 2),
                      "Beneficio Acumulado (COP)": round(beneficios, 2),
                      "Utilidad Neta Acumulada (COP)": round(beneficios, 2) - round(acumulado, 2)})
    return pd.DataFrame(filas)


def proyectar_negocio(costos, usuarios, crecimiento, ingreso_anual,
                     conversion=100.0, cobro=100.0, churn_mensual=0.0,
                     marketing=0.0, otros_opex=0.0):
    """Proyección anual simplificada: usuarios constantes dentro de cada año.

    Churn se repone para cumplir el crecimiento neto; las altas del año 1
    incluyen toda la base inicial. CapEx se incluye en caja, no en el resultado
    operativo. No se modelan impuestos, depreciación ni cuentas por cobrar.
    """
    costos = costos.copy()
    for col in ["Costo Base Anual (COP)", "Costo Variable por Usuario (COP)"]:
        costos[col] = pd.to_numeric(costos[col], errors="coerce").fillna(0).clip(lower=0)
    capex = costos.loc[costos["Categoría"].eq(CATEGORIAS[0]), "Costo Base Anual (COP)"].sum()
    recurrentes = costos[~costos["Categoría"].eq(CATEGORIAS[0])]
    activos, plus_anterior = int(usuarios), 0
    filas = []
    for i in range(3):
        if i:
            activos = int(activos * (1 + crecimiento / 100))
        plus = int(activos * conversion / 100)
        bajas = plus_anterior * (1 - (1 - churn_mensual / 100) ** 12)
        altas = max(0.0, plus - plus_anterior + bajas)
        importes = recurrentes["Costo Base Anual (COP)"] + recurrentes["Costo Variable por Usuario (COP)"] * activos
        # Servicio tecnológico fijo/variable: COGS; mantenimiento: OPEX.
        cogs = float(importes[~recurrentes["Categoría"].eq(CATEGORIAS[3])].sum())
        mantenimiento = float(importes[recurrentes["Categoría"].eq(CATEGORIAS[3])].sum())
        opex = mantenimiento + marketing + otros_opex
        ingreso = plus * ingreso_anual
        recaudo = ingreso * cobro / 100
        inversion = float(capex) if i == 0 else 0.0
        filas.append({
            "Periodo Fiscal": f"Año {i + 1}", "Usuarios Activos": activos,
            "Usuarios Plus": plus, "Usuarios Cero": activos - plus,
            "MRR (COP)": ingreso / 12, "Ingreso devengado (COP)": ingreso,
            "Recaudo (COP)": recaudo, "COGS (COP)": cogs,
            "Margen bruto (COP)": ingreso - cogs, "OPEX (COP)": opex,
            "Marketing (COP)": marketing, "Altas Plus estimadas": altas,
            "Churn Plus mensual (%)": churn_mensual,
            "CapEx (COP)": inversion, "Costo TI (COP)": cogs + mantenimiento,
            "Resultado operativo (COP)": ingreso - cogs - opex,
            "TCO (COP)": cogs + opex + inversion,
            "Neto caja (COP)": recaudo - cogs - opex - inversion,
        })
        plus_anterior = plus
    return pd.DataFrame(filas)

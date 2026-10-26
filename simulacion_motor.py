"""Proyección a tres años con la misma lógica del simulador guía."""
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

"""Verifica la equivalencia del motor con las fórmulas del simulador guía."""

import unittest
import pandas as pd
from simulacion_motor import proyectar, proyectar_negocio


class ProyeccionTest(unittest.TestCase):
    def test_negocio_ingresos_costos_y_capex(self):
        costos = pd.DataFrame([
            {"Categoría": "CapEx (Única Vez)", "Costo Base Anual (COP)": 1000, "Costo Variable por Usuario (COP)": 0},
            {"Categoría": "OpEx Fijo", "Costo Base Anual (COP)": 100, "Costo Variable por Usuario (COP)": 2},
            {"Categoría": "Mantenimiento", "Costo Base Anual (COP)": 200, "Costo Variable por Usuario (COP)": 1},
        ])
        tabla = proyectar_negocio(costos, 100, 20, 299000, conversion=50,
                                 cobro=80, marketing=500, otros_opex=300)
        self.assertEqual(tabla["Usuarios Activos"].tolist(), [100, 120, 144])
        self.assertEqual(tabla["Usuarios Plus"].tolist(), [50, 60, 72])
        self.assertEqual(tabla["Ingreso devengado (COP)"].sum(), 54418000)
        self.assertEqual(tabla["COGS (COP)"].tolist(), [300, 340, 388])
        self.assertEqual(tabla["CapEx (COP)"].tolist(), [1000, 0, 0])
        self.assertEqual(tabla["OPEX (COP)"].tolist(), [1100, 1120, 1144])
        self.assertEqual(tabla.iloc[0]["Neto caja (COP)"], 14950000 * .8 - 2400)
        self.assertEqual(tabla.iloc[0]["Resultado operativo (COP)"], 14950000 - 1400)

    def test_churn_se_repone_y_roi_sin_costos(self):
        from metricas_ceroa import resumir
        costos = pd.DataFrame(columns=["Categoría", "Costo Base Anual (COP)", "Costo Variable por Usuario (COP)"])
        tabla = proyectar_negocio(costos, 100, 20, 299000, churn_mensual=10)
        self.assertAlmostEqual(tabla.iloc[1]["Altas Plus estimadas"], 20 + 100 * (1 - .9 ** 12))
        self.assertEqual(tabla["Ingreso devengado (COP)"].sum(), 108836000)
        self.assertIsNone(resumir(tabla)["ROI caja (%)"])
        self.assertIsNone(resumir(tabla)["ROI TI (%)"])

    def test_equivalencia_guia(self):
        costos = pd.DataFrame([
            {"Categoría": "CapEx (Única Vez)", "Costo Base Anual (COP)": 1800, "Costo Variable por Usuario (COP)": 0},
            {"Categoría": "OpEx Fijo", "Costo Base Anual (COP)": 960, "Costo Variable por Usuario (COP)": 0},
            {"Categoría": "OpEx Variable", "Costo Base Anual (COP)": 0, "Costo Variable por Usuario (COP)": .35},
            {"Categoría": "Mantenimiento", "Costo Base Anual (COP)": 1500, "Costo Variable por Usuario (COP)": 0},
        ])
        tabla = proyectar(costos, 1000, 50, 150, 15)
        self.assertEqual(tabla["Usuarios Activos"].tolist(), [1000, 1500, 2250])
        self.assertEqual(tabla["Costo Anual Total (COP)"].tolist(), [4610, 2985, 3247.5])
        self.assertEqual(tabla["TCO Acumulado (COP)"].tolist(), [4610, 7595, 10842.5])
        self.assertEqual(tabla["Beneficio Acumulado (COP)"].tolist(), [22500, 56250, 106875])

    def test_truncamiento_anual_como_guia_y_costo_cero(self):
        costos = pd.DataFrame(columns=["Categoría", "Costo Base Anual (COP)", "Costo Variable por Usuario (COP)"])
        tabla = proyectar(costos, 11, 10, 10, 15)
        self.assertEqual(tabla["Usuarios Activos"].tolist(), [11, 12, 13])
        self.assertEqual(tabla["TCO Acumulado (COP)"].sum(), 0)
        self.assertEqual(tabla.iloc[-1]["Beneficio Acumulado (COP)"], 54)


if __name__ == "__main__":
    unittest.main()

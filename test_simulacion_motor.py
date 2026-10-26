import unittest
import pandas as pd
from simulacion_motor import proyectar


class ProyeccionTest(unittest.TestCase):
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

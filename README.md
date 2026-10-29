# Ceroa

Dashboard del negocio y simulador financiero a tres años. Los importes se presentan en pesos colombianos (COP).

## Ejecutar en PowerShell

Desde la carpeta del proyecto:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app_ceroa.py
```

Abre http://localhost:8501. Para detener la aplicación, presiona Ctrl + C en la terminal.

En la barra lateral, selecciona **Histórico** o **Simulador a 3 años**. El simulador permite comparar los escenarios A (Serverless), B (plataforma gestionada) y C (servidores dedicados), con costos y supuestos editables. Los valores son ilustrativos para el ejercicio.

## Archivos necesarios

- `app_ceroa.py`: aplicación principal y carga de datos.
- `dashboard_ui.py`: estilos y formato de gráficas.
- `simulador_ceroa.py`: interfaz de los tres escenarios.
- `simulacion_motor.py`: cálculos de la proyección.
- `metricas_ceroa.py`: métricas comerciales proyectadas y comparación A/B/C.
- `GUIA_METRICAS.md`: significado de métricas, gráficas y supuestos; visible en ambas vistas.
- `datos/`: siete CSV del histórico.
- `Ceroa_Base_Datos_Recalculada.xlsx`: tarifas, supuestos, finanzas y catálogos.
- `test_simulacion_motor.py`: pruebas de los cálculos.

Los datos se buscan junto a `app_ceroa.py`, independientemente de la carpeta desde la que se ejecute el comando.

## Verificar cálculos

```powershell
py -m unittest test_simulacion_motor.py
```

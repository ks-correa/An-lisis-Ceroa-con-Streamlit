# Ceroa y el simulador guía

El simulador de Ceroa replica la estructura y lógica de Streamlit/evaluacion_proveedores.py. La guía permanece intacta.

- Barra lateral: usuarios iniciales, crecimiento anual, ingreso anual por usuario, ahorro/eficiencia y proveedor A, B o C.
- Una tabla editable para el proveedor seleccionado; las ediciones se conservan por proveedor durante la sesión.
- Cuatro tarjetas: CapEx inicial, TCO a tres años, beneficio operativo neto y ROI estimado.
- ROI comparado con meta de 100% acumulado a tres años, igual al supuesto de la guía. La diferencia se expresa en puntos porcentuales.
- Curva de TCO frente a beneficios acumulados, anillo de costos base por categoría y desglose anual.

Fórmulas idénticas a la guía: usuarios del año siguiente = entero de usuarios anteriores por (1 + crecimiento). Beneficio anual = usuarios por ingreso anual por usuario por porcentaje de eficiencia. El beneficio usado para ROI es ese ahorro, sin sumarle el ingreso bruto. CapEx se aplica una sola vez; los costos fijos, variables y mantenimiento se repiten cada año. ROI = (beneficio acumulado - TCO) / TCO por 100. Si TCO es cero, se muestra 0%, según la convención de la guía.

Los valores de ejemplo de la guía se convierten de USD a COP con la TRM de referencia de la hoja Supuestos. Esta no es una cotización actual. La conversión conserva el mismo ROI. La meta del 100% pertenece al ejercicio, no es un estándar de plataformas digitales.

El anillo muestra costos base por categoría, igual a la guía; no incluye costos variables por usuario. La tabla denomina utilidad acumulada al resultado acumulado que calcula la guía.

Ceroa: http://localhost:8501, Vista > Simulador a 3 años.
Guía: http://localhost:8502.
Dashboard histórico guía: http://localhost:8503.

La fórmula conserva equivalencia con la guía. El caso inicial se ajustó a 100 usuarios, 20% de crecimiento, $299.000 COP de ingreso anual por usuario y 15% de eficiencia. Son supuestos ilustrativos editables. ROI inicial: A -56,7%; B -63,0%; C -81,6%. Se verificaron los tres escenarios y la actualización de indicadores y gráficas al variar los parámetros.

La vista principal presenta cuatro indicadores y las dos gráficas de la guía: payback y anillo de costos con leyenda. Las tablas se encuentran plegadas en Ajustar costos del escenario y Ver desglose anual.


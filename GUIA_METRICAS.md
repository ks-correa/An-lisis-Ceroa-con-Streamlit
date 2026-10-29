# Cómo leer Ceroa

## Histórico y proyección

El histórico corresponde a los datos del ejercicio entre enero de 2025 y septiembre de 2026. «Todos», «Todos los planes» y «Todas las ciudades» muestran la operación completa. La simulación es un escenario hipotético a tres años, no la continuación automática del histórico ni una predicción validada.

Los usuarios y el MRR son valores **al cierre**, no se suman entre meses o años. Recaudo, ingresos, costos y resultados se acumulan en el período indicado. El histórico completo cubre 21 meses; la proyección cubre 36 meses, por lo que sus totales no se comparan directamente.

## Métricas del negocio

| Métrica | Qué significa y cómo se calcula |
|---|---|
| MRR | Ingreso mensual recurrente equivalente de las suscripciones activas. Una suscripción anual de $299.000 aporta $24.916,67 mensuales. Es ingreso generado, no necesariamente dinero recibido ese mes. |
| ARR equivalente | MRR × 12. Anualiza el ritmo de suscripciones del cierre; no es la suma de los ingresos del año pasado. |
| Recaudo efectivo | Dinero recibido por cobros aprobados durante el período. En la simulación es ingreso anual × porcentaje de cobro supuesto; no son transacciones observadas. |
| Ingreso devengado | Valor del servicio generado durante el período, aunque el cobro ocurra en otro momento. En la simulación: usuarios Plus × ingreso anual por usuario Plus. |
| COGS directo | Costos necesarios para prestar el servicio. Histórico: infraestructura, backups, pasarela, soporte, procesamiento de deudas y mensajería. Proyección: costos fijos y variables del proveedor; no incluye automáticamente todos los conceptos históricos. |
| Margen bruto | Ingreso devengado − COGS. El porcentaje es margen bruto / ingreso devengado × 100. Indica lo que queda antes de gastos operativos. |
| Usuarios activos | Personas únicas al cierre; no la suma de registros de usuario de todos los meses. En la proyección se supone una base constante durante cada año. |
| Conversión a Plus | Usuarios Plus / usuarios activos × 100. Es participación de pagos en la base al cierre; no una tasa de conversión de visitantes o de una cohorte. |
| Churn Plus | Porcentaje de suscriptores pagos que cancelan en un mes. Histórico: bajas / base Plus al inicio del mes. Proyección: supuesto mensual editable, inicialmente 0%; se estiman altas de reemplazo para sostener el crecimiento neto. |
| CAC por alta Plus | Marketing del período / altas Plus del período. En la proyección las altas incluyen los Plus iniciales y, luego, crecimiento y reposición del churn. Si marketing es cero el CAC calculado es cero; eso expresa el supuesto, no demuestra adquisición gratuita real. Sin altas se muestra N/D. |
| OPEX | Gastos operativos. Histórico: personal, marketing, administración, Workspace y herramientas. Proyección: mantenimiento del proveedor + marketing + otros gastos que ingreses. |
| Resultado operativo | Ingreso devengado − COGS − OPEX. No resta el CapEx inicial. El histórico muestra el mes de cierre y el acumulado en el texto inferior; la proyección muestra tres años acumulados. |
| TCO | Costo total de propiedad del período. Histórico: COGS + OPEX. Proyección del negocio: COGS + OPEX + CapEx inicial. No incluye costos omitidos en los supuestos. |
| Beneficio o neto de caja | Recaudo − TCO. Es una aproximación de caja del ejercicio, no un estado completo de flujos de efectivo. No incluye préstamos, impuestos ni otros movimientos no modelados. |
| ROI de caja o efectivo | (Recaudo − TCO) / TCO × 100. 0% significa cubrir los desembolsos modelados; 20% significa $20 netos por cada $100 de costo. Un valor negativo indica que el recaudo no cubre ese costo. |
| ROI devengado | Resultado operativo / (COGS + OPEX) × 100 en el histórico. No es el mismo indicador que el ROI de caja cuando recaudo e ingreso difieren. |
| ROI de infraestructura y proveedores TI | (Ingreso devengado − costo TI) / costo TI × 100. Histórico: costo TI = COGS + Workspace + administración. Simulación: servicio del proveedor + mantenimiento. Excluye otros gastos y el CapEx; su alcance es menor que el ROI de caja. No comparar sus cifras sin revisar esos rubros. |

## Métricas originales de inversión y ahorro

| Métrica | Significado |
|---|---|
| CapEx inicial | Desembolso de instalación, compra o migración, aplicado una sola vez. |
| TCO consolidado de inversión TI | CapEx + costos recurrentes del proveedor durante tres años. No contiene automáticamente personal, marketing ni otros gastos del negocio. |
| Beneficio por eficiencia | Usuarios de cada año × ingreso anual de referencia × eficiencia. Con eficiencia del 15%, solo toma el 15% de ese ingreso como ahorro hipotético. Es el modelo original del ejercicio y no se suma a los ingresos en las métricas del negocio. |
| Ahorro neto de costos TI | Beneficio por eficiencia acumulado − TCO del proveedor. Antes se llamaba «Beneficio Operativo Neto»; el nombre actual aclara su alcance. |
| ROI por ahorro | (Beneficio por eficiencia acumulado − TCO del proveedor) / TCO del proveedor × 100. Puede ser negativo aunque el ROI basado en suscripciones sea positivo, porque evalúan beneficios distintos. |
| Diferencia frente a meta | ROI por ahorro − 100%, expresado en puntos porcentuales. El 100% es una meta ilustrativa del ejercicio. No es el punto de recuperación: recuperar el costo corresponde a ROI 0%. |

## Gráficas del histórico

| Gráfica | Qué muestra |
|---|---|
| Ingresos y recaudo mensual | MRR generado cada mes frente al efectivo cobrado ese mes. Un pago anual puede elevar el recaudo de un mes mientras su ingreso se distribuye entre doce meses. |
| Usuarios por plan | Personas únicas al cierre en Cero, Plus mensual y Plus anual. No son usuarios acumulados durante los 21 meses. |
| Costos por proveedor | Acumulado por rubros seleccionados: pasarela, AWS/backups, soporte/deudas, Workspace y Telegram. No es todo el TCO: faltan otros gastos como personal y marketing. |
| Deudas y abonos mensuales | Saldo de deudas de los usuarios al cierre de cada mes y pagos hechos a acreedores durante ese mes. Son un saldo y un flujo distintos; ninguno es ingreso de Ceroa. |
| Recuperación de la inversión | TCO, recaudo e ingreso devengado acumulados. El cruce del recaudo con el costo indica cobertura de los costos modelados en caja; el cruce del ingreso corresponde al criterio devengado. |
| Distribución del costo total | Participación de los rubros mostrados en el anillo: pasarela, AWS/backups, soporte/deudas, marketing, personal y administración/Workspace. Otros conceptos como Telegram o n8n, si tienen costo, no aparecen en este anillo. |

Cuando filtras plan o ciudad, MRR, recaudo, usuarios y cartera siguen el segmento. Los costos y las curvas de recuperación permanecen globales. El ROI de caja compara el recaudo filtrado con esos costos globales: no es una rentabilidad atribuida al segmento.

## Gráficas del simulador

| Gráfica | Qué muestra |
|---|---|
| Curva de payback: inversión y beneficios | Costos TI acumulados frente al ahorro hipotético por eficiencia acumulado. No representa los cobros de suscripciones. Si el ahorro supera el costo, la inversión queda cubierta según ese supuesto. |
| Composición de costos por categoría | Distribución de los costos base de la plantilla del proveedor. Mezcla el CapEx de una vez con bases anuales; excluye variables por usuario. No es el TCO acumulado. |
| Ingresos y recaudo anuales | Ingreso anual de los Plus frente al efectivo supuesto de cada año. Con cobro del 100%, las líneas coinciden; una puede tapar a la otra. |
| Usuarios por plan y año | Evolución de usuarios gratuitos y Plus según el crecimiento neto y la participación Plus que indiques. No se separan Plus mensual y anual. |
| Recuperación con ingresos y recaudo acumulados | TCO completo de la simulación del negocio frente a ingresos y recaudo acumulados. Los cortes son anuales; no permite afirmar el mes exacto de recuperación. |
| Distribución del TCO de tres años | Costos acumulados por COGS, mantenimiento, marketing, otros gastos y CapEx. Aquí sí se incluyen costos variables y la inversión inicial una sola vez. |

## Supuestos iniciales

Con 100 usuarios, crecimiento del 20% e ingreso anual por usuario de $299.000: las bases son **100, 120 y 144 usuarios**. Con todos en Plus, los ingresos son **$29.900.000, $35.880.000 y $43.056.000**; total: **$108.836.000**. El MRR del año 3 es **$3.588.000** y su ARR equivalente es **$43.056.000**.

La proyección comercial arranca con 100% Plus, cobro del 100%, churn del 0%, marketing cero y otros gastos cero. Son supuestos editables, no valores inferidos del histórico. Si incorporas personal, administración, pasarela y otros costos, la rentabilidad disminuye. Los costos de los proveedores son ilustrativos, convertidos con la TRM del Excel; no son cotizaciones actuales.

Con los mismos supuestos comerciales, A, B y C tienen los mismos usuarios e ingresos; cambian sus costos, márgenes y retornos. Las ediciones de costos se conservan por proveedor durante la sesión.

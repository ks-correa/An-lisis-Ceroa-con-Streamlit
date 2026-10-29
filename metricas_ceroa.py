"""Indicadores del negocio comparables con la vista histórica."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_ui import mostrar_grafica
from simulacion_motor import proyectar_negocio


def resumir(tabla):
    cierre = tabla.iloc[-1]
    ingreso = tabla["Ingreso devengado (COP)"].sum()
    tco = tabla["TCO (COP)"].sum()
    ti = tabla["Costo TI (COP)"].sum()
    altas = tabla["Altas Plus estimadas"].sum()
    margen = tabla["Margen bruto (COP)"].sum()
    return {
        "MRR cierre (COP)": cierre["MRR (COP)"],
        "Recaudo 3 años (COP)": tabla["Recaudo (COP)"].sum(),
        "COGS 3 años (COP)": tabla["COGS (COP)"].sum(),
        "Margen bruto 3 años (COP)": margen,
        "Margen bruto (%)": margen / ingreso * 100 if ingreso else None,
        "Usuarios activos año 3": int(cierre["Usuarios Activos"]),
        "Conversión a Plus (%)": cierre["Usuarios Plus"] / cierre["Usuarios Activos"] * 100 if cierre["Usuarios Activos"] else 0,
        "Churn Plus mensual (%)": cierre["Churn Plus mensual (%)"],
        "CAC estimado (COP)": tabla["Marketing (COP)"].sum() / altas if altas else None,
        "Resultado operativo 3 años (COP)": tabla["Resultado operativo (COP)"].sum(),
        "TCO 3 años (COP)": tco,
        "Neto caja 3 años (COP)": tabla["Neto caja (COP)"].sum(),
        "ROI caja (%)": tabla["Neto caja (COP)"].sum() / tco * 100 if tco else None,
        "ROI TI (%)": (ingreso - ti) / ti * 100 if ti else None,
    }


def mostrar_metricas_negocio(plantillas, proveedor, usuarios, crecimiento, ingreso):
    st.subheader("Indicadores del negocio proyectados")
    st.caption("MRR y usuarios: cierre del año 3. Importes y ROI: acumulado de tres años. Churn: tasa mensual supuesta.")
    with st.expander("Supuestos comerciales y costos adicionales", expanded=False):
        st.markdown("Los valores iniciales suponen **100% de usuarios Plus, cobro del 100% y churn del 0%**. Todos los Plus se modelan con el ingreso anual indicado, sin separar plan mensual y anual. La base se mantiene constante dentro de cada año; el crecimiento se aplica al comenzar el siguiente.")
        a, b, c = st.columns(3)
        conversion = a.number_input("Usuarios que son Plus (%)", 0.0, 100.0, 100.0, key="neg_conversion")
        cobro = b.number_input("Ingreso cobrado en el año (%)", 0.0, 100.0, 100.0, key="neg_cobro")
        churn = c.number_input("Churn Plus mensual supuesto (%)", 0.0, 100.0, 0.0, key="neg_churn")
        marketing = a.number_input("Marketing anual (COP)", min_value=0.0, value=0.0, step=100000.0, key="neg_marketing")
        otros = b.number_input("Otros gastos operativos anuales (COP)", min_value=0.0, value=0.0, step=100000.0, key="neg_otros")
        st.caption("Los costos de proveedor fijo/variable se clasifican como COGS y el mantenimiento como OPEX. Marketing y otros gastos parten de cero: añade equipo, administración y demás costos antes de interpretar el resultado como el de toda Ceroa. No se incluyen impuestos, depreciación, comisiones de pasarela ni costos adicionales que no ingreses. Las altas estimadas incluyen la base inicial y la reposición del churn; este no reduce el crecimiento neto indicado.")

    tablas = {}
    for nombre, plantilla in plantillas.items():
        costos = st.session_state.get(f"guia_ceroa_items_{nombre}", pd.DataFrame(plantilla))
        tablas[nombre] = proyectar_negocio(costos, usuarios, crecimiento, ingreso,
                                        conversion, cobro, churn, marketing, otros)
    tabla = tablas[proveedor]
    resumen = resumir(tabla)
    for inicio in range(0, len(resumen), 4):
        for col, (nombre, valor) in zip(st.columns(4), list(resumen.items())[inicio:inicio + 4]):
            formato = "N/D" if valor is None else (f"${valor:,.0f}" if "COP" in nombre else (f"{valor:.2f}%" if "%" in nombre else f"{valor:,.0f}"))
            detalle = None
            if nombre == "MRR cierre (COP)":
                detalle = f"ARR equivalente: ${valor * 12:,.0f}"
            elif nombre == "Usuarios activos año 3":
                detalle = f"{int(tabla.iloc[-1]['Usuarios Cero']):,} Cero | {int(tabla.iloc[-1]['Usuarios Plus']):,} Plus"
            elif nombre == "Resultado operativo 3 años (COP)":
                detalle = f"Año 3: ${tabla.iloc[-1]['Resultado operativo (COP)']:,.0f}"
            col.metric(nombre, formato, delta=detalle, delta_color="off")
    st.caption("TCO proyectado = COGS + OPEX + CapEx inicial. El resultado operativo excluye CapEx; el neto de caja lo incluye. El ROI TI usa solo el servicio tecnológico y su mantenimiento. Con costo cero, el ROI es N/D.")

    st.subheader("Evolución del negocio proyectada")
    a, b = st.columns(2)
    with a:
        fig = px.line(tabla, x="Periodo Fiscal", y=["Ingreso devengado (COP)", "Recaudo (COP)"], markers=True, title="Ingresos y recaudo anuales")
        mostrar_grafica(fig)
        st.caption("Ingreso generado durante cada año y efectivo que se estima cobrar. MRR = ingreso anual / 12; no se compara directamente con un recaudo anual.")
    with b:
        usuarios_tabla = tabla.melt(id_vars="Periodo Fiscal", value_vars=["Usuarios Cero", "Usuarios Plus"], var_name="Plan", value_name="Usuarios")
        mostrar_grafica(px.bar(usuarios_tabla, x="Periodo Fiscal", y="Usuarios", color="Plan", title="Usuarios por plan y año"), tipo="usuarios")
        st.caption("Usuarios activos por año, separados entre gratuitos y pagos según el porcentaje Plus supuesto.")
    a, b = st.columns(2)
    with a:
        curva = tabla[["Periodo Fiscal"]].copy()
        for columna in ["TCO (COP)", "Ingreso devengado (COP)", "Recaudo (COP)"]:
            curva[columna] = tabla[columna].cumsum()
        mostrar_grafica(px.line(curva, x="Periodo Fiscal", y=list(curva.columns[1:]), markers=True, title="Recuperación con ingresos y recaudo acumulados"))
        st.caption("Si el recaudo acumulado supera el TCO, se recuperan los desembolsos modelados. Solo hay cortes anuales: no determina el mes exacto de recuperación.")
    with b:
        composicion = pd.DataFrame({"Categoría": ["COGS", "Mantenimiento", "Marketing", "Otros OPEX", "CapEx"], "Monto (COP)": [tabla["COGS (COP)"].sum(), tabla["OPEX (COP)"].sum() - 3 * (marketing + otros), 3 * marketing, 3 * otros, tabla["CapEx (COP)"].sum()]})
        composicion = composicion[composicion["Monto (COP)"] > 0]
        if not composicion.empty:
            mostrar_grafica(px.pie(composicion, names="Categoría", values="Monto (COP)", hole=.45, title="Distribución del TCO de tres años"), leyenda_anillo=True)
        else:
            st.info("No hay costos para representar en el anillo.")
        st.caption("Participación de cada rubro en todos los costos proyectados; incluye costos variables y CapEx una sola vez.")
    with st.expander("Desglose anual de las métricas del negocio"):
        st.dataframe(tabla, hide_index=True, width="stretch")
    st.subheader("Comparación de los tres proveedores")
    st.caption("Mismos supuestos comerciales para A, B y C. Cada proveedor utiliza sus costos editados en esta sesión, o sus valores iniciales si no los has editado.")
    comparacion = pd.DataFrame([{"Proveedor": nombre, **resumir(t)} for nombre, t in tablas.items()])
    st.dataframe(comparacion, hide_index=True, width="stretch")

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard_ui import mostrar_grafica
from simulacion_motor import proyectar


def mostrar_simulador(datos):
    supuestos = datos["supuestos"]
    valores = dict(zip(supuestos["Variable"], supuestos["Valor editable"]))
    trm = float(valores.get("TRM usada en el escenario", 4050.0))
    st.subheader("Proyección a tres años")
    st.caption("Ajusta los supuestos y selecciona un escenario para comparar inversión, beneficios y ROI.")
    st.sidebar.header("Proyección del Negocio")
    usuarios_año_1 = st.sidebar.number_input(
        "Usuarios Activos Iniciales (Año 1):",
        min_value=10,
        max_value=1000000,
        value=100,
        step=10,
        key="sim_usuarios_iniciales_v2",
        help="Punto de partida prudente para el ejercicio; no es una previsi?n validada de clientes."
    )
    crecimiento_anual_pct = st.sidebar.slider(
        "Tasa de Crecimiento Anual (%):",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        key="sim_crecimiento_v2"
    )
    ingreso_anual_por_usuario = st.sidebar.number_input(
        "Ingreso Anual por Usuario (COP):",
        min_value=0.0,
        max_value=5000.0 * trm,
        value=299000.0,
        step=10000.0,
        key="sim_ingreso_anual_v2",
        help="Supuesto editable: $299.000 al a?o, equivalente al precio anual Plus de referencia. No es ingreso mensual."
    )
    ahorro_eficiencia_pct = st.sidebar.slider(
        "% Ahorro Operativo / Eficiencia Habilitada:",
        min_value=5,
        max_value=50,
        value=15,
        help="Porcentaje de ahorro que genera este sistema frente a la operación manual anterior."
    )

    st.sidebar.markdown("---")
    proveedor_activo = st.sidebar.selectbox(
        "Seleccionar Proveedor / Escenario a Analizar:",
        ["Proveedor A: Arquitectura Serverless (AWS / Supabase)",
         "Proveedor B: Plataforma Gestionada (PaaS / Heroku / Render)",
         "Proveedor C: Servidores Dedicados (IaaS / VPS On-Premise)"]
    )

    # Proyección de usuarios a 3 años
    u1 = int(usuarios_año_1)
    u2 = int(u1 * (1 + (crecimiento_anual_pct / 100)))
    u3 = int(u2 * (1 + (crecimiento_anual_pct / 100)))
    usuarios_multianual = [u1, u2, u3]

    st.sidebar.info(f"**Usuarios Proyectados:**\n* Año 1: {u1:,}\n* Año 2: {u2:,}\n* Año 3: {u3:,}")

    # ==============================================================================
    # 3. TABLAS EDITABLES EN VIVO: CREACIÓN DINÁMICA DE ÍTEMS DE COSTO
    # ==============================================================================
    # Dataset base editable por defecto según proveedor seleccionado
    plantillas_defecto = {
        "Proveedor A: Arquitectura Serverless (AWS / Supabase)": [
            {"Concepto": "Setup Inicial y Migración Cloud", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (COP)": 1800.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Suscripción Base y Almacenamiento", "Categoría": "OpEx Fijo", "Costo Base Anual (COP)": 960.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Consumo de APIs y Tráfico Cloud", "Categoría": "OpEx Variable", "Costo Base Anual (COP)": 0.0, "Costo Variable por Usuario (COP)": 0.35},
            {"Concepto": "Soporte y Horas de Dev/DevOps", "Categoría": "Mantenimiento", "Costo Base Anual (COP)": 1500.0, "Costo Variable por Usuario (COP)": 0.00}
        ],
        "Proveedor B: Plataforma Gestionada (PaaS / Heroku / Render)": [
            {"Concepto": "Capacitación y Configuración Docker", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (COP)": 800.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Dynos / Contenedores Gestionados", "Categoría": "OpEx Fijo", "Costo Base Anual (COP)": 2400.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Base de Datos Administrada", "Categoría": "OpEx Variable", "Costo Base Anual (COP)": 0.0, "Costo Variable por Usuario (COP)": 0.55},
            {"Concepto": "Soporte Técnico Especializado", "Categoría": "Mantenimiento", "Costo Base Anual (COP)": 900.0, "Costo Variable por Usuario (COP)": 0.00}
        ],
        "Proveedor C: Servidores Dedicados (IaaS / VPS On-Premise)": [
            {"Concepto": "Compra de Servidor / Setup Red", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (COP)": 4500.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Alquiler de Rack y Conectividad", "Categoría": "OpEx Fijo", "Costo Base Anual (COP)": 1800.0, "Costo Variable por Usuario (COP)": 0.00},
            {"Concepto": "Ancho de Banda Consumido", "Categoría": "OpEx Variable", "Costo Base Anual (COP)": 0.0, "Costo Variable por Usuario (COP)": 0.12},
            {"Concepto": "Ingeniero Administrador de Sistemas", "Categoría": "Mantenimiento", "Costo Base Anual (COP)": 4000.0, "Costo Variable por Usuario (COP)": 0.00}
        ]
    }

    # Conversión de las plantillas ilustrativas de la guía a pesos colombianos.
    for plantilla in plantillas_defecto.values():
        for item in plantilla:
            item["Costo Base Anual (COP)"] *= trm
            item["Costo Variable por Usuario (COP)"] *= trm

    # Inicialización del Session State para que las modificaciones no se borren
    clave_estado = f"guia_ceroa_items_{proveedor_activo}"
    if clave_estado not in st.session_state:
        st.session_state[clave_estado] = pd.DataFrame(plantillas_defecto[proveedor_activo])

    # Mantener estable la base del editor durante sus reruns y restaurar al volver.
    if st.session_state.get("guia_ceroa_proveedor_anterior") != proveedor_activo:
        st.session_state["guia_ceroa_editor_base"] = st.session_state[clave_estado].copy()
        st.session_state["guia_ceroa_editor_version"] = st.session_state.get("guia_ceroa_editor_version", 0) + 1
        st.session_state["guia_ceroa_proveedor_anterior"] = proveedor_activo

    with st.expander("Ajustar costos del escenario", expanded=False):
        st.caption("Agrega o modifica costos; los indicadores y gr?ficas se recalculan al instante.")
        # Componente interactivo para agregar y editar filas libremente
        df_costos_editados = st.data_editor(
            st.session_state["guia_ceroa_editor_base"],
            key=f"guia_ceroa_editor_{st.session_state['guia_ceroa_editor_version']}",
            num_rows="dynamic",
            width="stretch",
            column_config={
                "Concepto": st.column_config.TextColumn("Descripción del Ítem", required=True),
                "Categoría": st.column_config.SelectboxColumn(
                    "Tipo Contable",
                    options=["CapEx (Única Vez)", "OpEx Fijo", "OpEx Variable", "Mantenimiento"],
                    required=True
                ),
                "Costo Base Anual (COP)": st.column_config.NumberColumn(
                    "Costo Fijo (COP)",
                    min_value=0.0,
                    format="$%.2f"
                ),
                "Costo Variable por Usuario (COP)": st.column_config.NumberColumn(
                    "Costo Unitario / Usuario (COP)",
                    min_value=0.0,
                    format="$%.4f"
                )
            }
        )

    # Guardar el resultado en un estado independiente del widget.
    st.session_state[clave_estado] = df_costos_editados.copy()

    # ==============================================================================
    # 4. MOTOR MATEMÁTICO: CÁLCULO MULTIANUAL DE TCO Y BENEFICIOS
    # ==============================================================================
    capex_total = df_costos_editados.loc[
        df_costos_editados["Categoría"] == "CapEx (Única Vez)", "Costo Base Anual (COP)"
    ].sum()
    proyeccion = proyectar(df_costos_editados, usuarios_año_1, crecimiento_anual_pct,
                          ingreso_anual_por_usuario, ahorro_eficiencia_pct)
    años = proyeccion["Periodo Fiscal"].tolist()
    usuarios_multianual = proyeccion["Usuarios Activos"].tolist()
    u1, u2, u3 = usuarios_multianual
    tco_anual = proyeccion["Costo Anual Total (COP)"].tolist()
    tco_acumulado = proyeccion["TCO Acumulado (COP)"].tolist()
    ingresos_acumulados = proyeccion["Beneficio Acumulado (COP)"].tolist()

    tco_final_3_años = tco_acumulado[-1]
    beneficio_bruto_3_años = ingresos_acumulados[-1]
    beneficio_neto_total = beneficio_bruto_3_años - tco_final_3_años
    roi_final_pct = (beneficio_neto_total / tco_final_3_años) * 100 if tco_final_3_años > 0 else 0.0

    # ==============================================================================
    # 5. TARJETAS EJECUTIVAS (C-SUITE SCORECARDS)
    # ==============================================================================
    st.markdown("---")
    st.subheader(proveedor_activo)
    st.caption("Misma lógica de la guía: beneficio = usuarios × ingreso anual por usuario × eficiencia. ROI = (beneficio acumulado − TCO) / TCO. Meta de comparación: 100% acumulado a tres años, como supuesto del ejercicio.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label="CapEx Inicial (Setup)",
        value=f"${capex_total:,.0f}"
    )
    col2.metric(
        label="TCO Consolidado (3 Años)",
        value=f"${tco_final_3_años:,.2f} COP"
    )
    col3.metric(
        label="Beneficio Operativo Neto",
        value=f"${beneficio_neto_total:,.0f}",
        delta="Superávit" if beneficio_neto_total > 0 else "Déficit"
    )
    col4.metric(
        label="ROI Estimado a 3 Años",
        value=f"{roi_final_pct:.1f}%",
        delta=f"{roi_final_pct - 100:.1f} p.p. vs Meta (100%)"
    )

    # ==============================================================================
    # 6. GRÁFICOS VISUALES: CURVA DE PAYBACK Y DESGLOSE DE COSTOS
    # ==============================================================================
    g1, g2 = st.columns([3, 2])

    with g1:
        # Gráfico de Payback: TCO Acumulado vs Beneficio Acumulado
        df_curva = pd.DataFrame({
            "Periodo": años,
            "Inversión Acumulada (TCO)": tco_acumulado,
            "Ahorros / Beneficios Acumulados": ingresos_acumulados
        })
        
        fig_payback = px.line(
            df_curva,
            x="Periodo",
            y=["Inversión Acumulada (TCO)", "Ahorros / Beneficios Acumulados"],
            markers=True,
            title="Curva de payback: inversión y beneficios",
            labels={"value": "Pesos colombianos (COP)", "variable": "Línea Financiera"},
            color_discrete_map={
                "Inversión Acumulada (TCO)": "#EF4444", 
                "Ahorros / Beneficios Acumulados": "#10B981"
            }
        )
        fig_payback.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
        mostrar_grafica(fig_payback)

    with g2:
        # Gráfico de torta/anillo: Desglose de costos por categoría
        resumen_categorias = df_costos_editados.groupby("Categoría")["Costo Base Anual (COP)"].sum().reset_index()
        fig_donut = px.pie(
            resumen_categorias,
            names="Categoría",
            values="Costo Base Anual (COP)",
            title="Composición de Costos por Categoría",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        mostrar_grafica(fig_donut, leyenda_anillo=True)

    # ==============================================================================
    # 7. TABLA DE DETALLE ANUALIZADO (DRILL-DOWN)
    # ==============================================================================
    st.markdown("---")

    df_resumen_anual = pd.DataFrame({
        "Periodo Fiscal": años,
        "Usuarios Activos": [f"{u:,}" for u in usuarios_multianual],
        "Costo Anual Total (COP)": [f"${costo:,.2f}" for costo in tco_anual],
        "TCO Acumulado (COP)": [f"${costo_acum:,.2f}" for costo_acum in tco_acumulado],
        "Beneficio Acumulado (COP)": [f"${ben:,.2f}" for ben in ingresos_acumulados],
        "Utilidad Neta Acumulada (COP)": [f"${ingresos_acumulados[i] - tco_acumulado[i]:,.2f}" for i in range(3)]
    })

    with st.expander("Ver desglose anual", expanded=False):
        st.dataframe(df_resumen_anual, width="stretch", hide_index=True)
    with st.expander("Supuestos de la simulación", expanded=False):
        st.write("Inicio: 100 usuarios; crecimiento anual: 20%; ingreso anual por usuario: $299.000 COP; eficiencia: 15%. Son supuestos editables del ejercicio. La fórmula de ROI y la meta del 100% acumulado a tres años son las de la guía.")
        st.write(f"Costos ilustrativos de la guía, convertidos a COP con TRM de referencia {trm:,.0f}. El anillo muestra los costos base por categoría; los variables por usuario se incluyen en el TCO.")

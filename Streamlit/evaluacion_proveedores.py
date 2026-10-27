"""Compara costos y ahorro operativo de proveedores durante tres años."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# CONFIGURACIÓN VISUAL DEL TABLERO
st.set_page_config(
    page_title="FinOps & TCO/ROI Strategic Simulator",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💼 Simulador Estratégico de TI: TCO, ROI y Evaluación de Proveedores")
st.caption("Ingeniería de Sistemas (8vo Semestre) | FinOps & C-Suite Decision Making Engine")
st.markdown("---")

# BARRA LATERAL: PARÁMETROS DEL NEGOCIO Y CRECIMIENTO
st.sidebar.header("📈 Proyección del Negocio")
usuarios_año_1 = st.sidebar.number_input(
    "Usuarios Activos Iniciales (Año 1):",
    min_value=10,
    max_value=1000000,
    value=1000,
    step=50
)
crecimiento_anual_pct = st.sidebar.slider(
    "Tasa de Crecimiento Anual (%):",
    min_value=10,
    max_value=300,
    value=50,
    step=10
)
ingreso_anual_por_usuario = st.sidebar.number_input(
    "Ingreso Anual por Usuario (USD):",
    min_value=10.0,
    max_value=5000.0,
    value=150.0,
    step=10.0
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

st.sidebar.info(f"👥 **Usuarios Proyectados:**\n* Año 1: {u1:,}\n* Año 2: {u2:,}\n* Año 3: {u3:,}")

# Costos editables por proveedor.
st.subheader("📝 Estructura de Costos del Proveedor (Personalización Fila a Fila)")
st.write(
    "Agrega, edita o elimina conceptos de costo específicos para este proveedor. "
    "El simulador recalcula el TCO y el ROI instantáneamente al modificar la tabla."
)

# Define los costos iniciales de cada proveedor.
plantillas_defecto = {
    "Proveedor A: Arquitectura Serverless (AWS / Supabase)": [
        {"Concepto": "Setup Inicial y Migración Cloud", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (USD)": 1800.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Suscripción Base y Almacenamiento", "Categoría": "OpEx Fijo", "Costo Base Anual (USD)": 960.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Consumo de APIs y Tráfico Cloud", "Categoría": "OpEx Variable", "Costo Base Anual (USD)": 0.0, "Costo Variable por Usuario (USD)": 0.35},
        {"Concepto": "Soporte y Horas de Dev/DevOps", "Categoría": "Mantenimiento", "Costo Base Anual (USD)": 1500.0, "Costo Variable por Usuario (USD)": 0.00}
    ],
    "Proveedor B: Plataforma Gestionada (PaaS / Heroku / Render)": [
        {"Concepto": "Capacitación y Configuración Docker", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (USD)": 800.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Dynos / Contenedores Gestionados", "Categoría": "OpEx Fijo", "Costo Base Anual (USD)": 2400.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Base de Datos Administrada", "Categoría": "OpEx Variable", "Costo Base Anual (USD)": 0.0, "Costo Variable por Usuario (USD)": 0.55},
        {"Concepto": "Soporte Técnico Especializado", "Categoría": "Mantenimiento", "Costo Base Anual (USD)": 900.0, "Costo Variable por Usuario (USD)": 0.00}
    ],
    "Proveedor C: Servidores Dedicados (IaaS / VPS On-Premise)": [
        {"Concepto": "Compra de Servidor / Setup Red", "Categoría": "CapEx (Única Vez)", "Costo Base Anual (USD)": 4500.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Alquiler de Rack y Conectividad", "Categoría": "OpEx Fijo", "Costo Base Anual (USD)": 1800.0, "Costo Variable por Usuario (USD)": 0.00},
        {"Concepto": "Ancho de Banda Consumido", "Categoría": "OpEx Variable", "Costo Base Anual (USD)": 0.0, "Costo Variable por Usuario (USD)": 0.12},
        {"Concepto": "Ingeniero Administrador de Sistemas", "Categoría": "Mantenimiento", "Costo Base Anual (USD)": 4000.0, "Costo Variable por Usuario (USD)": 0.00}
    ]
}

# Conserva los costos editados durante la sesión.
clave_estado = f"items_costo_{proveedor_activo}"
if clave_estado not in st.session_state:
    st.session_state[clave_estado] = pd.DataFrame(plantillas_defecto[proveedor_activo])

# Permite agregar y editar conceptos de costo.
df_costos_editados = st.data_editor(
    st.session_state[clave_estado],
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Concepto": st.column_config.TextColumn("Descripción del Ítem", required=True),
        "Categoría": st.column_config.SelectboxColumn(
            "Tipo Contable",
            options=["CapEx (Única Vez)", "OpEx Fijo", "OpEx Variable", "Mantenimiento"],
            required=True
        ),
        "Costo Base Anual (USD)": st.column_config.NumberColumn(
            "Costo Fijo (USD)",
            min_value=0.0,
            format="$%.2f"
        ),
        "Costo Variable por Usuario (USD)": st.column_config.NumberColumn(
            "Costo Unitario / Usuario (USD)",
            min_value=0.0,
            format="$%.4f"
        )
    }
)

# Cálculo de costos y ahorro acumulados.
# Separación de CapEx (Año 1) de los costos operativos recurrentes
capex_total = df_costos_editados[df_costos_editados["Categoría"] == "CapEx (Única Vez)"]["Costo Base Anual (USD)"].sum()
items_recurrentes = df_costos_editados[df_costos_editados["Categoría"] != "CapEx (Única Vez)"]

años = ["Año 1", "Año 2", "Año 3"]
tco_anual = []
tco_acumulado = []
ingresos_acumulados = []
beneficios_netos_acumulados = []

costo_acum = capex_total
beneficio_acum = 0.0

for i, cant_usuarios in enumerate(usuarios_multianual):
    # Costo del año = Fijos recurrentes + (Usuarios * Costo variable)
    fijo_año = items_recurrentes["Costo Base Anual (USD)"].sum()
    variable_año = (items_recurrentes["Costo Variable por Usuario (USD)"] * cant_usuarios).sum()
    costo_año_total = fijo_año + variable_año
    
    # En el Año 1 sumamos el CapEx
    if i == 0:
        costo_año_total += capex_total
    
    costo_acum += (fijo_año + variable_año)
    tco_anual.append(round(costo_año_total, 2))
    tco_acumulado.append(round(costo_acum, 2))
    
    # Calcula el ahorro anual como usuarios por ingreso anual por eficiencia.
    ingreso_año = cant_usuarios * ingreso_anual_por_usuario
    ahorro_año = ingreso_año * (ahorro_eficiencia_pct / 100.0)
    beneficio_acum += ahorro_año
    
    ingresos_acumulados.append(round(beneficio_acum, 2))

tco_final_3_años = tco_acumulado[-1]
beneficio_bruto_3_años = ingresos_acumulados[-1]
beneficio_neto_total = beneficio_bruto_3_años - tco_final_3_años
roi_final_pct = (beneficio_neto_total / tco_final_3_años) * 100 if tco_final_3_años > 0 else 0.0

# Indicadores de inversión, costos y rentabilidad.
st.markdown("---")
st.subheader("📊 Indicadores Financieros Consolidados (Horizonte 3 Años)")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="CapEx Inicial (Setup)",
    value=f"${capex_total:,.2f} USD"
)
col2.metric(
    label="TCO Consolidado (3 Años)",
    value=f"${tco_final_3_años:,.2f} USD"
)
col3.metric(
    label="Beneficio Operativo Neto",
    value=f"${beneficio_neto_total:,.2f} USD",
    delta="Superávit" if beneficio_neto_total > 0 else "Déficit"
)
col4.metric(
    label="ROI Estimado a 3 Años",
    value=f"{roi_final_pct:.1f}%",
    delta=f"{roi_final_pct - 100:.1f}% vs Meta (100%)"
)

# Recuperación de la inversión y distribución de costos.
g1, g2 = st.columns([3, 2])

with g1:
    # Compara el costo total y el ahorro acumulados.
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
        title="📈 Análisis de Retorno: Curva de Payback (TCO vs. Beneficios)",
        labels={"value": "Dólares (USD)", "variable": "Línea Financiera"},
        color_discrete_map={
            "Inversión Acumulada (TCO)": "#EF4444", 
            "Ahorros / Beneficios Acumulados": "#10B981"
        }
    )
    fig_payback.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_payback, use_container_width=True)

with g2:
    # Gráfico de torta/anillo: Desglose de costos por categoría
    resumen_categorias = df_costos_editados.groupby("Categoría")["Costo Base Anual (USD)"].sum().reset_index()
    fig_donut = px.pie(
        resumen_categorias,
        names="Categoría",
        values="Costo Base Anual (USD)",
        title="🍩 Composición de Costos por Categoría",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# Desglose de resultados por año.
st.markdown("---")
st.subheader("🔍 Desglose Anual de Inversión y Retorno")

df_resumen_anual = pd.DataFrame({
    "Periodo Fiscal": años,
    "Usuarios Activos": [f"{u:,}" for u in usuarios_multianual],
    "Costo Anual Total (USD)": [f"${costo:,.2f}" for costo in tco_anual],
    "TCO Acumulado (USD)": [f"${costo_acum:,.2f}" for costo_acum in tco_acumulado],
    "Beneficio Acumulado (USD)": [f"${ben:,.2f}" for ben in ingresos_acumulados],
    "Utilidad Neta Periodo (USD)": [f"${ingresos_acumulados[i] - tco_acumulado[i]:,.2f}" for i in range(3)]
})

st.dataframe(df_resumen_anual, use_container_width=True, hide_index=True)
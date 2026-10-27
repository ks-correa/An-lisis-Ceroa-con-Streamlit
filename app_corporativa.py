"""Tablero corporativo con filtros, indicadores y gráficos de ingresos."""

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard_ui import aplicar_estilo, mostrar_grafica

# Configura la página de Streamlit.
st.set_page_config(
    page_title="Executive BI Platform | Enterprise Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

aplicar_estilo()
st.title("Panel Ejecutivo de Analítica Corporativa y Decisión")
st.caption("Ingeniería de Sistemas (8vo Semestre) | Arquitectura de Inteligencia de Negocios")
st.markdown("---")

@st.cache_data
def cargar_datos():
    """Carga el CSV corporativo, limpia sus columnas y calcula los márgenes."""
    archivo = "dataset_corporativo_tech.csv"
    
    # Detecta el separador del archivo CSV.
    try:
        # Detecta el delimitador con el motor de Python.
        df = pd.read_csv(archivo, sep=None, engine="python", encoding="utf-8-sig")
    except Exception:
        # Reintenta la lectura con codificación Latin-1 y punto y coma.
        df = pd.read_csv(archivo, sep=";", encoding="latin1")

    # Elimina espacios al inicio y al final de los encabezados.
    df.columns = df.columns.astype(str).str.strip()

    # Comprueba las columnas necesarias para el análisis.
    columnas_requeridas = ["Fecha", "Ingreso_USD", "COGS_USD", "Pais", "Sector_Industria"]
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        raise KeyError(f"Columnas faltantes: {columnas_faltantes}. Columnas leídas: {list(df.columns)}")

    # Convierte importes de texto y comas decimales a números.
    for col in ["Ingreso_USD", "COGS_USD"]:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
            )

    # Convierte las fechas; los valores inválidos quedan vacíos.
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Calcula el margen bruto y su porcentaje por transacción.
    df["Margen_Bruto_USD"] = df["Ingreso_USD"] - df["COGS_USD"]
    df["Margen_Pct"] = (df["Margen_Bruto_USD"] / df["Ingreso_USD"]) * 100
    
    return df

try:
    df_raw = cargar_datos()
except FileNotFoundError:
    st.error("Error Crítico: No se encontró 'dataset_corporativo_tech.csv'. Asegúrate de que el archivo esté en la misma carpeta que este script.")
    st.stop()
except KeyError as e:
    st.error(f"Error en estructura de datos: {e}")
    st.info("Consejo: Abre 'dataset_corporativo_tech.csv' en el Bloc de Notas para verificar que la primera fila contenga: ID_Transaccion,Fecha,Cliente,Pais,Sector_Industria,Producto_Plan,Canal_Adquisicion,Ingreso_USD,COGS_USD,Estado_Pago")
    st.stop()

st.sidebar.header("Filtros de Control Multidimensional")

# Filtro 1: Territorio Geográfico
paises_disponibles = ["Todos"] + sorted(df_raw["Pais"].dropna().unique().tolist())
filtro_pais = st.sidebar.selectbox("Filtrar por Territorio:", paises_disponibles)

# Filtro 2: Sector de Industria
sectores_disponibles = ["Todos"] + sorted(df_raw["Sector_Industria"].dropna().unique().tolist())
filtro_sector = st.sidebar.selectbox("Filtrar por Sector:", sectores_disponibles)

df_filtrado = df_raw.copy()

if filtro_pais != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Pais"] == filtro_pais]

if filtro_sector != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Sector_Industria"] == filtro_sector]

st.sidebar.info(f"Mostrando **{len(df_filtrado)}** de **{len(df_raw)}** transacciones auditadas.")

st.subheader("Indicadores Clave de Gestión (C-Suite Scorecards)")

ingresos_totales = df_filtrado["Ingreso_USD"].sum()
cogs_total = df_filtrado["COGS_USD"].sum()
utilidad_bruta = ingresos_totales - cogs_total
margen_promedio = (utilidad_bruta / ingresos_totales * 100) if ingresos_totales > 0 else 0.0
total_transacciones = len(df_filtrado)
ticket_promedio = (ingresos_totales / total_transacciones) if total_transacciones > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Ingresos Totales", f"${ingresos_totales:,.2f} USD")
c2.metric("COGS Directo", f"${cogs_total:,.2f} USD")
c3.metric("Utilidad Bruta", f"${utilidad_bruta:,.2f} USD")
c4.metric("Margen Bruto (%)", f"{margen_promedio:.1f}%", delta=f"{margen_promedio - 70:.1f}% vs Meta (70%)")
c5.metric("Ticket Promedio", f"${ticket_promedio:,.2f} USD")

st.markdown("---")

st.subheader("Análisis Visual de Rendimiento")
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Agrupación cronológica por mes
    df_tiempo = (
        df_filtrado
        .dropna(subset=["Fecha"])
        .set_index("Fecha")
        .resample("ME")["Ingreso_USD"]
        .sum()
        .reset_index()
    )
    df_tiempo["Mes_Etiqueta"] = df_tiempo["Fecha"].dt.strftime("%b %Y")
    
    fig_temporal = px.line(
        df_tiempo,
        x="Mes_Etiqueta",
        y="Ingreso_USD",
        title="Evolución Mensual de Facturación (MRR Run-Rate)",
        markers=True,
        labels={"Mes_Etiqueta": "Mes Fiscal", "Ingreso_USD": "Ingresos (USD)"}
    )
    fig_temporal.update_traces(line_color="#0284C7", line_width=3)
    mostrar_grafica(fig_temporal, moneda="USD")

with col_graf2:
    # Agrupación por Sector de Industria
    df_sector = df_filtrado.groupby("Sector_Industria")["Ingreso_USD"].sum().reset_index()
    fig_sector = px.bar(
        df_sector,
        x="Sector_Industria",
        y="Ingreso_USD",
        color="Sector_Industria",
        title="Facturación Consolidada por Sector Económico",
        labels={"Sector_Industria": "Sector", "Ingreso_USD": "Ventas (USD)"}
    )
    mostrar_grafica(fig_sector, moneda="USD")

st.markdown("---")

st.subheader("Explorador Transaccional y Auditoría Fila a Fila")

columnas_mostrar = [
    "ID_Transaccion", "Fecha", "Cliente", "Pais", 
    "Sector_Industria", "Producto_Plan", "Ingreso_USD", "COGS_USD", "Margen_Pct"
]
columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]

st.dataframe(
    df_filtrado[columnas_existentes],
    width="stretch",
    hide_index=True
)



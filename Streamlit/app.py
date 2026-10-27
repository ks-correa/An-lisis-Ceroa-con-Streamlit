"""Ejemplo de controles de Streamlit para explorar datos corporativos."""

import streamlit as st
import pandas as pd

df = pd.read_csv("dataset_corporativo_tech.csv")

def main():
    st.title("Dashboard de Análisis de Datos")
    st.set_page_config(
        page_title="Dashboard de Análisis de Datos",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    

    # Selecciona la sección del análisis.
    opcion = st.selectbox(
        "Selecciona una opción:",
        ["Visualizar Datos", "Análisis Estadístico", "Gráficos Interactivos"]
    )
    
    # Selecciona las columnas que se mostrarán.
    opciones = st.multiselect(
        "Selecciona las columnas a mostrar:",
        df.columns.tolist(),
        default=None
    )
    
    # Selecciona el intervalo de edades.
    edad = st.slider(
        "Selecciona un rango de edad:",
        min_value=0,
        max_value=100,
        value=25,
        step=1,
    )
    
    # Selecciona el nivel de ingresos.
    st.select_slider(
        "Selecciona un rango de ingresos:",
        options=[0, 10000, 20000, 30000, 40000, 50000],
        value=(10000, 30000)
    )
    
    nombre = st.text_input("Ingresa tu nombre:")
    detalle = st.text_area("Ingresa detalles adicionales:", height=100)
    numero = st.number_input("Ingresa un número:", min_value=0, max_value=100, value=10, step=1)
    fecha = st.date_input("Selecciona una fecha:")
    hora = st.time_input("Selecciona una hora:")
    color = st.color_picker("Selecciona un color:")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
if __name__ == "__main__":
    main()
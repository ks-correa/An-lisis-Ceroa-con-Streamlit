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
    
    #st.header("Bienvenido al Dashboard de Análisis de Datos")
    #st.subheader("Este dashboard permite explorar y analizar los datos de manera interactiva.")
    #st.text("Utiliza los filtros en la barra lateral para personalizar la visualización de los datos.")
    #st.success("¡Explora los datos y descubre insights valiosos!")
    #st.warning("⚠️ Asegúrate de que los datos estén correctamente formateados antes de realizar análisis.")
    #st.info("💡 Consejo: Puedes descargar los datos filtrados para un análisis más detallado.")
    #st.error("❌ Error: Si encuentras algún problema, revisa los datos y la estructura del archivo CSV.") """

    # Selectbox
    opcion = st.selectbox(
        "Selecciona una opción:",
        ["Visualizar Datos", "Análisis Estadístico", "Gráficos Interactivos"]
    )
    
    # Multiselect
    opciones = st.multiselect(
        "Selecciona las columnas a mostrar:",
        df.columns.tolist(),
        default=None
    )
    
    # Slider
    edad = st.slider(
        "Selecciona un rango de edad:",
        min_value=0,
        max_value=100,
        value=25,
        step=1,
    )
    
    # Select slider
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
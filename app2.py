import streamlit as st

st.set_page_config(
    page_title="Dashboard de Análisis de Datos",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    st.title("Dashboard de Análisis de Datos")
    st.caption("Bienvenido al Dashboard de Análisis de Datos. Explora y analiza los datos de manera interactiva.")
    st.sidebar.header("Navegación")
    
if __name__ == "__main__":
    main()